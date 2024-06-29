from utime import ticks_ms
from math import ceil
import rp2
import network
from ubinascii import hexlify
import config
from lib.ulogging import uLogger
from lib.utils import StatusLED
from asyncio import sleep
from error_handling import ErrorHandler

class WirelessNetwork:

    def __init__(self) -> None:
        self.log = uLogger("WIFI")
        self.status_led = StatusLED()
        self.wifi_ssid = config.WIFI_SSID
        self.wifi_password = config.WIFI_PASSWORD
        self.wifi_country = config.WIFI_COUNTRY
        rp2.country(self.wifi_country)
        self.disable_power_management = 0xa11140
        self.led_retry_backoff_frequency = 4
        
        # Reference: https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
        self.CYW43_LINK_DOWN = 0
        self.CYW43_LINK_JOIN = 1
        self.CYW43_LINK_NOIP = 2
        self.CYW43_LINK_UP = 3
        self.CYW43_LINK_FAIL = -1
        self.CYW43_LINK_NONET = -2
        self.CYW43_LINK_BADAUTH = -3
        self.status_names = {
        self.CYW43_LINK_DOWN: "Link is down",
        self.CYW43_LINK_JOIN: "Connected to wifi",
        self.CYW43_LINK_NOIP: "Connected to wifi, but no IP address",
        self.CYW43_LINK_UP: "Connect to wifi with an IP address",
        self.CYW43_LINK_FAIL: "Connection failed",
        self.CYW43_LINK_NONET: "No matching SSID found (could be out of range, or down)",
        self.CYW43_LINK_BADAUTH: "Authenticatation failure",
        }
        self.ip = "Unknown"
        self.subnet = "Unknown"
        self.gateway = "Unknown"
        self.dns = "Unknown"

        self.configure_wifi()
        self.configure_error_handling()

    def configure_wifi(self) -> None:
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config(pm=self.disable_power_management)
        self.mac = hexlify(self.wlan.config('mac'),':').decode()
        self.log.info("MAC: " + self.mac)

    def configure_error_handling(self) -> None:
        self.error_handler = ErrorHandler("Wifi")
        self.errors = {
            "CON": "Wifi connect"
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)

    def dump_status(self):
        status = self.wlan.status()
        self.log.info(f"active: {1 if self.wlan.active() else 0}, status: {status} ({self.status_names[status]})")
        return status
    
    async def wait_status(self, expected_status, *, timeout=config.WIFI_CONNECT_TIMEOUT_SECONDS, tick_sleep=0.5) -> bool:
        for unused in range(ceil(timeout / tick_sleep)):
            await sleep(tick_sleep)
            status = self.dump_status()
            if status == expected_status:
                return True
            if status < 0:
                raise Exception(self.status_names[status])
        return False
    
    async def disconnect_wifi_if_necessary(self) -> None:
        status = self.dump_status()
        if status >= self.CYW43_LINK_JOIN and status <= self.CYW43_LINK_UP:
            self.log.info("Disconnecting...")
            self.wlan.disconnect()
            try:
                await self.wait_status(self.CYW43_LINK_DOWN)
            except Exception as x:
                raise Exception(f"Failed to disconnect: {x}")
        self.log.info("Ready for connection!")
    
    def generate_connection_info(self, elapsed_ms) -> None:
        self.ip, self.subnet, self.gateway, self.dns = self.wlan.ifconfig()
        self.log.info(f"IP: {self.ip}, Subnet: {self.subnet}, Gateway: {self.gateway}, DNS: {self.dns}")
        
        self.log.info(f"Elapsed: {elapsed_ms}ms")
        if elapsed_ms > 5000:
            self.log.warn(f"took {elapsed_ms} milliseconds to connect to wifi")

    async def connection_error(self) -> None:
        self.log.info("Error connecting")
        if not self.error_handler.is_error_enabled("CON"):
            self.error_handler.enable_error("CON")
        await self.status_led.async_flash(2, 2)

    async def connection_success(self) -> None:
        self.log.info("Successful connection")
        if self.error_handler.is_error_enabled("CON"):
            self.error_handler.disable_error("CON")
        await self.status_led.async_flash(1, 2)

    async def attempt_ap_connect(self) -> None:
        self.log.info(f"Connecting to SSID {self.wifi_ssid} (password: {self.wifi_password})...")
        await self.disconnect_wifi_if_necessary()
        self.wlan.connect(self.wifi_ssid, self.wifi_password)
        try:
            await self.wait_status(self.CYW43_LINK_UP)
        except Exception as x:
            await self.connection_error()
            raise Exception(f"Failed to connect to SSID {self.wifi_ssid} (password: {self.wifi_password}): {x}")
        await self.connection_success()
        self.log.info("Connected successfully!")
    
    async def connect_wifi(self) -> None:
        self.log.info("Connecting to wifi")
        start_ms = ticks_ms()
        try:
            await self.attempt_ap_connect()
        except Exception:
            raise Exception("Failed to connect to network")

        elapsed_ms = ticks_ms() - start_ms
        self.generate_connection_info(elapsed_ms)

    def get_status(self) -> int:
        return self.wlan.status()
    
    async def network_retry_backoff(self) -> None:
        self.log.info(f"Backing off retry for {config.WIFI_RETRY_BACKOFF_SECONDS} seconds")
        await self.status_led.async_flash((config.WIFI_RETRY_BACKOFF_SECONDS * self.led_retry_backoff_frequency), self.led_retry_backoff_frequency)

    async def check_network_access(self) -> bool:
        self.log.info("Checking for network access")
        retries = 0
        while self.get_status() != 3 and retries <= config.WIFI_CONNECT_RETRIES:
            try:
                await self.connect_wifi()
                return True
            except Exception:
                self.log.warn(f"Error connecting to wifi on attempt {retries + 1} of {config.WIFI_CONNECT_RETRIES + 1}")
                retries += 1
                await self.network_retry_backoff()

        if self.get_status() == 3:
            self.log.info("Connected to wireless network")
            return True
        else:
            self.log.warn("Unable to connect to wireless network")
            return False
        
    async def network_monitor(self) -> None:
        while True:
            await self.check_network_access()
            await sleep(5)
    
    def get_mac(self) -> str:
        return self.mac
    
    def get_wlan_status_description(self, status) -> str:
        description = self.status_names[status]
        return description
    
    def get_all_data(self) -> dict:
        all_data = {}
        all_data['mac'] = self.get_mac()
        status = self.get_status()
        all_data['status description'] = self.get_wlan_status_description(status)
        all_data['status code'] = status
        return all_data
