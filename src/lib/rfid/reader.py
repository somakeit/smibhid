from lib.rfid.mfrc522 import MFRC522
from lib.rfid.users import user_tag_mapping
from asyncio import create_task, Event, sleep
from lib.ulogging import uLogger
from config import RFID_SCK, RFID_MOSI, RFID_MISO, RFID_RST, RFID_CS, BUZZER_PIN
from lib.error_handling import ErrorHandler
from machine import Pin
from lib.displays.display import Display

class RFIDReader:
    def __init__(self, tag_read_event: Event, display: Display, rfid_sck: int = RFID_SCK, rfid_mosi: int = RFID_MOSI, rfid_miso: int = RFID_MISO, rfid_rst: int = RFID_RST, rfid_cs: int = RFID_CS) -> None:
        """
        Pass in GPIO pins for RFID reader and an asyncio Event to signal when a tag is read. Defaults to config file values.
        Call startup() to start the RFID reader.
        Call get_last_tag_id() to get the last tag ID read.
        Call get_last_tag_user() to get the user associated with the last tag read based on the user_tag_mapping file.
        """
        self.log = uLogger("RFIDReader")
        self.error_handler = ErrorHandler("RFIDReader")
        self.rfid_sck = rfid_sck
        self.rfid_mosi = rfid_mosi
        self.rfid_miso = rfid_miso
        self.rfid_rst = rfid_rst
        self.rfid_cs = rfid_cs
        self.tag_read_event = tag_read_event
        self.last_tag_id = None
        self.co2_alarm_buzzer = Pin(BUZZER_PIN, Pin.OUT)
        self.display = display
        self.configure_error_handler()

    def configure_error_handler(self) -> None:
        """Configure the error handler with an RFID reader instance."""
        self.error_handler = ErrorHandler("RFIDReader")
        self.errors = {
            "CFG": "Incorrect RFID configuration"
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)
    
    def uidToString(self, uid) -> str:
        """Convert UID to string."""
        mystring = ""
        for i in uid:
            mystring = "%02X" % i + mystring
        return mystring
    
    def startup(self) -> None:
        """Init RFID reader startup methods."""
        self.log.info("Starting RFID reader")
        create_task(self.async_poll())
    
    async def async_beep_buzzer(self) -> None:
        """
        Beep the buzzer for 0.2 seconds
        """
        self.co2_alarm_buzzer.value(1)
        await sleep(0.2)
        self.co2_alarm_buzzer.value(0)
    
    async def async_timeout_tag_display(self, timeout: int = 5) -> None:
        """Clear the tag display after a timeout period."""
        await sleep(timeout)
        self.display.print_show_status()

    async def async_poll(self) -> None:
        """Poll the RFID reader for tags, store the tag value and signal the tag_read_event when a tag detected."""
        try:
            self.log.info("Initialising RFID reader poller")
            self.tag_read_event.clear()
            rdr = MFRC522(self.rfid_sck, self.rfid_mosi, self.rfid_miso, self.rfid_rst, self.rfid_cs)

        except Exception as e:
            self.log.error(f"Error in RFID polling: {e}, RFID poller not started.")
            self.error_handler.enable_error("CFG")
            return

        while True:
            (stat, unused_tag_type) = await rdr.async_request(rdr.REQIDL)

            if stat == rdr.OK:
        
                (stat, uid) = rdr.SelectTagSN()
            
                if stat == rdr.OK:
                    create_task(self.async_beep_buzzer())
                    self.last_tag_id = self.uidToString(uid)
                    username = user_tag_mapping.get(self.last_tag_id, "TagID: %s" % self.last_tag_id)
                    self.log.info(f"Tag read: {username}")
                    self.tag_read_event.set()
                    self.display.tag_read(username)
                    self.tag_display_timeout_task = create_task(self.async_timeout_tag_display(5))
                else:
                    print("Authentication error")
    
    def get_tag_read_event(self) -> Event:
        """Return the tag read event for signalling when a tag is read."""
        return self.tag_read_event
    
    def get_last_tag_id(self) -> str:
        """Return the last tag ID read."""
        return self.last_tag_id

    def get_last_tag_user(self) -> str:
        """Return the user associated with the last tag read based on the user_tag_mapping file."""
        return user_tag_mapping.get(self.last_tag_id, "Unknown: %s" % self.last_tag_id)    
    