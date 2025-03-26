from lib.ulogging import uLogger

class SensorModule:
    """
    Base class for sensor modules.
    """
    def __init__(self, sensors: list) -> None:
        self.log = uLogger("SensorModule")
        self.sensors = sensors
    
    def get_sensors(self) -> list:
        """
        Return list of sensors for a specific module.
        """
        return self.sensors
    
    def get_reading(self) -> dict[str, float]:
        """
        Return a dictionary of sensor name and value pairs
        """
        raise NotImplementedError("Subclasses must implement this method")