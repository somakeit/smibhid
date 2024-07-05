from display import Display
from networking import WirelessNetwork
from asyncio import create_task

class ModuleConfig:
    """
    Create a new instance of the module configurations for use in child modules of HID.
    Dependency injection to ensure we are managing module configurations in a single place without the use of singletons.
    """
    def __init__(self, display: Display, wifi: WirelessNetwork) -> None:
        self.display = display
        self.wifi = wifi

    def get_display(self) -> Display:
        return self.display
    
    def get_wifi(self) -> WirelessNetwork:
        return self.wifi
    