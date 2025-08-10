from utime import ticks_ms, gmtime, time
from math import ceil
import rp2
import network
from ubinascii import hexlify
import config
from lib.ulogging import uLogger
from lib.utils import StatusLED
from asyncio import sleep, create_task
from lib.error_handling import ErrorHandler
from machine import RTC
from socket import getaddrinfo, socket, AF_INET, SOCK_DGRAM
import struct

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
        self.ntp_last_synced_timestamp = 0

        self.configure_wifi()
        self.configure_error_handling()

    def configure_wifi(self) -> None:
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.config(pm=self.disable_power_management)
        self.mac = self.get_mac_address()
        self.mac_no_colons = self.mac.replace(":", "")
        self.log.info("MAC: " + self.mac)
        self.hostname = self.determine_hostname()
        network.hostname(self.hostname)

    def get_mac_address(self) -> str:
        """
        Get the MAC address of the wireless interface.
        Returns:
            str: The MAC address in the format 'xx:xx:xx:xx:xx:xx'.
        """
        mac = hexlify(self.wlan.config('mac'),':').decode()
        self.log.info(f"MAC address: {mac}")
        return mac

    def determine_hostname(self) -> str:
        """
        Generate and return a default hostname based on the MAC address if no
        custom hostname is provided.
        """
        if config.CUSTOM_HOSTNAME:
            hostname = config.CUSTOM_HOSTNAME
        else:
            hostname = "smibhid-" + self.mac_no_colons[-6:]
        self.log.info(f"Setting hostname to {hostname}")
        return hostname

    def startup(self) -> None:
        self.log.info("Starting wifi network monitor")
        create_task(self.network_monitor())

    def configure_error_handling(self) -> None:
        self.error_handler = ErrorHandler("Wifi")
        self.errors = {
            "CON": "Wifi connect",
            "AUTH": "Wifi authentication error"
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
            elif status == self.CYW43_LINK_BADAUTH:
                self.log.error("Bad authentication, check your SSID and password")
                raise ValueError(self.status_names[status])
            elif status == self.CYW43_LINK_FAIL or status == self.CYW43_LINK_NONET:
                self.log.error(f"Connection failed: {self.status_names[status]}")
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

    async def auth_error(self) -> None:
        self.log.info("Bad wifi credentials")
        if not self.error_handler.is_error_enabled("AUTH"):
            self.error_handler.enable_error("AUTH")
        await self.status_led.async_flash(2, 2)
    
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
        except ValueError as ve:
            self.log.error(f"Authentication failed connecting to SSID {self.wifi_ssid} (password: {self.wifi_password}): {ve}")
            await self.auth_error()
            raise ValueError(f"Authentication failed connecting to SSID {self.wifi_ssid} (password: {self.wifi_password}): {ve}")
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
        except ValueError as ve:
            self.log.error(f"Auth error: {ve}")
            raise ValueError(ve)
        except Exception as e:
            raise Exception(f"Failed to connect to network: {e}")

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
            except ValueError as ve:
                self.log.error(f"Auth error, will not retry, please check credentials in the config file : {ve}")
                raise ValueError(ve)
            except Exception as e:
                self.log.warn(f"Error connecting to wifi on attempt {retries + 1} of {config.WIFI_CONNECT_RETRIES + 1}: {e}")
                retries += 1
                await self.network_retry_backoff()

        if self.get_status() == 3:
            self.log.info("Connected to wireless network")
            if self.ntp_last_synced_timestamp == 0 or (time() - self.ntp_last_synced_timestamp) > config.NTP_SYNC_INTERVAL_SECONDS:
                self.log.info(f"Syncing RTC from NTP as it has not been synced in {config.NTP_SYNC_INTERVAL_SECONDS} seconds.")
                await self.async_sync_rtc_from_ntp()
            return True
        else:
            self.log.warn("Unable to connect to wireless network")
            return False
        
    async def network_monitor(self) -> None:
        while True:
            await self.check_network_access()
            await sleep(5)
    
    def get_mac(self) -> str:
        """
        Get the MAC address of the wireless interface as stored in the Wireless
        Network class - cheaper than calling the wlan config.
        """
        return self.mac
    
    def get_ip(self) -> str:
        return self.ip
    
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

    def get_hostname(self) -> str:
        return self.hostname
    
    async def async_get_timestamp_from_ntp(self) -> tuple:
        ntp_host = "pool.ntp.org"
        port = 123
        buf_size = 48
        ntp_request_id = 0x1b
        timestamp = (2000, 1, 1, 0, 0, 0, 0, 0)

        try:
            query = bytearray(buf_size)
            query[0] = ntp_request_id
            address = getaddrinfo(ntp_host, port)[0][-1]
            udp_socket = socket(AF_INET, SOCK_DGRAM)
            udp_socket.setblocking(False)
            
            socket.sendto(udp_socket, query, address)
   
            timeout_ms = 5000
            start_time = ticks_ms()
            while (ticks_ms() - start_time) < timeout_ms:
                try:
                    data, _ = udp_socket.recvfrom(buf_size)
                    udp_socket.close()
                    
                    local_epoch = 2208988800
                    timestamp = struct.unpack("!I", data[40:44])[0] - local_epoch
                    timestamp = gmtime(timestamp)
                    break
                except OSError:
                    await sleep(0.1)

        except Exception as e:
            self.log.error(f"Failed to get NTP time: {e}")

        return timestamp

    async def async_sync_rtc_from_ntp(self) -> tuple:
        try:
            timestamp = await self.async_get_timestamp_from_ntp()
            RTC().datetime((
                timestamp[0], timestamp[1], timestamp[2], timestamp[6], 
                timestamp[3], timestamp[4], timestamp[5], 0))
            self.ntp_last_synced_timestamp = time()
            self.log.info("RTC synced from NTP")
        except Exception as e:
            self.log.error(f"Failed to sync RTC from NTP: {e}")
        return timestamp
    
    def is_connected(self) -> bool:
        return self.get_status() == 3
