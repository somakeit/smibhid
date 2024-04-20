from lib.ulogging import uLogger
import lib.uaiohttpclient as httpclient
from uasyncio import run
from lib.networking import Wireless_Network
from config import WEBSERVER_HOST, WEBSERVER_PORT

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, log_level: int, wifi: Wireless_Network) -> None:
        self.log = uLogger("Slack API", debug_level=log_level)
        self.wifi = wifi
        self.event_api_base_url = "http://" + WEBSERVER_HOST + ":" + WEBSERVER_PORT + "/smib/event/"

    async def space_open(self) -> int:
        """Call space_open."""
        self.log.info(f"Calling slack API: space_open")
        self.space_open_url = self.event_api_base_url + "space_open"
        self.log.info(f"Calling URL: {self.space_open_url}")

        try:
            await self.wifi.check_network_access()
            request = await httpclient.request("PUT", self.space_open_url)
            self.log.info(f"request: {request}")
            response = await request.read()
            self.log.info(f"response data: {response}")
            return 0
        except Exception as e:
            self.log.error(f"Failed to call slack API: space_open. Exception: {e}")
            return -1        
    
    async def space_closed(self) -> int:
        """Call space_open."""
        self.log.info(f"Calling slack API: space_closed")
        self.space_closed_url = self.event_api_base_url + "space_closed"
        self.log.info(f"Calling URL: {self.space_closed_url}")

        try:
            await self.wifi.check_network_access()
            request = await httpclient.request("PUT", self.space_closed_url)
            self.log.info(f"request: {request}")
            response = await request.read()
            self.log.info(f"response data: {response}")
            return 0
        except Exception as e:
            self.log.error(f"Failed to call slack API: space_closed. Exception: {e}")
            return -1