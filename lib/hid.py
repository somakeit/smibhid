from ulogging import uLogger
from asyncio import get_event_loop, Event, create_task
from slack_api import Wrapper
from display import Display
from space_state import SpaceState
from error_handling import ErrorHandling

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
        self.error_event = Event()
        self.loaded_modules = []
        self.spaceState = SpaceState(self.error_event, self.display)
        self.loaded_modules.append(self.spaceState) # TODO this should be space state registering with error handling module
        self.error_handling = ErrorHandling(self.display, self.error_event, self.loaded_modules)
        
    def startup(self) -> None:
        """
        Initialise all aysnc services for the HID.
        """
        self.log.info("--------Starting SMIBHID--------")
        self.log.info(f"SMIBHID firmware version: {self.version}")
        self.display.clear()
        self.display.print_startup(self.version)
        self.spaceState.startup()
        self.error_handling.startup()
      
        self.log.info("Entering main loop")        
        self.loop_running = True
        loop = get_event_loop()
        loop.run_forever()