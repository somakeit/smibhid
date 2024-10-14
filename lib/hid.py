from lib.ulogging import uLogger
from asyncio import get_event_loop, Event
from lib.space_state import SpaceState, NoneState, OpenState, ClosedState
from lib.error_handling import ErrorHandler
from lib.module_config import ModuleConfig
from lib.display import Display
from lib.networking import WirelessNetwork
from lib.rfid.reader import RFIDReader
from config import RFID_ENABLED
from lib.uistate import UIState
from lib.ui_log import UILog
from http.website import Web_App

class HID:
    
    def __init__(self) -> None:
        """
        Human Interface Device for event spaces providing buttons and status LEDs for space open state.
        Create HID instance and then run startup() to start services for button monitoring and LED output.
        """
        self.log = uLogger("HID")
        self.log.warn("SMIBHID has been restarted")
        self.version = "1.2.0"
        self.loop_running = False
        self.moduleConfig = ModuleConfig()
        self.moduleConfig.register_display(Display())
        self.moduleConfig.register_wifi(WirelessNetwork())
        if RFID_ENABLED:
            self.moduleConfig.register_rfid(RFIDReader(Event()))
        self.display = self.moduleConfig.get_display()
        self.wifi = self.moduleConfig.get_wifi()
        self.moduleConfig.register_ui_log(UILog(self.wifi))
        self.reader = self.moduleConfig.get_rfid()
        self.ui_log = self.moduleConfig.get_ui_log()
        self.space_state = SpaceState(self.moduleConfig, self)
        self.error_handler = ErrorHandler("HID")
        self.error_handler.configure_display(self.display)
        self.web_app = Web_App(self.moduleConfig, self)
        self.ui_state_instance = StartUIState(self, self.space_state)
        self.ui_state_instance.on_enter()

    def set_ui_state(self, state):
        self.ui_state_instance = state
    
    def get_ui_state(self):
        return self.ui_state_instance

    def startup(self) -> None:
        """
        Initialise all async services for the HID.
        """
        self.log.info("--------Starting SMIBHID--------")
        self.log.info(f"SMIBHID firmware version: {self.version}")
        self.wifi.startup()
        self.space_state.startup()
        if self.reader:
            self.reader.startup()
        self.ui_log.startup()
        self.web_app.startup()
      
        self.log.info("Entering main loop")        
        self.switch_to_appropriate_spacestate_uistate()
        self.loop_running = True
        loop = get_event_loop()
        loop.run_forever()

    def switch_to_appropriate_spacestate_uistate(self) -> None:
        """
        Determine the current state of the space and switch to the appropriate
        UI state.
        """       
        self.log.info("Switching to appropriate UI state based on space state")
        if self.space_state.space_state is None:
            self.log.info("Space state is None, transitioning to NoneState")
            self.ui_state_instance.transition_to(NoneState(self, self.space_state))
        elif self.space_state.space_state is True:
            self.log.info("Space state is open, transitioning to OpenState")
            self.ui_state_instance.transition_to(OpenState(self, self.space_state))
        elif self.space_state.space_state is False:
            self.log.info("Space state is closed, transitioning to ClosedState")
            self.ui_state_instance.transition_to(ClosedState(self, self.space_state))
        else:
            self.log.error("Space state is in an unexpected state")
            raise ValueError("Space state is in an unexpected state")
    
class StartUIState(UIState):
    
    def __init__(self, hid: HID, space_state: SpaceState) -> None:
        super().__init__(hid, space_state)
        self.display = self.hid.display
        self.version = self.hid.version

    def on_enter(self):
        super().on_enter()
        self.display.clear()
        self.display.print_startup(self.version)
        self.display.set_busy_output()

    def on_exit(self):
        super().on_exit()
