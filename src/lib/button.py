"""
Classes relating to button use and management, leveraging asyncio Events to
signal button presses.
"""

from asyncio import Event, sleep
from re import sub

from machine import Pin

from lib.ulogging import uLogger


class Button:
    """
    Class to represent a button, with a name, GPIO pin, and an Event to signal
    """

    def __init__(
        self, gpio_pin: int, button_name: str, button_pressed_event: Event
    ) -> None:
        self.logger = uLogger(f"Button {gpio_pin}")
        self.gpio = gpio_pin
        self.pin = Pin(gpio_pin, Pin.IN, Pin.PULL_UP)
        self.name = button_name
        self.button_pressed = button_pressed_event

    async def wait_for_press(self) -> None:
        """
        Button press watcher, which will wait for a button press and then set
        the event passed to the constructor.
        Also logs button press and release.
        """
        self.logger.info(f"Starting button press watcher for button: {self.name}")

        while True:
            current_value = self.pin.value()
            active = 0
            while active < 20:
                if self.pin.value() != current_value:
                    active += 1
                else:
                    active = 0
                await sleep(0.001)

            if self.pin.value() == 0:
                self.logger.info(f"Button pressed: {self.name}")
                self.button_pressed.set()
            else:
                self.logger.info(f"Button released: {self.name}")

    def get_name(self) -> str:
        """Get the name of the button"""
        return self.name
    
    def get_id(self) -> str:
        """Get the ID of the button"""
        return sub(r"\s+", "_", self.name).lower()
    
    def get_pin(self) -> int:
        """Get the GPIO pin of the button"""
        return self.gpio
