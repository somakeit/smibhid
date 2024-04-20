from utime import ticks_ms, sleep
from math import ceil
import rp2
import network
from ubinascii import hexlify
import config
from lib.ulogging import uLogger
from lib.utils import Status_LED
import uasyncio
from sys import exit
from display import Display

class Wireless_Network:

    def __init__(self, log_level: int, display: Display) -> None:
        self.logger = uLogger("WIFI", log_level)
        self.status_led = Status_LED(log_level)
        self.wifi_ssid = config.wifi_ssid
        self.wifi_password = config.wifi_password
        self.wifi_country = config.wifi_country
        rp2.country(self.wifi_country)
        self.disable_power_management = 0xa11140
        self.led_retry_backoff_frequency = 4
        self.display = display
        
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

    def configure_wifi(self) -> None:
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config(pm=self.disable_power_management)
        self.mac = hexlify(self.wlan.config('mac'),':').decode()
        self.logger.info("MAC: " + self.mac)

    def init_service(self) -> None:
        uasyncio.create_task(self.network_status_monitor())

    async def network_status_monitor(self) -> None:
        while True:
            status = self.dump_status()
            if status == 3:
                self.display.update_main_display_values({"wifi_status": "Connected"})
            elif status >= 0:
                self.display.update_main_display_values({"wifi_status": "Connecting"})
            else:
                self.display.update_main_display_values({"wifi_status": "Error"})
            await uasyncio.sleep(5)
    
    def dump_status(self):
        status = self.wlan.status()
        self.logger.info(f"active: {1 if self.wlan.active() else 0}, status: {status} ({self.status_names[status]})")
        return status
    
    async def wait_status(self, expected_status, *, timeout=config.wifi_connect_timeout_seconds, tick_sleep=0.5) -> bool:
        for unused in range(ceil(timeout / tick_sleep)):
            await uasyncio.sleep(tick_sleep)
            status = self.dump_status()
            if status == expected_status:
                return True
            if status < 0:
                raise Exception(self.status_names[status])
        return False
    
    async def disconnect_wifi_if_necessary(self) -> None:
        status = self.dump_status()
        if status >= self.CYW43_LINK_JOIN and status <= self.CYW43_LINK_UP:
            self.logger.info("Disconnecting...")
            self.wlan.disconnect()
            try:
                await self.wait_status(self.CYW43_LINK_DOWN)
            except Exception as x:
                raise Exception(f"Failed to disconnect: {x}")
        self.logger.info("Ready for connection!")
    
    def generate_connection_info(self, elapsed_ms) -> None:
        self.ip, self.subnet, self.gateway, self.dns = self.wlan.ifconfig()
        self.logger.info(f"IP: {self.ip}, Subnet: {self.subnet}, Gateway: {self.gateway}, DNS: {self.dns}")
        
        self.logger.info(f"Elapsed: {elapsed_ms}ms")
        if elapsed_ms > 5000:
            self.logger.warn(f"took {elapsed_ms} milliseconds to connect to wifi")

    async def connection_error(self) -> None:
        await self.status_led.flash(2, 2)

    async def connection_success(self) -> None:
        await self.status_led.flash(1, 2)

    async def attempt_ap_connect(self) -> None:
        self.logger.info(f"Connecting to SSID {self.wifi_ssid} (password: {self.wifi_password})...")
        await self.disconnect_wifi_if_necessary()
        self.wlan.connect(self.wifi_ssid, self.wifi_password)
        try:
            await self.wait_status(self.CYW43_LINK_UP)
        except Exception as x:
            await self.connection_error()
            raise Exception(f"Failed to connect to SSID {self.wifi_ssid} (password: {self.wifi_password}): {x}")
        await self.connection_success()
        self.logger.info("Connected successfully!")
    
    async def connect_wifi(self) -> None:
        self.logger.info("Connecting to wifi")
        start_ms = ticks_ms()
        try:
            await self.attempt_ap_connect()
        except Exception:
            raise Exception(f"Failed to connect to network")

        elapsed_ms = ticks_ms() - start_ms
        self.generate_connection_info(elapsed_ms)

    def get_status(self) -> int:
        return self.wlan.status()
    
    async def network_retry_backoff(self) -> None:
        self.logger.info(f"Backing off retry for {config.wifi_retry_backoff_seconds} seconds")
        await self.status_led.flash((config.wifi_retry_backoff_seconds * self.led_retry_backoff_frequency), self.led_retry_backoff_frequency)

    async def check_network_access(self) -> bool:
        self.logger.info("Checking for network access")
        retries = 0
        while self.get_status() != 3 and retries <= config.wifi_connect_retries:
            try:
                await self.connect_wifi()
                return True
            except Exception:
                self.logger.warn(f"Error connecting to wifi on attempt {retries + 1} of {config.wifi_connect_retries + 1}")
                retries += 1
                await self.network_retry_backoff()

        if self.get_status() == 3:
            self.logger.info("Connected to wireless network")
            return True
        else:
            self.logger.warn("Unable to connect to wireless network")
            return False
        
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
