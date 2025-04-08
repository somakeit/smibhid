from asyncio import create_task, sleep
from machine import I2C, Pin
from config import SENSOR_MODULES, SENSOR_LOG_CACHE_ENABLED, CO2_ALARM_THRESHOLD_PPM, CO2_ALARM_RESET_THRESHOLD_PPM, CO2_ALARM_SNOOZE_DURATION_S, CO2_ALARM_LED_PIN, CO2_ALARM_BUZZER_PIN, CO2_ALARM_SNOOZE_BUTTON_PIN
from lib.ulogging import uLogger
from lib.sensors.SGP30 import SGP30
from lib.sensors.BME280 import BME280
from lib.sensors.SCD30 import SCD30
from lib.sensors.sensor_module import SensorModule
from lib.sensors.file_logging import FileLogger
from lib.button import Button
from asyncio import Event, create_task
from time import time

class Sensors:
    def __init__(self, i2c: I2C) -> None:
        self.log = uLogger("Sensors")
        self.i2c = i2c
        self.SENSOR_MODULES = SENSOR_MODULES
        self.available_modules: dict[str, SensorModule] = {}
        self.configured_modules: dict[str, SensorModule] = {}
        self.file_logger = FileLogger(init_files=True)
        modules = ["SGP30", "BME280", "SCD30"]
        if CO2_ALARM_THRESHOLD_PPM > 0:
            self.configure_co2_alarm()
        self.load_modules(modules)
        self._configure_modules() 

    def configure_co2_alarm(self) -> None:
        """
        Configure the CO2 alarm state and set the GPIO pins for the alarm components."""
        self.co2_alarm_buzzer = Pin(CO2_ALARM_BUZZER_PIN, Pin.OUT)
        self.co2_alarm_buzzer.off()
        self.co2_alarm_led = Pin(CO2_ALARM_LED_PIN, Pin.OUT)
        self.co2_alarm_led.off()
        self.co2_alarm_snooze_event = Event()
        self.co2_alarm_snooze_button = Button(CO2_ALARM_SNOOZE_BUTTON_PIN, "CO2 alarm snooze", self.co2_alarm_snooze_event)
        self.co2_alarm_buzzer_snooze_set_time = None
        create_task(self.co2_alarm_snooze_button.wait_for_press())
    
    async def async_co2_alarm_button_press_watcher(self) -> None:
        """
        Asynchronously wait for the CO2 alarm snooze button press event.
        """
        while True:
            await self.co2_alarm_snooze_event.wait()
            self.co2_alarm_snooze_event.clear()
            self.snooze_co2_alarm()            
    
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
        if SENSOR_LOG_CACHE_ENABLED:
            self.log.info(f"Starting sensors: {self.configured_modules}")
            create_task(self._poll_sensors())
            self.log.info("Sensor polling started")
        else:
            self.log.info("Sensor log cache disabled, skipping sensor startup")

    async def _poll_sensors(self) -> None:
        """
        Asynchronously poll sensors and log readings every 60 seconds.
        """
        while True:
            readings = self.get_readings()
            self.log.info(f"Sensor readings: {readings}")
            
            if len(readings) > 0:
                self.file_logger.log_minute_entry(readings)
                self.assess_co2_alarm(readings)
            
            else:
                self.log.error("No sensor readings available")
            
            await sleep(60)
    
    def assess_co2_alarm(self, readings: dict) -> None:
        """
        Assess the CO2 alarm state based on readings from the SCD30 sensor.
        """
        if "SCD30" in readings:
            co2_ppm = readings["SCD30"]["CO2"]
            if co2_ppm >= CO2_ALARM_THRESHOLD_PPM:
                self.log.info(f"CO2 of {co2_ppm} ppm above alarm threshold of ({CO2_ALARM_THRESHOLD_PPM} ppm), setting alarm")
                self.set_co2_alarm()
                
            elif co2_ppm <= CO2_ALARM_RESET_THRESHOLD_PPM:
                self.log.info(f"CO2 of {co2_ppm} ppm below alarm reset threshold of ({CO2_ALARM_RESET_THRESHOLD_PPM} ppm), resetting alarm")
                self.unset_co2_alarm()
    
    def set_co2_alarm(self) -> None:
        """
        Set the CO2 alarm state.
        """
        self.log.info("Setting CO2 alarm state")
        self.co2_alarm_led.on()
        self.set_co2_alarm_buzzer()

    def unset_co2_alarm(self) -> None:
        """
        Unset the CO2 alarm state.
        """
        self.log.info("Unsetting CO2 alarm state")
        self.co2_alarm_led.off()
        self.co2_alarm_buzzer.off()

    def snooze_co2_alarm(self) -> None:
        """
        Snooze the CO2 alarm for a specified duration.
        """
        self.log.info("Snoozing CO2 alarm")
        self.co2_alarm_buzzer.off()
        self.co2_alarm_snooze_set_time = time()    

    def set_co2_alarm_buzzer(self) -> None:
        """
        Set the CO2 alarm buzzer state.
        """
        self.log.info("Setting CO2 alarm buzzer state")
        if self.co2_alarm_buzzer_snooze_set_time is None:
            self.co2_alarm_buzzer.on()
        else:
            if time() - self.co2_alarm_buzzer_snooze_set_time >= CO2_ALARM_SNOOZE_DURATION_S:
                self.co2_alarm_buzzer.on()
                self.co2_alarm_snooze_set_time = None
            else:
                self.log.info("CO2 alarm buzzer snoozed, not setting buzzer")
    
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

    def get_readings(self, module: str = "") -> dict:
        """
        Return readings from a specific module by passing it's name as a
        string, or all modules if none specified.
        """
        readings = {}
        if module:
            readings[module] = self.configured_modules[module].get_reading()
        else:
            for name, instance in self.configured_modules.items():
                readings[name] = instance.get_reading()
        return readings
