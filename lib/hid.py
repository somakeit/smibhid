from ulogging import uLogger
from asyncio import get_event_loop, Event, create_task
from slack_api import Wrapper
from display import Display
from space_state import SpaceState
from error_handling import ErrorHandler

class HID:
    
    def __init__(self) -> None:
        """
        Human Interface Device for event spaces providing buttons and status LEDs for space open state.
        Create HID instance and then run startup() to start services for button monitoring and LED output.
        """
        self.log = uLogger("HID")
        self.version = "1.1.0"     
        self.slack_api = Wrapper()
        self.loop_running = False
        self.display = Display()
        self.spaceState = SpaceState(self.display)
        self.errorHandler = ErrorHandler("HID")
        self.errorHandler.configure_display(self.display)
        
    def startup(self) -> None:
        """
        Initialise all aysnc services for the HID.
        """
        self.log.info("--------Starting SMIBHID--------")
        self.log.info(f"SMIBHID firmware version: {self.version}")
        self.display.clear()
        self.display.print_startup(self.version)
        self.spaceState.startup()
      
        self.log.info("Entering main loop")        
        self.loop_running = True
        loop = get_event_loop()
        loop.run_forever()