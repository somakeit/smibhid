from LCD1602 import LCD1602
from config import I2C_ID, SCL_PIN, SDA_PIN
from ulogging import uLogger

def check_enabled(method):
        def wrapper(self, *args, **kwargs):
            if self.enabled:
                return method(self, *args, **kwargs)
            return None
        return wrapper

class Display:
    """
    Display management for SMIBHID to drive displays via driver classes abstracting display constraints from the messaging required.
    Provides functions to clear display and print top or bottom line text.
    Currently supports 2x16 character LCD display.
    """
    def __init__(self, log_level: int) -> None:
        """Connect to display using configu file values for I2C"""
        self.log = uLogger("Display", log_level)
        self.log.info("Init display")
        self.enabled = True
        try:
            self.lcd = LCD1602(log_level, I2C_ID, SDA_PIN, SCL_PIN, 16, 2)
        except Exception:
            self.log.error("Error initialising display on I2C bus. Disabling display functionality.")
            self.enabled = False
    
    @check_enabled
    def clear(self) -> None:
        """Clear entire screen"""
        self.lcd.clear()
    
    def _text_to_line(self, text: str) -> str:
        """Internal function to ensure line fits the screen and no previous line text is present for short strings."""
        text = text[:16]
        text = "{:<16}".format(text)
        return text

    @check_enabled
    def print_top_line(self, text: str) -> None:
        """Print up to 16 characters on the top line."""
        self.lcd.setCursor(0, 0)
        self.lcd.printout(self._text_to_line(text))
    
    @check_enabled
    def print_bottom_line(self, text: str) -> None:
        """Print up to 16 characters on the bottom line."""
        self.lcd.setCursor(0, 1)
        self.lcd.printout(self._text_to_line(text))

    @check_enabled
    def print_space_state(self, state: str) -> None:
        """Abstraction for space state formatting and placement."""
        self.print_bottom_line(f"Space: {state}")