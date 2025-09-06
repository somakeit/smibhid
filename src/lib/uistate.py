from lib.ulogging import uLogger
from asyncio import create_task, sleep
from time import ticks_ms

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from lib.hid import HID
    from lib.space_state import SpaceState

class UIState:
    """
    State machine for the SMIBHID user interface.
    """
    def __init__(self, hid: HID, space_state: SpaceState) -> None:
        """
        Pass HID instance for global UI state reference.
        Pass SpaceState instance to allow space open and closed buttons to work
        in all UIs.
        """
        self.hid = hid
        self.space_state = space_state
        self.log = uLogger("UIState")
        self.state_change_API_timeout_s = 4

    def on_enter(self) -> None:
        """
        Default actions for entering a UI state.
        """
        self.log.info(f"Entering {self.__class__.__module__} {self.__class__.__name__} State")

    def on_exit(self) -> None:
        """
        Default actions for exiting a UI state.
        """
        self.log.info(f"Exiting {self.__class__.__module__} {self.__class__.__name__} State")

    def transition_to(self, state: 'UIState') -> None:
        """
        Move to a new UI state.
        """
        self.on_exit()
        self.hid.set_ui_state(state)
        state.on_enter()

    async def _async_close_space(self) -> None:
        """
        Default action for closing the space.
        """
        self.space_state.flash_task = create_task(self.space_state.space_closed_led.async_constant_flash(4))
        try:
            self.change_state_task = create_task(self.space_state.slack_api.async_space_closed())
            await self._async_space_state_change_timeout_check()
            if self.space_state.flash_task:
                self.space_state.flash_task.cancel()
            self.space_state.set_output_space_closed()
            create_task(self.space_state.async_update_space_state_output())
        except Exception as e:
            self.log.error(
                f"An exception was encountered trying to set SMIB space state: {e}"
            )
            self._abort_space_state_change()
    
    async def _async_open_space(self, open_for_hours: int = 0) -> None:
        """
        Default action for opening the space.
        """
        self.space_state.flash_task = create_task(self.space_state.space_open_led.async_constant_flash(4))
        try:
            self.change_state_task = create_task(self.space_state.slack_api.async_space_open(open_for_hours))
            await self._async_space_state_change_timeout_check()
            if self.space_state.flash_task:
                self.space_state.flash_task.cancel()
            self.space_state.set_output_space_open()
            create_task(self.space_state.async_update_space_state_output())
        except Exception as e:
            self.log.error(
                f"An exception was encountered trying to set SMIB space state: {e}"
            )
            self._abort_space_state_change()
    
    def _abort_space_state_change(self) -> None:
        """
        Cancel flash task and reset space state output to current state.
        """
        if self.space_state.flash_task:
            self.space_state.flash_task.cancel()
        self.space_state._set_space_output(self.space_state.space_state)
        create_task(self.space_state.async_update_space_state_output())

    async def _async_space_state_change_timeout_check(self) -> None:
        """
        Timeout check for space state change API call and raise exception if timeout reached.
        """
        now = ticks_ms()
        while not self.change_state_task.done():
            if now + (self.state_change_API_timeout_s * 1000) < ticks_ms():
                raise Exception("API call to change space state timed out")
            await sleep(0.01)
    
    async def async_on_space_closed_button(self) -> None:
        """
        Close space when space closed button pressed outside of space state UI.
        """
        await self._async_close_space()
    
    async def async_on_space_open_button(self) -> None:
        """
        Open space with no hours when when space open button pressed outside of space state UI.
        """
        await self._async_open_space()
