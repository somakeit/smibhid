from time import sleep, mktime, gmtime
from machine import Pin, RTC
from os import listdir, mkdir
import uasyncio
from lib.ulogging import uLogger

def check_and_create_folder(logger: uLogger, path: str, folder: str) -> bool:
    """
    Check if folder exists under path, creating it if not. path may or
    may not have a trailing slash.
    """
    logger.info(f"Checking for {folder} in {path}")
    try:
        if folder not in listdir(path[0:-1] if path.endswith("/") else path):
            logger.info(f"{folder} does not exist in {path} - creating")
            mkdir(path + folder)
            logger.info(f"{path + folder} folder created")
        else:
            logger.info(f"{folder} exists in {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to check for {folder} in {path}: {e}")
        return False

class ListWriter:
    """
    Minimal file-like object accepting sys.print_exception()'s write()
    calls, so a traceback can be captured as a string for passing to the
    logger.
    """
    def __init__(self) -> None:
        self.chunks = []

    def write(self, data: str) -> int:
        self.chunks.append(data)
        return len(data)

class StatusLED:
    """
    Instantiate an LED on a GPIO pin or leave pin unset for onboard LED.
    Info log level output of state changes.
    Supports sync and async flash functions taking count and frequency arguments.
    """
    def __init__(self, gpio_pin: int = -1) -> None:
        self.logger = uLogger("Status_LED")
        if gpio_pin > -1:
            self.status_led = Pin(gpio_pin, Pin.OUT)
            self.pin_id = gpio_pin
        else:
            self.status_led = Pin("LED", Pin.OUT)
            self.pin_id = "LED"
    
    def on(self) -> None:
        """"Turn the LED on"""
        self.logger.info(f"Pin {self.pin_id}: LED on")
        self.status_led.on()

    def off(self) -> None:
        """"Turn the LED off"""
        self.logger.info(f"Pin {self.pin_id}: LED off")
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
    
    async def async_constant_flash(self, hz: float) -> None:
        """
        Flash the LED constantly at a given frequency using async awaits on the sleep function.
        This should be started by task = asyncio.create_task() and cancelled with task.cancel().
        """
        self.off()
        sleep_duration = (1 / hz) / 2
        while True:
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

class DateTimeUtils:
    """
    Utility class for handling extra date and time operations.
    """
    
    def __init__(self) -> None:
        self.logger = uLogger("DateTimeUtils")
        
    def datetime_string(self) -> str:
        """
        Get the current datetime from the onboard RTC as a string in ISO 8601 format.
        """
        dt = RTC().datetime()
        return "{0:04d}-{1:02d}-{2:02d}T{4:02d}:{5:02d}:{6:02d}Z".format(*dt)

    def timestamp_to_iso8601(self, timestamp: float) -> str:
        """
        Convert a Unix timestamp (UTC) to an ISO 8601 formatted string.
        """
        try:
            year, month, day, hour, minute, second, *_ = gmtime(timestamp)
        except Exception as e:
            self.logger.error(f"Failed to convert timestamp to ISO 8601: {e}")
            return "0000-00-00T00:00:00Z"
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"

    def timestamp(self, dt: str) -> float:
        """
        Convert a datetime string in ISO 8601 format to a Unix timestamp.
        """
        year = int(dt[0:4])
        month = int(dt[5:7])
        day = int(dt[8:10])
        hour = int(dt[11:13])
        minute = int(dt[14:16])
        second = int(dt[17:19])
        return mktime((year, month, day, hour, minute, second, 0, 0))
            
    def uk_bst(self) -> bool:
        """
        Return True if the UK is currently in BST - requires manual update of
        bst_timestamps {} dict over time.
        """
        dt = self.datetime_string()
        year = int(dt[0:4])
        ts = self.timestamp(dt)
        bst = False

        bst_timestamps = {
            2025: {"start": 1743296400, "end": 1761440400},
            2026: {"start": 1774746000, "end": 1792890000},
            2027: {"start": 1806195600, "end": 1824944400},
            2028: {"start": 1837645200, "end": 1856394000},
            2029: {"start": 1869094800, "end": 1887843600},
            2030: {"start": 1901149200, "end": 1919293200}
        }

        if year in bst_timestamps:
            if bst_timestamps[year]["start"] < ts and bst_timestamps[year]["end"] > ts:
                self.logger.info(f"Current time {dt} is in BST for year {year}")
                bst = True
            else:
                self.logger.info(f"Current time {dt} is not in BST for year {year}")
        else:
            self.logger.warn(f"Provided year is not in BST lookup dictionary: {year}")
            raise ValueError(f"Provided year {year} is not in BST lookup dictionary.")
        return bst
