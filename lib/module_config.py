from display import Display
from networking import WirelessNetwork
from asyncio import create_task
from ulogging import uLogger
from rfid.reader import RFIDReader

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
        return self.display
    
    def get_wifi(self) -> WirelessNetwork:
        return self.wifi
    
    def get_rfid(self) -> RFIDReader:
        return self.reader
    