from lib.ulogging import uLogger
import lib.uaiohttpclient as httpclient
from lib.networking import WirelessNetwork
from config import WEBSERVER_HOST, WEBSERVER_PORT
import gc

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, log_level: int, wifi: WirelessNetwork) -> None:
        self.log = uLogger("Slack API", debug_level=log_level)
        self.wifi = wifi
        self.event_api_base_url = "http://" + WEBSERVER_HOST + ":" + WEBSERVER_PORT + "/smib/event/"

    async def space_open(self) -> int:
        """Call space_open."""
        self.log.info("Calling slack API: space_open")
        url = self.event_api_base_url + "space_open"
        result = await self.async_slack_api_request(url)
        return result
    
    async def space_closed(self) -> int:
        """Call space_open."""
        self.log.info("Calling slack API: space_closed")
        url = self.event_api_base_url + "space_closed"
        result = await self.async_slack_api_request(url)
        return result
        
    async def async_slack_api_request(self, url) -> int:
        gc.collect()

        self.log.info(f"Calling URL: {url}")

        try:
            await self.wifi.check_network_access()
            request = await httpclient.request("PUT", url)
            self.log.info(f"request: {request}")
            response = await request.read()
            self.log.info(f"response data: {response}")
            
            if request.status == 200:
                self.log.info("Request processed sucessfully by SMIB API")
                return 0
            else:
                self.log.info(f"Request to SMIB API encountered errors: {request.status} - {response}")
                return -1
        except Exception as e:
            self.log.error(f"Failed to call slack API: {url}. Exception: {e}")
            return -1
        finally:
            gc.collect()