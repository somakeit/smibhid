from lib.ulogging import uLogger
import lib.uaiohttpclient as httpclient
from lib.networking import WirelessNetwork
from config import WEBSERVER_HOST, WEBSERVER_PORT
import gc
from json import loads, dumps

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, network: WirelessNetwork) -> None:
        self.log = uLogger("Slack API")
        self.wifi = network
        self.event_api_base_url = "http://" + WEBSERVER_HOST + ":" + WEBSERVER_PORT + "/api/"

    async def async_space_open(self, hours: int = 0) -> None:
        """Call space_open, with optional hours open for parameter."""
        json_hours = dumps({"hours" : hours})
        await self.async_slack_api_request("PUT", "space/state/open", json_hours)
    
    async def async_space_closed(self) -> None:
        """Call space_closed."""
        await self.async_slack_api_request("PUT", "space/state/closed")
    
    async def async_get_space_state(self) -> bool | None:
        """Call space_state and return boolean: True = Open, False = closed."""
        response = await self.async_slack_api_request("GET", "space/state")
        self.log.info(f"Request result: {response}")
        try:
            state = response['open']
            if state not in [True, False, None]:
                raise ValueError(f"Space state set to illegal value: {state}")
        except Exception as e:
            self.log.error(f"Unable to load space state from response data: {e}")
            raise
        return state
    
    async def async_upload_ui_log(self, log: list) -> None:
        """Upload the UI log to the server."""
        json_log = dumps(log)
        await self.async_slack_api_request("POST", "smibhid/log/ui", json_log)

    async def async_slack_api_request(self, method: str, url_suffix: str, json_data: str = "") -> dict:
        """
        Make a request to the S.M.I.B. SLACK API, provide the URL suffix to event api url, e.g. 'space_open'.
        Returns the response data as a dict, throws an exception if the return status code is not 200.
        """
        self.log.info(f"Calling slack API: {url_suffix} with method: {method} and data: {json_data}")
        url = self.event_api_base_url + url_suffix
        result = await self._async_api_request(method, url, json_data)
        return result
    
    async def _async_api_request(self, method: str, url: str, json_data: str = "") -> dict:
        """
        Internal method to make a PUT or GET request to an API, provide the HTTP method and the full API URL
        Returns the response data as a dict, throws an exception if the return status code is not 200.
        """
        if method in ["GET", "PUT", "POST"]:
            response = await self._async_api_make_request(method, url, json_data)
            return response
        else:
            raise ValueError(f"{method} is not 'GET' 'PUT' or 'POST'.")

    async def _async_api_make_request(self, method: str, url: str, json_data: str = "") -> dict:
        """
        Internal method for making an API request, provide the method and full URL.
        Returns the response data as a dict, throws an exception if the return status code is not 200.
        """
        gc.collect()

        self.log.info(f"Calling URL: {url}, with method: {method}")

        try:
            await self.wifi.check_network_access()
            hostname = self.wifi.get_hostname()
            headers = {
                "Content-Type": "application/json",
                "x-smibhid-hostname": hostname,
                "Content-Length" : str(len(json_data))
            }
            request = await httpclient.request(method, url, headers=headers, json_data=json_data)
            self.log.info(f"Request: {request}")
            response = await request.read()
            self.log.info(f"Response data: {response}")
            data = {}
            if response:
                data = loads(response)
                self.log.info(f"JSON data: {data}")

            if request.status >= 200 and request.status < 300:
                self.log.info("Request processed successfully by SMIB API")
                return data
            else:
                raise ValueError(f"HTTP status code was not 200. Status code: {request.status}, HTTP response: {response}")
        except Exception as e:
            self.log.error(f"Failed to call slack API: {url}. Exception: {e}")
            raise
        finally:
            gc.collect()
