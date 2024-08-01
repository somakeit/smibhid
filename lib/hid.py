from lib.ulogging import uLogger
from asyncio import get_event_loop, Event, create_task, sleep
from lib.space_state import SpaceState, NoneState, OpenState, ClosedState
from lib.error_handling import ErrorHandler
from lib.module_config import ModuleConfig
from lib.display import Display
from lib.networking import WirelessNetwork
from lib.rfid.reader import RFIDReader
from config import RFID_ENABLED, ENABLE_UI_LOGGING_UPLOAD
from lib.uistate import UIState
from lib.slack_api import Wrapper

class HID:
    
    def __init__(self) -> None:
        """
        Human Interface Device for event spaces providing buttons and status LEDs for space open state.
        Create HID instance and then run startup() to start services for button monitoring and LED output.
        """
        self.log = uLogger("HID")
        self.version = "1.2.0"
        self.loop_running = False
        self.moduleConfig = ModuleConfig()
        self.moduleConfig.register_display(Display())
        self.moduleConfig.register_wifi(WirelessNetwork())
        if RFID_ENABLED:
            self.moduleConfig.register_rfid(RFIDReader(Event()))
        self.display = self.moduleConfig.get_display()
        self.wifi = self.moduleConfig.get_wifi()
        self.reader = self.moduleConfig.get_rfid()
        self.space_state = SpaceState(self.moduleConfig, self)
        self.errorHandler = ErrorHandler("HID")
        self.errorHandler.configure_display(self.display)
        self.ui_state_instance = StartUIState(self, self.space_state)
        self.ui_state_instance.on_enter()
        self.slack = Wrapper(self.wifi)
        self.ui_log = []
        self.configure_error_handling()

    def configure_error_handling(self) -> None:
        """
        Register errors with the error handler for the space state module.
        """
        self.errors = {
            "UIL": "Failed to upload UI log"
        }

        for error_key, error_message in self.errors.items():
            self.errorHandler.register_error(error_key, error_message)

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
        create_task(self.async_ui_log_uploader())
      
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
    
    async def async_ui_log_uploader(self) -> None:
        """
        Periodically upload the UI log to the server.
        """
        while True:
            self.log.info("Uploading UI log to server")
            if self.ui_log:
                if ENABLE_UI_LOGGING_UPLOAD:
                    self.log.info("UI log contains data, uploading to server")
                    try:
                        await self.slack.async_upload_ui_log(self.ui_log)
                        self.log.info("UI log uploaded successfully")
                        self.log.info("Clearing UI log")
                        self.ui_log = []
                        self.errorHandler.disable_error("UIL")
                    except Exception as e:
                        self.log.error(f"Failed to upload UI log: {e}")
                        self.errorHandler.enable_error("UIL")
                
                else:
                    self.log.info("UI logging is disabled, no upload will occur")
                    self.log.info(f"UI log: {self.ui_log}")
                    self.log.info("Clearing UI log")
                    self.ui_log = []

            else:
                self.log.info("UI log is empty, no upload required")
            
            await sleep(51)

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
