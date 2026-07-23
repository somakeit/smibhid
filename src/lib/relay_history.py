"""
Tracks relay on/off time to a local file so total on time survives a reboot,
and pushes relay state changes and resets to SMIB.
"""

from lib.ulogging import uLogger
from lib.utils import DateTimeUtils
from lib.error_handling import ErrorHandler
from lib.slack_api import Wrapper
from os import listdir, mkdir
from time import time
from json import dumps, loads
from asyncio import create_task
import config

class RelayHistory:
    """
    Persists relay active state and cumulative active seconds to a single
    JSON file on the local filesystem, rewritten in place on every
    transition and on a periodic heartbeat. This allows total on time to
    be calculated without keeping an unbounded log, and allows a power
    loss to be detected and accounted for on the next boot.
    Also owns pushing relay state changes and resets to SMIB.
    """

    def __init__(self, slack_api: Wrapper, data_root: str = "/") -> None:
        """
        slack_api should be the caller's existing Wrapper instance so relay
        pushes share it rather than opening a second, redundant one.
        data_root defaults to the filesystem root, giving the on-device
        state file path /data/relay/state.json. Only override in tests, to
        point state persistence at a temporary directory instead of the
        real filesystem root.
        """
        self.log = uLogger("RelayHistory")
        self.datetime_utils = DateTimeUtils()
        self.slack_api = slack_api
        self.enabled = config.RELAY_HISTORY_ENABLED
        self.STATE_FILE = data_root + "data/relay/state.json"
        self.configure_error_handling()
        if self.enabled:
            self._init_file_structure(data_root)

    def configure_error_handling(self) -> None:
        """
        Register errors with the error handler for the relay history module.
        """
        self.error_handler = ErrorHandler("RelayHistory")
        self.errors = {
            "PUSH": "Failed to push relay state update to SMIB.",
            "HEARTBEAT": "Relay history heartbeat failed.",
            "WRITE": "Failed to write relay state file.",
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)

    def _init_file_structure(self, data_root: str) -> None:
        self._check_and_create_folder(data_root, "data")
        self._check_and_create_folder(data_root + "data/", "relay")

    def _check_and_create_folder(self, path: str, folder: str) -> bool:
        try:
            if folder not in listdir(path[0:-1] if path.endswith("/") else path):
                mkdir(path + folder)
            return True
        except Exception as e:
            self.log.error(f"Failed to check for {folder} in {path}: {e}")
            return False

    def _read_state(self) -> dict | None:
        try:
            with open(self.STATE_FILE, "r") as f:
                return loads(f.read())
        except Exception as e:
            self.log.info(f"No existing relay state file to read: {e}")
            return None

    def _write_state(self, active: bool, timestamp: float, total_active_seconds: float) -> bool:
        state = {
            "active": active,
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

    def check_and_recover_on_boot(self) -> None:
        """
        On startup, check the persisted state. If the relay was active when
        the device last wrote state, only credit on time up to that last
        recorded timestamp - any time between then and now is unknown, as
        the device may have been unplugged with no chance to record a
        clean shutdown, so it is treated as off.
        """
        if not self.enabled:
            return

        state = self._read_state()
        now = time()

        if state is None:
            self._write_state(False, now, 0)
            return

        total_active_seconds = state.get("total_active_seconds", 0)

        if state.get("active"):
            self.log.info("Relay was active at last recorded state - crediting time up to last known timestamp only, treating device as off since then")

        self._write_state(False, now, total_active_seconds)

    def record_transition(self, active: bool) -> None:
        """
        Record a relay state transition, folding elapsed active time since
        the last recorded state into the running total before overwriting
        the current state. Always pushes the new state to SMIB, even if the
        local write failed - the relay changing state is a real-world event
        driven by space/light state outside smibhid's control, so SMIB must
        be told regardless of whether smibhid managed to persist it locally.
        Any resulting discrepancy between smibhid's and SMIB's totals is
        diagnosable as smibhid-side, and SMIB's own total remains the
        trusted figure surfaced to users.
        """
        if not self.enabled:
            return

        now = time()
        state = self._read_state()
        total_active_seconds = self._accumulate(state, now)

        self._write_state(active, now, total_active_seconds)

        try:
            create_task(self.slack_api.async_relay_state_update(active, total_active_seconds))
            self.log.info("Relay state update pushed to SMIB")
            if self.error_handler.is_error_enabled("PUSH"):
                self.error_handler.disable_error("PUSH")
        except Exception as e:
            self.log.error(f"Failed to push relay state update to SMIB: {e}")
            if not self.error_handler.is_error_enabled("PUSH"):
                self.error_handler.enable_error("PUSH")

    def heartbeat(self) -> None:
        """
        Periodic local-only refresh of the state file so a future boot can
        tell how recently the device was last known to be running. Does
        not push to SMIB.
        """
        if not self.enabled:
            return

        try:
            now = time()
            state = self._read_state()
            if state is None:
                self._write_state(False, now, 0)
            else:
                total_active_seconds = self._accumulate(state, now)
                self._write_state(state.get("active", False), now, total_active_seconds)

            if self.error_handler.is_error_enabled("HEARTBEAT"):
                self.error_handler.disable_error("HEARTBEAT")
        except Exception as e:
            self.log.error(f"Relay history heartbeat failed: {e}")
            if not self.error_handler.is_error_enabled("HEARTBEAT"):
                self.error_handler.enable_error("HEARTBEAT")

    def _accumulate(self, state: dict | None, now: float) -> float:
        """
        Return the running total_active_seconds, adding elapsed time since
        the last recorded state if that state was active.
        """
        if state is None:
            return 0

        total_active_seconds = state.get("total_active_seconds", 0)
        if state.get("active"):
            last_timestamp = state.get("timestamp", now)
            total_active_seconds += max(0, now - last_timestamp)

        return total_active_seconds

    def get_total_active_seconds(self) -> float | None:
        """
        Return the current total active seconds, including time elapsed
        since the last recorded state if the relay is currently active.
        Returns None if relay history tracking is not enabled.
        """
        if not self.enabled:
            return None

        state = self._read_state()
        if state is None:
            return 0

        return self._accumulate(state, time())

    def get_current_state(self) -> dict | None:
        if not self.enabled:
            return None
        return self._read_state()

    def reset(self) -> float | None:
        """
        Reset the cumulative total to zero, preserving the current active
        state and timestamp. Notifies SMIB of the reset. Returns the total
        that was reset, in seconds, or None if relay history tracking is
        not enabled.
        Raises RuntimeError if the reset state could not be persisted, so
        the reset is not reported as successful (and SMIB is not notified)
        when smibhid's own total would in fact revert on next read.
        """
        if not self.enabled:
            return None

        state = self._read_state()
        now = time()
        previous_total = self._accumulate(state, now)
        active = state.get("active", False) if state is not None else False

        if not self._write_state(active, now, 0):
            raise RuntimeError("Failed to persist relay history reset - reset not applied")

        try:
            create_task(self.slack_api.async_relay_reset(previous_total))
            self.log.info("Relay reset notification pushed to SMIB")
            if self.error_handler.is_error_enabled("PUSH"):
                self.error_handler.disable_error("PUSH")
        except Exception as e:
            self.log.error(f"Failed to push relay reset notification to SMIB: {e}")
            if not self.error_handler.is_error_enabled("PUSH"):
                self.error_handler.enable_error("PUSH")

        return previous_total
