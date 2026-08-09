from lib.ulogging import uLogger
from lib.utils import DateTimeUtils
from lib.error_handling import ErrorHandler
from lib.slack_api import Wrapper
from os import listdir, mkdir
from time import time
from json import dumps, loads
import config

# 2024-01-01T00:00:00Z. The RP2040's RTC has no battery backup and resets
# to a fixed default on every power-on until NTP sync completes (expected
# early, at network access on boot). A clock reading before this floor
# means NTP hasn't corrected it yet, so any elapsed-time diff against it
# would be meaningless - treated the same as the relay being off for
# accounting purposes.
RTC_SANITY_FLOOR_EPOCH_S = 1704067200

class RTCUnreliableError(Exception):
    """Raised when the system clock reads before RTC_SANITY_FLOOR_EPOCH_S."""
    pass

class RelayHistory:
    """
    Tracks cumulative relay active seconds, backed up to a JSON file on
    the local filesystem. Pushes relay state changes and resets to SMIB.
    """

    def __init__(self, slack_api: Wrapper, data_root: str = "/") -> None:
        self.log = uLogger("RelayHistory")
        self.datetime_utils = DateTimeUtils()
        self.slack_api = slack_api
        self.enabled = config.SPACE_OPEN_RELAY_HISTORY_ENABLED
        self.STATE_FILE = data_root + "data/relay/state.json"
        self._total_active_seconds: float | None = None
        self._last_checkpoint_timestamp: float | None = None
        self.configure_error_handling()
        if self.enabled and not self._init_file_structure(data_root):
            self.log.error("Failed to create relay state storage folder - disabling relay history tracking")
            self.error_handler.enable_error("INIT")
            self.enabled = False

    def configure_error_handling(self) -> None:
        """
        Register errors with the error handler for the relay history module.
        """
        self.error_handler = ErrorHandler("RelayHistory")
        self.errors = {
            "PUSH": "Failed to push relay state update to SMIB.",
            "WRITE": "Failed to write relay state file.",
            "INIT": "Failed to create relay state storage folder.",
            "CLOCK": "System clock not yet reliable (pre-2024) - relay on time not being recorded.",
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)

    def _init_file_structure(self, data_root: str) -> bool:
        data_ok = self._check_and_create_folder(data_root, "data")
        relay_ok = self._check_and_create_folder(data_root + "data/", "relay")
        return data_ok and relay_ok

    def _check_and_create_folder(self, path: str, folder: str) -> bool:
        try:
            if folder not in listdir(path[0:-1] if path.endswith("/") else path):
                mkdir(path + folder)
            return True
        except Exception as e:
            self.log.error(f"Failed to check for {folder} in {path}: {e}")
            return False

    def _restore_total_from_file(self) -> float:
        """
        Read total_active_seconds back from the backup file. Returns 0 if
        the file is missing or its value isn't a valid non-negative number.
        """
        try:
            with open(self.STATE_FILE, "r") as f:
                state = loads(f.read())
        except Exception as e:
            self.log.info(f"No existing relay state file to read: {e}")
            return 0

        total_active_seconds = state.get("total_active_seconds", 0)
        if not isinstance(total_active_seconds, (int, float)) or total_active_seconds < 0:
            self.log.error(f"Relay state file has an implausible total_active_seconds ({total_active_seconds!r}) - treating as corrupt, starting from 0")
            return 0

        return total_active_seconds

    def _write_state(self, timestamp: float, total_active_seconds: float) -> bool:
        """
        Write timestamp and total_active_seconds to the backup file.
        """
        state = {
            "timestamp": timestamp,
            "human_timestamp": self.datetime_utils.timestamp_to_iso8601(timestamp),
            "total_active_seconds": total_active_seconds
        }
        try:
            with open(self.STATE_FILE, "w") as f:
                f.write(dumps(state))
            if self.error_handler.is_error_enabled("WRITE"):
                self.error_handler.disable_error("WRITE")
            return True
        except Exception as e:
            self.log.error(f"Failed to write relay state file: {e}")
            if not self.error_handler.is_error_enabled("WRITE"):
                self.error_handler.enable_error("WRITE")
            return False

    def _ensure_total_loaded(self) -> float:
        """
        If None in memory, restore total_active_seconds from the backup file
        and return 0 if no valid file value.
        """
        if not isinstance(self._total_active_seconds, (int, float)) or self._total_active_seconds < 0:
            self._total_active_seconds = self._restore_total_from_file()
        return self._total_active_seconds

    def get_total_active_seconds(self, previous_active: bool) -> float | None:
        """
        Return total active seconds, crediting elapsed time since the
        last checkpoint if previous_active is True.
        Returns None if relay history tracking is not enabled.
        Raises RTCUnreliableError if the clock isn't yet reliable.
        """
        if not self.enabled:
            return None

        now = time()
        if now < RTC_SANITY_FLOOR_EPOCH_S:
            self.log.error(f"System clock not yet reliable ({now=}, pre-2024) - cannot calculate relay on time")
            if not self.error_handler.is_error_enabled("CLOCK"):
                self.error_handler.enable_error("CLOCK")
            raise RTCUnreliableError(f"System clock reads {now}, before RTC sanity floor {RTC_SANITY_FLOOR_EPOCH_S}")
        if self.error_handler.is_error_enabled("CLOCK"):
            self.error_handler.disable_error("CLOCK")

        total_active_seconds = self._ensure_total_loaded()

        if previous_active and self._last_checkpoint_timestamp is not None:
            elapsed = max(0, now - self._last_checkpoint_timestamp)
            total_active_seconds += elapsed

        return total_active_seconds

    def _calculate_total(self, previous_active: bool) -> tuple[float, float] | None:
        """
        Return (timestamp, total_active_seconds), or None if the clock
        isn't yet reliable. Only called while self.enabled, so
        total_active_seconds is always a float here.
        """
        try:
            total_active_seconds = self.get_total_active_seconds(previous_active)
        except RTCUnreliableError:
            return None

        assert total_active_seconds is not None
        return time(), total_active_seconds

    def _update_on_time(self, previous_active: bool, active: bool) -> bool:
        """
        Calculate the up-to-date total, persist it as the new checkpoint,
        back it up to file, and push it to SMIB.
        Returns True on success, False if the clock isn't yet reliable.
        """
        if not self.enabled:
            return True

        result = self._calculate_total(previous_active)
        if result is None:
            return False
        timestamp, total_active_seconds = result

        self._total_active_seconds = total_active_seconds
        self._last_checkpoint_timestamp = timestamp

        self._write_state(timestamp, total_active_seconds)

        self.slack_api.fire_and_forget_async_task(
            self.slack_api.async_relay_state_update(active, total_active_seconds),
            self.error_handler,
            "PUSH",
            "Relay state update pushed to SMIB"
        )
        return True

    def record_transition(self, previous_active: bool, active: bool) -> None:
        """
        Record a relay state transition from previous_active to active.
        """
        self._update_on_time(previous_active, active)

    def heartbeat(self, active: bool) -> bool:
        """
        Refresh the total and backup file without a state transition.
        Returns True on success, False if the clock isn't yet reliable.
        """
        return self._update_on_time(active, active)

    def reset(self, active: bool) -> float | None:
        """
        Reset the cumulative total to zero and notify SMIB. Returns the
        total that was reset, in seconds, or None if relay history
        tracking is not enabled.
        Raises RTCUnreliableError if the clock isn't yet reliable.
        Raises RuntimeError if the reset could not be persisted.
        """
        previous_total = self.get_total_active_seconds(active)
        if previous_total is None:
            return None

        if not self._write_state(time(), 0):
            raise RuntimeError("Failed to persist relay history reset - reset not applied")

        self._total_active_seconds = 0

        self.slack_api.fire_and_forget_async_task(
            self.slack_api.async_relay_reset(previous_total),
            self.error_handler,
            "PUSH",
            "Relay reset notification pushed to SMIB"
        )

        return previous_total
