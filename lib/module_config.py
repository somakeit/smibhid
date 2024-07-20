from lib.display import Display
from lib.networking import WirelessNetwork
from lib.ulogging import uLogger
from lib.rfid.reader import RFIDReader

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

    def register_display(self, display: Display) -> None:
        self.display = display

    def register_wifi(self, wifi: WirelessNetwork) -> None:
        self.wifi = wifi
    
    def register_rfid(self, reader: RFIDReader) -> None:
        self.reader = reader

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
    
    def get_rfid(self) -> RFIDReader:
        if not self.reader:
            self.log.warn("RFID module not registered")
            raise ModuleNotRegisteredError("RFID")
        return self.reader
    