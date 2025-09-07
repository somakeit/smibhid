from asyncio import create_task, sleep, run
from machine import I2C
from config import SENSOR_MODULES, SENSOR_LOGGING_ENABLED, SENSOR_LOG_CACHE_ENABLED, CO2_ALARM_THRESHOLD_PPM
from lib.ulogging import uLogger
from lib.sensors.SGP30 import SGP30
from lib.sensors.BME280 import BME280
from lib.sensors.SCD30 import SCD30
from lib.sensors.sensor_module import SensorModule
from lib.sensors.file_logging import FileLogger
from lib.sensors.alarm import Alarm
from lib.displays.display import Display
from lib.networking import WirelessNetwork
from lib.space_state import SpaceState
from lib.slack_api import Wrapper
from json import dumps
from time import time, localtime

class Sensors:
    def __init__(self, i2c: I2C, display: Display, wifi: WirelessNetwork, space_state: SpaceState) -> None:
        self.log = uLogger("Sensors")
        self.i2c = i2c
        self.display = display
        self.wifi = wifi
        self.api_wrapper = Wrapper(self.wifi)
        self.space_state = space_state
        self.SENSOR_SCREEN = "SSD1306"
        self.SENSOR_MODULES = SENSOR_MODULES
        self.available_modules: dict = {}
        self.configured_modules: dict = {}
        self.file_logger = FileLogger(init_files=True)
        modules = ["SGP30", "BME280", "SCD30"]
        self.load_modules(modules)
        self._configure_modules()
        self.alarm = Alarm(self.display, self.space_state)
        if CO2_ALARM_THRESHOLD_PPM > 0 and 'SCD30' in self.configured_modules:
            self.alarm.enable()
            self.log.info("SCD30 present and CO2_ALARM_THRESHOLD_PPM > 0, CO2 alarm enabled")

    def load_modules(self, modules: list[str]) -> None:
        """
        Load a list of sensor modules by name passed as a list of strings.
        """
        for module in modules:
            try:
                self.log.info(f"Loading {module} sensor module")
                module_class = globals().get(module)
                if module_class is None:
                    raise ValueError(f"Sensor module '{module}' not imported.")
                self.available_modules[module] = module_class(self.i2c)
                self.log.info(f"Loaded {module} sensor module")

            except RuntimeError as e:
                self.log.error(f"Failed to load {module} sensor module: {e}")

            except Exception as e:
                self.log.error(f"Failed to load {module} sensor module: {e}")
    
    def _configure_modules(self) -> None:
        """
        Configure sensor modules by checking if they are available and logging their status.
        """
        self.log.info(f"Attempting to locate drivers for: {self.SENSOR_MODULES}")

        for sensor_module in self.SENSOR_MODULES:
            if sensor_module in self.available_modules:
                self.log.info(f"Found driver for {sensor_module}")
                self.configured_modules[sensor_module] = self.available_modules[sensor_module]
                self.log.info(f"Configured {sensor_module} sensor module")
                self.log.info(f"Available sensors: {self.get_sensors(sensor_module)}")
            else:
                self.log.error(f"Driver not found for {sensor_module}")

        self.log.info(f"Configured modules: {self.get_modules()}")

    def startup(self) -> None:
        """
        Perform startup tasks for the sensors, including clearing the display and starting sensor polling.
        """
        screen_set = self.display.set_screen_for_next_command(self.SENSOR_SCREEN)
        if screen_set:
            self.log.info("Sensor screen cleared")
            self.display.clear()
        
        self.display.update_co2("Unknown")
        self.display.update_alarm("Clear")

        if self.alarm.enabled:
            run(self.alarm.async_test_co2_alarm())

        if SENSOR_LOGGING_ENABLED:
            self.log.info(f"Starting sensors: {self.configured_modules}")
            create_task(self._poll_sensors())
            self.log.info("Sensor polling started")
        else:
            self.log.info("Sensor log cache disabled, skipping sensor startup")
    
    async def async_push_sensor_readings_payload(self, payload: dict) -> dict:
        """
        Asynchronously push sensor readings to the slack web API server
        """
        self.log.info("Making async push of sensor readings to SMIB API")

        result = {}

        try:
            if payload:
                result = await self.api_wrapper.async_slack_api_request("POST", "smibhid/log/sensor", dumps(payload))
                self.log.info(f"Pushed sensor readings: {payload}, result: {result}")
            else:
                self.log.warn("No sensor readings to push")
        except Exception as e:
            self.log.error(f"Error pushing sensor readings: {e}")
            raise
        
        return result
    
    def generate_timestamped_readings(self, readings: dict) -> dict:
        """
        Generate a timestamped reading dictionary from reading data with unix timestamp and human readable time tuple.
        """
        timestamped_readings = {
                    "timestamp": time(),
                    "human_timestamp": self.file_logger.localtime_to_iso8601(localtime()),
                    "data": readings
                }
        return timestamped_readings

    def update_display_and_log_cache(self, readings: dict) -> None:
        """
        Update the display with sensor readings and log them to cache if caching enabled.
        """
        if readings.get("SCD30"):
                self.display.update_co2(readings["SCD30"]["co2"])
                
        if SENSOR_LOG_CACHE_ENABLED:
            self.file_logger.log_minute_entry(readings)
    
    def create_unit_encapsulated_readings_payload(self, readings_list: list) -> dict:
        """
        Return a dictionary with the readings_list encapsulated in a 'readings' key and a 'unit' key
        containing the corresponding reading units.
        """
        self.log.info("Creating payload for sensor readings")
        units = {}
        modules = self.get_modules()
        self.log.info(f"Configured modules: {modules}")
        for module in modules:
            units[module] = {}
            sensors = self.get_sensors(module)
            for sensor in sensors:
                self.log.info(f"Adding sensor {sensor['name']} with unit {sensor['unit']}")
                units[module][sensor["name"]] = sensor["unit"]

        payload = {
            "units": units,
            "readings": readings_list            
        }

        self.log.info(f"Created payload for sensor readings: {payload}")
        
        return payload
    
    async def async_push_all_readings(self, readings_list: list) -> None:
        """
        Asynchronously push all sensor readings to the API, including any cached readings.
        Cache any failed pushes to the file cache for later retry.
        """
        failed_push_list = []
        payload = self.create_unit_encapsulated_readings_payload(readings_list)
        try:
            self.log.info(f"Pushing sensor readings: {payload}")
            await self.async_push_sensor_readings_payload(payload)
            self.log.info("Sensor readings pushed successfully.")

        except Exception as e:
            self.log.error(f"Error pushing sensor reading: {e}")
            failed_push_list.extend(readings_list)

        if self.file_logger.check_for_smib_cache():
            self.file_logger.delete_smib_cache()

        if failed_push_list:
            self.log.error(f"Failed to push sensor readings: {failed_push_list}")
            self.file_logger.write_smib_cache_list(failed_push_list)
        else:
            self.log.info("All sensor readings pushed successfully")
    
    def collect_cached_readings(self, readings_list: list) -> list:
        """
        Check for previous failed readings in cache and append them to the readings list.
        """
        if self.file_logger.check_for_smib_cache():
            self.log.info("SMIB cache file found, reading cached sensor readings")
            cached_readings = self.file_logger.read_smib_cache_list()
            readings_list.extend(cached_readings)
            self.log.info(f"Readings from cache: {cached_readings}")
            self.log.info(f"Total readings to push: {len(readings_list)}")
            
        else:
            self.log.info("No cached readings found, pushing current readings only")

        return readings_list
    
    async def async_gather_and_push_all_readings(self, readings: dict) -> None:
        """
        Gather all previously cached sensor readings that failed to push,
        append a timestamp to the current readings and add to the cached
        readings to push them to the API. Create a new cache for any failed
        pushes.
        """
        readings_list = []
        readings_list.append(self.generate_timestamped_readings(readings))
        readings_list = self.collect_cached_readings(readings_list)
        await self.async_push_all_readings(readings_list)

        return

    async def _poll_sensors(self) -> None:
        """
        Asynchronously poll sensors and log readings every 60 seconds.
        """
        self.log.info("Starting sensor polling")
        
        while True:
            readings = self.get_readings()
            self.log.info(f"Sensor readings: {readings}")
            
            if len(readings) > 0:
                if self.alarm.enabled:
                    self.alarm.assess_co2_alarm(readings)

                self.update_display_and_log_cache(readings)
                await self.async_gather_and_push_all_readings(readings)
            
            else:
                self.log.error("No sensor readings available")
            
            await sleep(60)
    
    def get_modules(self) -> list:
        """
        Return a dictionary of configured sensor modules.
        """
        return list(self.configured_modules.keys())

    def get_sensors(self, module: str) -> list:
        """
        Return list of sensors for a specific module name.
        """
        module_object = self.configured_modules[module]
        sensors = module_object.get_sensors()
        self.log.info(f"Available sensors for {module}: {sensors}")
        return sensors

    def clean_readings(self, readings: dict) -> dict:
        """
        Remove None values from sensor readings and empty modules.
        
        Args:
            readings: Raw sensor readings dictionary
            
        Returns:
            Cleaned readings dictionary with None values and empty modules removed
        """
        self.log.info("Cleaning sensor readings of None values")
        self.log.info(f"Raw sensor readings: {readings}")
        
        cleaned_readings = {}
        for reading in readings:
            cleaned_module_data = {}
            for module in readings[reading]:
                if readings[reading][module] is not None:
                    cleaned_module_data[module] = readings[reading][module]
                else:
                    self.log.warn(f"Sensor {reading} from module {module} returned None, removing from reading data")

            if cleaned_module_data:
                cleaned_readings[reading] = cleaned_module_data
            else:
                self.log.warn(f"Module {reading} has no valid readings, removing entire module from reading data")
        
        self.log.info(f"Cleaned sensor readings: {cleaned_readings}")
        return cleaned_readings

    def get_readings(self, module: str = "") -> dict:
        """
        Return readings from a specific module by passing it's name as a
        string, or all modules if none specified.
        Remove any readings that return None to avoid logging invalid data.
        """
        readings = {}
        if module:
            readings[module] = self.configured_modules[module].get_reading()
        else:
            for name, instance in self.configured_modules.items():
                readings[name] = instance.get_reading()

        return self.clean_readings(readings)
