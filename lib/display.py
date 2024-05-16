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
    def __init__(self, log_level: int) -> None:
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
        self.lcd.clear()
    
    def _text_to_line(self, text: str) -> str:
        text = text[:16]
        text = "{:<16}".format(text)
        return text

    @check_enabled
    def print_top_line(self, text: str) -> None:
        self.lcd.setCursor(0, 0)
        self.lcd.printout(self._text_to_line(text))
    
    @check_enabled
    def print_bottom_line(self, text: str) -> None:
        self.lcd.setCursor(0, 1)
        self.lcd.printout(self._text_to_line(text))

    @check_enabled
    def print_space_state(self, state: str) -> None:
        self.print_bottom_line(f"Space: {state}")