from ulogging import uLogger
from asyncio import get_event_loop, Event
from space_state import SpaceState
from error_handling import ErrorHandler
from module_config import ModuleConfig
from display import Display
from networking import WirelessNetwork
from rfid.reader import RFIDReader
from config import RFID_ENABLED

class HID:
    
    def __init__(self) -> None:
        """
        Human Interface Device for event spaces providing buttons and status LEDs for space open state.
        Create HID instance and then run startup() to start services for button monitoring and LED output.
        """
        self.log = uLogger("HID")
        self.version = "1.1.1"
        self.loop_running = False
        self.moduleConfig = ModuleConfig()
        self.moduleConfig.register_display(Display())
        self.moduleConfig.register_wifi(WirelessNetwork())
        if RFID_ENABLED:
            self.moduleConfig.register_rfid(RFIDReader(Event()))
        self.display = self.moduleConfig.get_display()
        self.wifi = self.moduleConfig.get_wifi()
        self.reader = self.moduleConfig.get_rfid()
        self.spaceState = SpaceState(self.moduleConfig)
        self.errorHandler = ErrorHandler("HID")
        self.errorHandler.configure_display(self.display)
        
    def startup(self) -> None:
        """
        Initialise all async services for the HID.
        """
        self.log.info("--------Starting SMIBHID--------")
        self.log.info(f"SMIBHID firmware version: {self.version}")
        self.wifi.startup()
        self.display.clear()
        self.display.print_startup(self.version)
        self.display.set_busy_output()
        self.spaceState.startup()
        if self.reader:
            self.reader.startup()
      
        self.log.info("Entering main loop")        
        self.loop_running = True
        loop = get_event_loop()
        loop.run_forever()