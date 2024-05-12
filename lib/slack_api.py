from lib.ulogging import uLogger
import lib.uaiohttpclient as httpclient
from lib.networking import WirelessNetwork
from config import WEBSERVER_HOST, WEBSERVER_PORT
import gc
from json import loads

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, log_level: int, wifi: WirelessNetwork) -> None:
        self.log = uLogger("Slack API", debug_level=log_level)
        self.wifi = wifi
        self.event_api_base_url = "http://" + WEBSERVER_HOST + ":" + WEBSERVER_PORT + "/smib/event/"

    async def async_space_open(self) -> None:
        """Call space_open."""
        await self._async_slack_api_request("PUT", "space_open")
    
    async def async_space_closed(self) -> None:
        """Call space_closed."""
        await self._async_slack_api_request("PUT", "space_closed")
    
    async def async_get_space_state(self) -> bool | None:
        """Call space_state and return boolean: True = Open, False = closed."""
        response = await self._async_slack_api_request("GET", "space_state")
        self.log.info(f"Request result: {response}")
        try:
            state = response['open']
            if state not in [True, False, None]:
                raise ValueError(f"Space state set to illegal value: {state}")
        except Exception as e:
            self.log.error(f"Unable to load space state from response data: {e}")
            raise
        return state
        
    async def _async_slack_api_request(self, method: str, url_suffix: str) -> dict:
        """
        Make a request to the S.M.I.B. SLACK API, provide the URL suffix to event api url, e.g. 'space_open'.
        Returns the response payload as a string
        """
        self.log.info(f"Calling slack API: {url_suffix}")
        url = self.event_api_base_url + url_suffix
        result = await self._async_api_request(method, url)
        return result
    
    async def _async_api_request(self, method: str, url: str) -> dict:
        """Internal method to make a PUT or GET request to an API, provide the HTTP method and the full API URL"""
        if method in ["GET", "PUT"]:
            response = await self._async_api_make_request(method, url)
            return response
        else:
            raise ValueError(f"{method} is not 'GET' or 'PULL'.")

    async def _async_api_make_request(self, method: str, url: str) -> dict:
        """
        Internal method for making an API request, provide the method and full URL.
        Returns the response data as a dict, throws an exception if the return status code is not 200.
        """
        gc.collect()

        self.log.info(f"Calling URL: {url}, with method: {method}")

        try:
            await self.wifi.check_network_access()
            request = await httpclient.request(method, url)
            self.log.info(f"Request: {request}")
            response = await request.read()
            self.log.info(f"Response data: {response}")
            data = {}
            if response:
                data = loads(response)
                self.log.info(f"JSON data: {data}")
            
            if request.status == 200:
                self.log.info("Request processed sucessfully by SMIB API")
                return data
            else:
                raise ValueError(f"HTTP status code was not 200. Status code: {request.status}, HTTP response: {response}")
        except Exception as e:
            self.log.error(f"Failed to call slack API: {url}. Exception: {e}")
            raise
        finally:
            gc.collect()