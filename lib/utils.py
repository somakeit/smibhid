from time import sleep
from machine import Pin
import uasyncio
from lib.ulogging import uLogger

class Status_LED:
    """
    Instantiate an LED on a GPIO pin or leave pin unset for onboard LED.
    Info log level output of state changes.
    Supports sync and async flash functions taking count and frequency arguments.
    """
    def __init__(self, log_level: int, gpio_pin=None) -> None:
        self.logger = uLogger("Status_LED", log_level)
        self.pin_number = gpio_pin
        if self.pin_number:
            self.status_led = Pin(gpio_pin, Pin.OUT)
        else:
            self.status_led = Pin("LED", Pin.OUT)
    
    def on(self) -> None:
        """"Turn the LED on"""
        self.logger.info(f"Pin {self.pin_number}: LED on")
        self.status_led.on()

    def off(self) -> None:
        """"Turn the LED off"""
        self.logger.info(f"Pin {self.pin_number}: LED off")
        self.status_led.off()

    async def async_flash(self, count: int, hz: float) -> None:
        """Flash the LED a number of times at a given frequency using async awaits on the sleep function."""
        self.off()
        sleep_duration = (1 / hz) / 2
        for unused in range(count):
            await uasyncio.sleep(sleep_duration)
            self.on()
            await uasyncio.sleep(sleep_duration)
            self.off()
    
    def flash(self, count: int, hz: float) -> None:
        """Flash the LED a number of times at a given frequency using standrad blocking sleep function."""
        self.off()
        sleep_duration = (1 / hz) / 2
        for unused in range(count):
            sleep(sleep_duration)
            self.on()
            sleep(sleep_duration)
            self.off()