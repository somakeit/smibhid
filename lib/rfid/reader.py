from lib.rfid.mfrc522 import MFRC522
from lib.rfid.users import user_tag_mapping
from asyncio import create_task, Event
from ulogging import uLogger

class RFIDReader:
    def __init__(self, RFID_SCK, RFID_MOSI, RFID_MISO, RFID_RST, RFID_CS, tag_read_event: Event) -> None:
        """
        Pass in GPIO pins for RFID reader and an asyncio Event to signal when a tag is read.
        Call startup() to start the RFID reader.
        Call get_last_tag_id() to get the last tag ID read.
        Call get_last_tag_user() to get the user associated with the last tag read based on the user_tag_mapping file.
        """
        self.log = uLogger("RFIDReader")
        self.RFID_SCK = RFID_SCK
        self.RFID_MOSI = RFID_MOSI
        self.RFID_MISO = RFID_MISO
        self.RFID_RST = RFID_RST
        self.RFID_CS = RFID_CS
        self.tag_read_event = tag_read_event
        self.last_tag_id = None

    def uidToString(self, uid) -> str:
        mystring = ""
        for i in uid:
            mystring = "%02X" % i + mystring
        return mystring
    
    def startup(self) -> None:
        self.log.info("Starting RFID reader")
        create_task(self.async_poll())
    
    async def async_poll(self) -> None:
            
        rdr = MFRC522(self.RFID_SCK, self.RFID_MOSI, self.RFID_MISO, self.RFID_RST, self.RFID_CS)

        while True:
            (stat, unused_tag_type) = await rdr.async_request(rdr.REQIDL)

            if stat == rdr.OK:
        
                (stat, uid) = rdr.SelectTagSN()
            
                if stat == rdr.OK:
                    print("User: %s" % user_tag_mapping.get(self.uidToString(uid), "Unknown: %s" % self.uidToString(uid)))
                    self.last_tag_id = self.uidToString(uid)
                    self.tag_read_event.set()
                else:
                    print("Authentication error")
    
    def get_tag_read_event(self) -> Event:
        return self.tag_read_event
    
    def get_last_tag_id(self) -> str:
        return self.last_tag_id

    def get_last_tag_user(self) -> str:
        return user_tag_mapping.get(self.last_tag_id, "Unknown: %s" % self.last_tag_id)    
    