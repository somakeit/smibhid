from ulogging import uLogger
import config
from button import Button
from uasyncio import Event, create_task, get_event_loop
from utils import Status_LED
from slack_api import Wrapper

class HID:
    
    def __init__(self, loglevel: int = 2) -> None:
        """
        Human Interface Device for event spaces providing buttons and status LEDs for space open state.
        Create HID instance and then run startup() to start services for button monitoring and LED output.
        """
        self.log = uLogger("HID", loglevel)
        self.space_open_button_event = Event()
        self.space_closed_button_event = Event()
        self.open_button = Button(loglevel, config.SPACE_OPEN_BUTTON, "Space_open", self.space_open_button_event)
        self.closed_button = Button(loglevel, config.SPACE_CLOSED_BUTTON, "Space_closed", self.space_closed_button_event)
        self.space_open_led = Status_LED(loglevel, config.SPACE_OPEN_LED)
        self.space_closed_led = Status_LED(loglevel, config.SPACE_CLOSED_LED)
        self.space_open_led.on()
        self.space_closed_led.off()
        self.slack_api = Wrapper()
        self.loop_running = False

    def startup(self) -> None:
        """
        Initialise all aysnc servcies for the HID.
        """
        self.log.info(f"Starting HID")
        self.log.info(f"Starting {self.open_button.get_name()} button watcher")
        create_task(self.open_button.wait_for_press())
        self.log.info(f"Starting {self.closed_button.get_name()} button watcher")
        create_task(self.closed_button.wait_for_press())
        self.log.info(f"Starting {self.open_button.get_name()} button pressed event catcher")
        create_task(self.space_opened_watcher())
        self.log.info(f"Starting {self.closed_button.get_name()} button pressed event catcher")
        create_task(self.space_closed_watcher())

        self.log.info(f"Entering main loop")        
        self.loop_running = True
        loop = get_event_loop()
        loop.run_forever()

    async def space_opened_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space open button press event and taking appropriate actions.
        """
        while True:
            await self.space_open_button_event.wait()
            self.space_open_button_event.clear()
            try:
                response = self.slack_api.space_open()
                self.space_open_led.on()
                self.space_closed_led.off()
                self.log.info(f"Space state set to opened successfully, API response: {response}")
            except Exception as e:
                self.log.warn(f"An exception was encountered trying to set SMIB space state: {e}")


    async def space_closed_watcher(self) -> None:
        """
        Coroutine to be added to the async loop for watching for the space close button press event and taking appropriate actions.
        """
        while True:
            await self.space_closed_button_event.wait()
            self.space_closed_button_event.clear()
            try:
                response = self.slack_api.space_closed()
                self.space_closed_led.on()
                self.space_open_led.off()
                self.log.info(f"Space state set to closed successfully, API response: {response}")
            except Exception as e:
                self.log.warn(f"An exception was encountered trying to set SMIB space state: {e}")