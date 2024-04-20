from lib.ulogging import uLogger
from lib.uaiohttpclient import request
from uasyncio import run
from lib.networking import Wireless_Network

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, log_level: int, wifi: Wireless_Network) -> None:
        self.log = uLogger("Slack API", debug_level=log_level)
        self.wifi = wifi

    async def space_open(self) -> int:
        """Call space_open."""
        self.log.info(f"Calling slack API: space_open")
        try:
            await self.wifi.check_network_access()
            return 0
        except Exception as e:
            self.log.info(f"Failed to call slack API: space_open")
            return -1        
    
    async def space_closed(self) -> int:
        """Call space_open."""
        self.log.info(f"Calling slack API: space_closed")
        try:
            await self.wifi.check_network_access()
            return 0
        except:
            self.log.info(f"Failed to call slack API: space_closed")
            return -1