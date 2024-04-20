from machine import Pin
import uasyncio
from lib.ulogging import uLogger
import uasyncio.event

class Button:

    def __init__(self, log_level: int, GPIO_pin: int, button_name: str, button_pressed_event: uasyncio.Event) -> None:
        self.log_level = log_level
        self.logger = uLogger(f"Button {GPIO_pin}", log_level)
        self.gpio = GPIO_pin
        self.pin = Pin(GPIO_pin, Pin.IN, Pin.PULL_UP)
        self.name = button_name
        self.button_pressed = button_pressed_event
   
    async def wait_for_press(self) -> None:
        self.logger.info(f"Starting button press watcher for button: {self.name}")

        while True:
            previous_value = self.pin.value()
            while (self.pin.value() == previous_value):
                previous_value = self.pin.value()
                await uasyncio.sleep(0.1)

            self.logger.info(f"Button pressed: {self.name}")
            self.button_pressed.set()

    def get_name(self) -> str:
        return self.name
    
    def get_pin(self) -> int:
        return self.gpio
