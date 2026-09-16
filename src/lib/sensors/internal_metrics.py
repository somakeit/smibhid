from lib.relay_history import RTCUnreliableError
from lib.sensors.sensor_module import SensorModule
from lib.space_state import SpaceState
from lib.ulogging import uLogger

class InternalMetrics(SensorModule):
    """
    Reports internal SMIBHID metrics as sensor readings, rather than
    readings from an external, physically attached, I2C sensor.
    """

    def __init__(self, space_state: SpaceState) -> None:
        super().__init__([{"name": "relay_on_time", "unit": "s"}])
        self.log = uLogger("InternalMetrics")
        self.space_state = space_state

    def _get_relay_on_time(self) -> float | None:
        """
        Return cumulative relay active seconds from relay history, or None
        if relay history is not available or not enabled.
        """
        relay_history = getattr(self.space_state, "relay_history", None)
        if relay_history is None:
            self.log.info("Relay history not available - no relay on time to report")
            return None

        try:
            return relay_history.get_total_active_seconds(bool(self.space_state._last_relay_state))
        except RTCUnreliableError:
            self.log.info("System clock not yet reliable - no relay on time to report")
            return None

    def get_reading(self) -> dict[str, float | None]:
        """
        Get internal metrics reading in SMIBHID format.
        """
        return {
            "relay_on_time": self._get_relay_on_time()
        }
