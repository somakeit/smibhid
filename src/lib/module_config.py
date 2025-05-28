from lib.displays.display import Display
from lib.networking import WirelessNetwork
from lib.ulogging import uLogger
from lib.rfid.reader import RFIDReader
from config import RFID_ENABLED
from lib.ui_log import UILog

class ModuleNotRegisteredError(Exception):
    """Exception raised when a required module is not registered."""
    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"{module_name} module not registered")

class ModuleConfig:
    """
    Create a new instance of the module configurations for use in child modules of HID.
    Dependency injection to ensure we are managing module configurations in a single place without the use of singletons.
    """
    def __init__(self) -> None:
        self.log = uLogger("ModuleConfig")
        self.display = None
        self.wifi = None
        self.reader = None
        self.ui_log = None
        self.sensors = None

    def register_display(self, display: Display) -> None:
        self.display = display

    def register_wifi(self, wifi: WirelessNetwork) -> None:
        self.wifi = wifi
    
    def register_rfid(self, reader: RFIDReader) -> None:
        self.reader = reader
    
    def register_ui_log(self, ui_log: UILog) -> None:
        self.ui_log = ui_log
    
    def register_sensors(self, sensors) -> None:
        self.sensors = sensors

    def get_display(self) -> Display:
        if not self.display:
            self.log.warn("Display module not registered")
            raise ModuleNotRegisteredError("Display")
        return self.display
    
    def get_wifi(self) -> WirelessNetwork:
        if not self.wifi:
            self.log.warn("WiFi module not registered")
            raise ModuleNotRegisteredError("WiFi")
        return self.wifi
    
    def get_rfid(self) -> RFIDReader | None:
        if not self.reader and RFID_ENABLED:
            self.log.warn("RFID module not registered")
            raise ModuleNotRegisteredError("RFID")
        return self.reader
    
    def get_ui_log(self) -> UILog:
        if not self.ui_log:
            self.log.warn("UI Log module not registered")
            raise ModuleNotRegisteredError("UI Log")
        return self.ui_log
    
    def get_sensors(self):
        if not self.sensors:
            self.log.warn("Sensors module not registered")
            raise ModuleNotRegisteredError("Sensors")
        return self.sensors
