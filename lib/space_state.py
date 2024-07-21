"""
Classes related to space state management.
"""

from asyncio import Event, create_task, sleep, wait_for, CancelledError

import config
from lib.button import Button
from lib.constants import CLOSED, OPEN
from lib.error_handling import ErrorHandler
from lib.module_config import ModuleConfig
from lib.slack_api import Wrapper
from lib.ulogging import uLogger
from lib.utils import StatusLED
from lib.uistate import UIState
from time import ticks_ms


class SpaceState:
    """
    Management of the space state, including driving the space state LED's, the space
    state display, and the space state buttons.
    Makes calls to the SMIB server to update the space state and to get the
    current space state.
    Leverages a state machine to determine the current spacestate mode for menu interaction using the buttons where a display is present.
    """

    def __init__(self, module_config: ModuleConfig, hid: object) -> None:
        """
        Configures error handling for space state module.
        ModuleConfig is used to get the display and wifi instances.
        HID is used to call the appropriate UI state functions when the space
        open and closed buttons are pressed as HID hosts the UI state.
        """
        self.log = uLogger("SpaceState")
        self.hid = hid
        self.display = module_config.get_display()
        self.wifi = module_config.get_wifi()
        self.slack_api = Wrapper(self.wifi)
        self.space_open_button_event = Event()
        self.space_closed_button_event = Event()
        self.open_button = Button(
            config.SPACE_OPEN_BUTTON, "Space_open", self.space_open_button_event
        )
        self.closed_button = Button(
            config.SPACE_CLOSED_BUTTON, "Space_closed", self.space_closed_button_event
        )
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
        self.state_check_error_open_led_flash_task = None
        self.state_check_error_closed_led_flash_task = None
        self.last_button_press_ms = 0
        self.configure_error_handling()

    def configure_error_handling(self) -> None:
        """
        Register errors with the error handler for the space state module.
        """
        self.error_handler = ErrorHandler("SpaceState")
        self.errors = {
            "API": "Space state API slow responding.",
            "CHK": "Failure checking space state.",
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)

    def startup(self) -> None:
        """
        Start the space state module. This includes starting the button
        watchers, the space state poller, and setting the initial space state.
        """
        self.log.info(f"Starting {self.open_button.get_name()} button watcher")
        create_task(self.open_button.wait_for_press())
        self.log.info(f"Starting {self.closed_button.get_name()} button watcher")
        create_task(self.closed_button.wait_for_press())
        self.log.info(
            f"Starting {self.open_button.get_name()} button pressed event catcher"
        )
        create_task(self.async_space_open_button_watcher())
        self.log.info(
            f"Starting {self.closed_button.get_name()} button pressed event catcher"
        )
        create_task(self.async_space_close_button_watcher())

        if self.space_state_poll_frequency != 0:
            self.log.info(
                f"Starting space state poller with frequency of \
                    {self.space_state_poll_frequency} seconds"
            )
            create_task(self.async_space_state_watcher())
        else:
            self.log.info("Space state poller disabled by config")

    def set_output_space_open(self) -> None:
        """
        Set LED's and display to show the space as open.
        """
        self.space_state = True
        self.space_open_led.on()
        self.space_closed_led.off()
        self.display.update_state("Open")
        self.hid.ui_state_instance.transition_to(OpenState(self.hid, self))
        self.log.info("Space state is open.")

    def set_output_space_closed(self) -> None:
        """
        Set LED's and display to show the space as closed.
        """
        self.space_state = False
        self.space_open_led.off()
        self.space_closed_led.on()
        self.display.update_state("Closed")
        self.hid.ui_state_instance.transition_to(ClosedState(self.hid, self))
        self.log.info("Space state is closed.")

    def set_output_space_none(self) -> None:
        """
        Set LED's and display to show the space as unknown.
        """
        self.space_state = None
        self.space_open_led.off()
        self.space_closed_led.off()
        self.display.update_state("None")
        self.hid.ui_state_instance.transition_to(NoneState(self.hid, self))
        self.log.info("Space state is none.")

    def _set_space_state_check_to_error(self) -> None:
        """
        Activities relating to space_state check moving to error state.
        """
        self.log.info("Space state check has errored.")
        if not self.error_handler.is_error_enabled("CHK"):
            self.error_handler.enable_error("CHK")
            self.state_check_error_open_led_flash_task = create_task(
                self.space_open_led.async_constant_flash(2)
            )
            self.state_check_error_closed_led_flash_task = create_task(
                self.space_closed_led.async_constant_flash(2)
            )

    def _set_space_state_check_to_ok(self) -> None:
        """
        Activities relating to space_state check moving to ok state.
        """
        self.log.info("Space state check status error has cleared")
        if self.error_handler.is_error_enabled("CHK"):
            self.error_handler.disable_error("CHK")
            if self.state_check_error_open_led_flash_task is not None:
                self.state_check_error_open_led_flash_task.cancel()
            if self.state_check_error_closed_led_flash_task is not None:
                self.state_check_error_closed_led_flash_task.cancel()
            self.space_open_led.off()
            self.space_closed_led.off()
            self._set_space_output(self.space_state)

    def _free_to_check_space_state(self) -> bool:
        """
        Check that we're not already checking for space state.
        """
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
        """
        Call appropriate space output configuration method for new space state.
        """
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
        Checks space state from server and sets SMIDHID output to reflect
        current space state, including errors if space state not available.
        """
        self.log.info("Checking space state")
        self.display.set_busy_output()
        if not self._free_to_check_space_state():
            return
        else:
            try:
                self.log.info("Checking space status from server")
                new_space_state = await wait_for(
                    self.slack_api.async_get_space_state(),
                    self.checking_space_state_timeout_s,
                )
                self.log.info(
                    f"Space state is: {new_space_state}, was: {self.space_state}"
                )
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

    async def async_space_open_button_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space open
        button press event and taking appropriate actions.
        """
        while True:
            await self.space_open_button_event.wait()
            self.space_open_button_event.clear()
            self.last_button_press_ms = ticks_ms()
            await self.hid.ui_state_instance.async_on_space_open_button()


    async def async_space_close_button_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space
        close button press event and taking appropriate actions.
        """
        while True:
            await self.space_closed_button_event.wait()
            self.space_closed_button_event.clear()
            self.last_button_press_ms = ticks_ms()
            await self.hid.ui_state_instance.async_on_space_closed_button()

    async def async_space_state_watcher(self) -> None:
        """
        Coroutine to frequently poll the space state from the slack server and
        update SMIBHID output if the state has changed.
        """

        async def task_wrapper_for_error_handling():
            try:
                await self.async_update_space_state_output()
            except Exception as e:
                self.log.error(
                    f"State poller task encountered an error updating space state: {e}"
                )

        while True:
            self.log.info("Polling space state")
            try:
                create_task(task_wrapper_for_error_handling())
            except CancelledError as e:
                self.log.info(f"State poller task cancelled: {e}")
            finally:
                await sleep(self.space_state_poll_frequency)

class SpaceStateUIState(UIState):
    """
    Base class for space state UI state.
    """
    def __init__(self, hid: object, space_state: SpaceState) -> None:
        super().__init__(hid, space_state)
        self.open_for_hours = 0

    def last_button_press_x_seconds_ago(self, x: int = 2) -> bool:
        """
        Check if the last button press was x seconds ago.
        """
        now = ticks_ms()
        return now - self.space_state.last_button_press_ms > (x * 1000)
    
    def increment_open_for_hours_single_digit(self) -> None:
        """
        Increment the open for hours counter.
        """
        if self.open_for_hours < 9:
            self.open_for_hours += 1
        else:
            self.open_for_hours = 0
        
        self.hid.display.update_open_for_hours(self.open_for_hours) # TODO: make this display function
    
    async def _async_button_timeout_watcher(self) -> None:
        """
        Call open space with current open hours count if no button press for 2 seconds.
        """
        while not self.last_button_press_x_seconds_ago(2):
            await sleep(0.1)

        await self._async_open_space(self.open_for_hours)

class OpenState(UIState):
    """
    UI state for open space state.
    """
    def __init__(self, hid: object, space_state: SpaceState) -> None:
        super().__init__(hid, space_state)

    async def async_on_space_closed_button(self) -> None:
        await super().async_on_space_closed_button()

    async def async_on_space_open_button(self) -> None:
        self.log.info("Space is already open")

class ClosedState(UIState):
    """
    UI state for closed space state.
    """
    def __init__(self, hid: object, space_state: SpaceState) -> None:
        super().__init__(hid, space_state)

    async def async_on_space_closed_button(self) -> None:
        self.log.info("Space is already closed")

    async def async_on_space_open_button(self) -> None:
        await super().async_on_space_open_button()

class NoneState(UIState):
    """
    UI state for unknown space state.
    """
    def __init__(self, hid: object, space_state: SpaceState) -> None:
        super().__init__(hid, space_state)
    
    async def async_on_space_closed_button(self) -> None:
        await super().async_on_space_closed_button()

    async def async_on_space_open_button(self) -> None:
        await super().async_on_space_open_button()

class AddingHoursState(SpaceStateUIState):
    """
    UI state for adding hours to the open for hours counter.
    """
    def __init__(self, hid: object, space_state: SpaceState) -> None:
        super().__init__(hid, space_state)
        self.log.info("Entering AddingHoursState")
        self.update_display_open_for_hours()

    def on_enter(self) -> None:
        super().on_enter()
        self.hid.display.add_hours_screen(self.open_for_hours) # TODO make this display function
        create_task(self._async_button_timeout_watcher())

    async def async_on_space_closed_button(self) -> None:
        self.hid.display.cancelling_update() # TODO make this display function
        await sleep(2)
        self.space_state._set_space_output(CLOSED)
        self.hid.ui_state_instance.transition_to(ClosedState(self.hid, self.space_state))

    async def async_on_space_open_button(self) -> None:
        self.increment_open_for_hours_single_digit()
