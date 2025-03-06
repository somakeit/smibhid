from asyncio import create_task, sleep
from machine import I2C
from config import SENSORS, SDA_PIN, SCL_PIN, I2C_ID
from lib.ulogging import uLogger
from lib.sensors.SGP30 import SGP30

class Sensors:
    def __init__(self):
        self.log = uLogger("Sensors")
        self.i2c = I2C(I2C_ID, sda = SDA_PIN, scl = SCL_PIN, freq = 400000) # TODO: load from HID for here and display
        self.SENSORS = SENSORS
        self.available_sensors = {}
        self.available_sensors["SGP30"] = SGP30(self.i2c)
        self.configured_sensors = {}
        self._load_sensors()   

    def _load_sensors(self):
        self.log.info(f"Attempting to locate drivers for: {self.SENSORS}")
        for sensor in self.SENSORS:
            if sensor in self.available_sensors:
                self.log.info(f"Found driver for {sensor}")
                self.configured_sensors[sensor] = self.available_sensors[sensor]
            else:
                self.log.error(f"Driver not found for {sensor}")

    def startup(self):
        self.log.info(f"Starting sensors: {self.configured_sensors}")
        create_task(self._poll_sensors())

    async def _poll_sensors(self):
        while True:
            readings = self.get_readings()
            for reading in readings:
                self.log.info(f"Sensor: {reading}: {readings[reading]}")
            await sleep(5)
    
    def get_readings(self):
        readings = {}
        for name, instance in self.configured_sensors.items():
            readings[name] = instance.get_reading()
        return readings
