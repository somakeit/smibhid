from lib.ulogging import uLogger
import lib.uaiohttpclient as httpclient
from lib.networking import WirelessNetwork
from lib.utils import DateTimeUtils
from lib.error_handling import ErrorHandler
from config import WEBSERVER_HOST, WEBSERVER_PORT
import gc
from json import loads, dumps
from time import time
from asyncio import create_task

class Wrapper:
    """
    API wrapper for the REST API accepting comands to pass to the local slack server socket.
    """
    def __init__(self, network: WirelessNetwork) -> None:
        self.log = uLogger("Slack API")
        self.wifi = network
        self.datetime_utils = DateTimeUtils()
        self.event_api_base_url = "http://" + WEBSERVER_HOST + ":" + WEBSERVER_PORT + "/api/"

    def fire_and_forget_async_task(self, coro, error_handler: ErrorHandler | None = None, error_key: str | None = None, success_message: str = "Push to SMIB succeeded") -> None:
        """
        Schedule a coroutine as a task without awaiting it, catching any
        exception it raises and optionally reflecting it via an ErrorHandler key.
        """
        try:
            create_task(self._async_fire_and_forget_task(coro, error_handler, error_key, success_message))
        except Exception as e:
            self.log.error(f"Failed to schedule fire and forget task: {e}")
            if error_handler is not None and error_key is not None and not error_handler.is_error_enabled(error_key):
                error_handler.enable_error(error_key)

    async def _async_fire_and_forget_task(self, coro, error_handler: ErrorHandler | None, error_key: str | None, success_message: str) -> None:
        try:
            await coro
            self.log.info(success_message)
            if error_handler is not None and error_key is not None and error_handler.is_error_enabled(error_key):
                error_handler.disable_error(error_key)
        except Exception as e:
            self.log.error(f"Fire and forget task failed: {e}")
            if error_handler is not None and error_key is not None and not error_handler.is_error_enabled(error_key):
                error_handler.enable_error(error_key)

    async def async_space_open(self, hours: int = 0) -> None:
        """Call space_open, with optional hours open for parameter."""
        json_hours = dumps({"hours" : hours})
        await self.async_slack_api_request("PUT", "space/state/open", json_hours)
    
    async def async_space_closed(self, minutes: int = 0) -> None:
        """Call space_closed."""
        json_minutes = dumps({"minutes": minutes})
        await self.async_slack_api_request("PUT", "space/state/closed", json_minutes)

    async def async_space_light_update(self, light_state: bool | None, light_value: float | None, threshold: float | None) -> None:
        """Push space light state update to SMIB.
        
        Args:
            light_state: True if light level is above threshold (space "open"), 
                        False if below threshold (space "closed"), 
                        None if not configured/unavailable
            light_value: The light level reading in lux
            threshold: The configured threshold value in lux
        """
        payload = {
            "light_state": light_state,
            "light_value_lux": light_value,
            "threshold_lux": threshold
        }
        json_payload = dumps(payload)
        await self.async_slack_api_request("PUT", "space/light/state", json_payload)

    async def async_relay_state_update(self, active: bool, total_active_seconds: float) -> None:
        """Push a relay state transition to SMIB.

        Args:
            active: True if the relay is now active, False if now inactive
            total_active_seconds: SMIBHID's current running total relay active time
        """
        payload = {
            "active": active,
            "timestamp": self.datetime_utils.timestamp_to_iso8601(time()),
            "total_active_seconds": total_active_seconds
        }
        json_payload = dumps(payload)
        await self.async_slack_api_request("POST", "space/relay/state", json_payload)

    async def async_relay_reset(self, previous_total_active_seconds: float) -> None:
        """Notify SMIB that the local relay on-time counter has been reset.

        Args:
            previous_total_active_seconds: The running total that was reset to zero
        """
        payload = {
            "timestamp": self.datetime_utils.timestamp_to_iso8601(time()),
            "previous_total_active_seconds": previous_total_active_seconds
        }
        json_payload = dumps(payload)
        await self.async_slack_api_request("POST", "space/relay/reset", json_payload)

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

        request = None
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
            if request is not None:
                await request.aclose()
            gc.collect()
