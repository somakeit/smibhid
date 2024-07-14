from ulogging import uLogger
import config
from utils import StatusLED
from button import Button
from asyncio import Event, create_task, sleep, wait_for
from constants import OPEN, CLOSED
from slack_api import Wrapper
from module_config import ModuleConfig
from error_handling import ErrorHandler

class SpaceState:
    def __init__(self, module_config: ModuleConfig) -> None:
        """
        Pass an asyncio event object to error_event and use a coroutine to
        monitor for event triggers to handle errors in space state checking
        by querying the is_in_error_state attribute.
        """
        self.log = uLogger("SpaceState")
        self.display = module_config.get_display()
        self.wifi = module_config.get_wifi()
        self.slack_api = Wrapper(self.wifi)
        self.space_open_button_event = Event()
        self.space_closed_button_event = Event()
        self.open_button = Button(config.SPACE_OPEN_BUTTON, "Space_open", self.space_open_button_event)
        self.closed_button = Button(config.SPACE_CLOSED_BUTTON, "Space_closed", self.space_closed_button_event)
        self.space_open_led = StatusLED(config.SPACE_OPEN_LED)
        self.space_closed_led = StatusLED(config.SPACE_CLOSED_LED)
        self.space_open_led.off()
        self.space_closed_led.off()
        self.space_state = None
        self.checking_space_state = False
        self.checking_space_state_timeout_s = 30
        self.space_state_poll_frequency = config.space_state_poll_frequency_s
        if self.space_state_poll_frequency != 0 and self.space_state_poll_frequency < 5:
            self.space_state_poll_frequency = 5
        self.configure_error_handling()

    def configure_error_handling(self) -> None:
        self.error_handler = ErrorHandler("SpaceState")
        self.errors = {
            "API": "Space state API slow responding.",
            "CHK": "Failure checking space state."
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)
    
    def startup(self) -> None:
        self.log.info(f"Starting {self.open_button.get_name()} button watcher")
        create_task(self.open_button.wait_for_press())
        self.log.info(f"Starting {self.closed_button.get_name()} button watcher")
        create_task(self.closed_button.wait_for_press())
        self.log.info(f"Starting {self.open_button.get_name()} button pressed event catcher")
        create_task(self.async_space_opened_watcher())
        self.log.info(f"Starting {self.closed_button.get_name()} button pressed event catcher")
        create_task(self.async_space_closed_watcher())
        
        if self.space_state_poll_frequency != 0:
            self.log.info(f"Starting space state poller with frequency of {self.space_state_poll_frequency} seconds")
            create_task(self.async_space_state_watcher())
        else:
            self.log.info("Space state poller disabled by config")
    
    def set_output_space_open(self) -> None:
        """Set LED's display etc to show the space as open"""
        self.space_state = True
        self.space_open_led.on()
        self.space_closed_led.off()
        self.display.update_state("Open")
        self.log.info("Space state is open.")
    
    def set_output_space_closed(self) -> None:
        """Set LED's display etc to show the space as closed"""
        self.space_state = False
        self.space_open_led.off()
        self.space_closed_led.on()
        self.display.update_state("Closed")
        self.log.info("Space state is closed.")

    def set_output_space_none(self) -> None:
        """Set LED's display etc to show the space as none"""
        self.space_state = None
        self.space_open_led.off()
        self.space_closed_led.off()
        self.display.update_state("None")
        self.log.info("Space state is none.")

    def _set_space_state_check_to_error(self) -> None:
        """Activities relating to space_state check moving to error state"""
        self.log.info("Space state check has errored.")
        if not self.error_handler.is_error_enabled("CHK"):
            self.error_handler.enable_error("CHK")
            self.state_check_error_open_led_flash_task = create_task(self.space_open_led.async_constant_flash(2))
            self.state_check_error_closed_led_flash_task = create_task(self.space_closed_led.async_constant_flash(2))
    
    def _set_space_state_check_to_ok(self) -> None:
        """Activities relating to space_state check moving to ok state"""
        self.log.info("Space state check status error has cleared")
        if self.error_handler.is_error_enabled("CHK"):
            self.error_handler.disable_error("CHK")
            self.state_check_error_open_led_flash_task.cancel()
            self.state_check_error_closed_led_flash_task.cancel()
            self.space_open_led.off()
            self.space_closed_led.off()
            self._set_space_output(self.space_state)

    def _free_to_check_space_state(self) -> bool:
        """Check that we're not already checking for space state"""
        self.log.info("Checking space state check state")
        if self.checking_space_state:
            self.log.warn("Already checking space state")
            if not self.error_handler.is_error_enabled("API"):
                self.error_handler.enable_error("API")
            return False
        else:
            self.log.info("Free to check space state")
            self.checking_space_state = True
            if self.error_handler.is_error_enabled("API"):
                self.error_handler.disable_error("API")
            return True
        
    def _set_space_output(self, new_space_state: bool | None) -> None:
        """Call appropriate space output configuration method for new space state."""
        if new_space_state is OPEN:
            self.set_output_space_open()
        elif new_space_state is CLOSED:
            self.set_output_space_closed()
        elif new_space_state is None:
            self.set_output_space_none()
        else:
            raise ValueError("Space state is not an expected value")
    
    async def async_update_space_state_output(self) -> None:
        """
        Checks space state from server and sets SMIDHID output to reflect current space state, including errors if space state not available.
        """
        self.log.info("Checking space state")
        self.display.set_busy_output()
        if not self._free_to_check_space_state():
            return
        else:
            try:
                self.log.info("Checking space status from server")
                new_space_state = await wait_for(self.slack_api.async_get_space_state(), self.checking_space_state_timeout_s)
                self.log.info(f"Space state is: {new_space_state}, was: {self.space_state}")
                self._set_space_output(new_space_state)
                self._set_space_state_check_to_ok()
            
            except Exception as e:
                self.log.error(f"Error encountered updating space state: {e}")
                self._set_space_state_check_to_error()
                raise
            
            finally:
                self.log.info("Setting checking_space_state to False")
                self.checking_space_state = False
                self.display.clear_busy_output()
    
    async def async_space_opened_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space open button press event and taking appropriate actions.
        """
        while True:
            await self.space_open_button_event.wait()
            self.space_open_button_event.clear()
            flash_task = create_task(self.space_open_led.async_constant_flash(4))
            try:
                await self.slack_api.async_space_open()
                flash_task.cancel()
                self.set_output_space_open()
                create_task(self.async_update_space_state_output())
            except Exception as e:
                self.log.error(f"An exception was encountered trying to set SMIB space state: {e}")
                flash_task.cancel()
                self.space_open_led.off()

    async def async_space_closed_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space close button press event and taking appropriate actions.
        """
        while True:
            await self.space_closed_button_event.wait()
            self.space_closed_button_event.clear()
            flash_task = create_task(self.space_closed_led.async_constant_flash(4))
            try:
                await self.slack_api.async_space_closed()
                flash_task.cancel()
                self.set_output_space_closed()
                create_task(self.async_update_space_state_output())
            except Exception as e:
                self.log.error(f"An exception was encountered trying to set SMIB space state: {e}")
                flash_task.cancel()
                self.space_closed_led.off()

    async def async_space_state_watcher(self) -> None:
        """
        Coroutine to frequently poll the space state from the slack server and update SMIBHID output if the state has changed.
        """

        async def task_wrapper_for_error_handling():
            try:
                await self.async_update_space_state_output()
            except Exception as e:
                self.log.error(f"State poller task encountered an error updating space state: {e}")

        while True:
            self.log.info("Polling space state")
            try:
                create_task(task_wrapper_for_error_handling())
            except Exception as e:
                self.log.error(f"State poller encountered an error creating task: {e}")
            finally:
                await sleep(self.space_state_poll_frequency)
