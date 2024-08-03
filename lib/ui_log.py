from time import time
from lib.button import Button
from lib.ulogging import uLogger
from asyncio import create_task, sleep
from config import ENABLE_UI_LOGGING_UPLOAD
from lib.error_handling import ErrorHandler
from lib.slack_api import Wrapper
from lib.networking import WirelessNetwork

class UILog:
    def __init__(self, wifi: WirelessNetwork) -> None:
        self.log = uLogger("UI Log")
        self.log.info("UI Log initialised")
        self.ui_log = []
        self.slack = Wrapper(wifi)
        self.configure_error_handling()

    def configure_error_handling(self) -> None:
        """
        Register errors with the error handler for the space state module.
        """
        self.error_handler = ErrorHandler("UI Log")
        self.errors = {
            "UIL": "Failed to upload UI log"
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)

    def startup(self) -> None:
        """
        Start the UI log uploader.
        """
        self.log.info("Starting UI log uploader")
        create_task(self.async_ui_log_uploader())
    
    def log_button_press(self, button: Button) -> None:
        self.log.info(f"Button press logged: {button.get_name()}")
        self.ui_log.append({"timestamp": time(), "type": "button_press", "event": {"button_id": button.get_id(), "button_name": button.get_name()}})
    
    def log_rotary_dial_input(self) -> None:
        self.log.info("Rotary dial input logged")
    
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
                        self.error_handler.disable_error("UIL")
                    except Exception as e:
                        self.log.error(f"Failed to upload UI log: {e}")
                        self.error_handler.enable_error("UIL")
                
                else:
                    self.log.info("UI logging is disabled, no upload will occur")
                    self.log.info(f"UI log: {self.ui_log}")
                    self.log.info("Clearing UI log")
                    self.ui_log = []

            else:
                self.log.info("UI log is empty, no upload required")
            
            await sleep(51)