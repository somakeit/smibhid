from lib.ulogging import uLogger
# from lib.networking import Wireless_Network
from lib.uaiohttpclient import request

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, log_level: int = 2) -> None:
        self.log = uLogger("Slack API", debug_level=log_level)

    def space_open(self) -> int:
        """Call space_open."""
        try:
            self.log.info(f"Calling slack API: space_open")
            return 0
        except Exception as e:
            self.log.info(f"Failed to call slack API: space_open")
            return -1        
    
    def space_closed(self) -> int:
        """Call space_open."""
        try:
            self.log.info(f"Calling slack API: space_closed")
            return 0
        except:
            self.log.info(f"Failed to call slack API: space_closed")
            return -1