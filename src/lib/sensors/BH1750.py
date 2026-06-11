"""
BH1750 Digital Ambient Light Sensor Driver for MicroPython

Written from scratch for smibhid based on the BH1750 datasheet.
Licensed under MIT License to match smibhid project license.

Datasheet: https://components101.com/sites/default/files/component_datasheet/BH1750.pdf

Copyright (c) 2025 So Make It
"""

from micropython import const
from utime import sleep_ms
from lib.sensors.sensor_module import SensorModule

# I2C Commands (from BH1750 datasheet)
_CMD_POWER_DOWN = const(0x00)
_CMD_POWER_ON = const(0x01)
_CMD_RESET = const(0x07)
_CMD_CONTINUOUS_HIGH_RES = const(0x10)
_CMD_CONTINUOUS_HIGH_RES2 = const(0x11)
_CMD_CONTINUOUS_LOW_RES = const(0x13)

# Default I2C address (ADDR pin low)
_I2C_ADDRESS = const(0x23)

# Measurement timing constants from datasheet
_DEFAULT_MEAS_TIME = const(69)
_SENSITIVITY_FACTOR = const(12)  # 1.2 * 10 to avoid float in const


class BH1750(SensorModule):
    """Driver for BH1750 digital ambient light sensor.
    
    This driver defaults to continuous high-resolution mode to avoid blocking
    the asyncio event loop on every measurement read. The sensor continuously
    measures light and updates its internal register, allowing instant reads.
    
    Measurement specifications (from datasheet):
    - High resolution mode: 1 lx resolution, 120ms measurement time
    - High resolution mode2: 0.5 lx resolution, 120ms measurement time  
    - Low resolution mode: 4 lx resolution, 16ms measurement time
    """

    def __init__(self, i2c, address: int = _I2C_ADDRESS):
        """Initialize BH1750 sensor.
        
        Args:
            i2c: MicroPython I2C interface object
            address: I2C address (default 0x23)
        """
        super().__init__([{"name": "light", "unit": "lx"}])
        self._i2c = i2c
        self._address = address
        self._mode_cmd = _CMD_CONTINUOUS_HIGH_RES
        self._resolution_factor = 1.0
        
        # Power on and start continuous measurement
        # This blocking delay only happens once at initialization
        self._i2c.writeto(self._address, bytes([_CMD_POWER_ON]))
        sleep_ms(10)  # Power-on time from datasheet
        self._i2c.writeto(self._address, bytes([_CMD_CONTINUOUS_HIGH_RES]))
        sleep_ms(180)  # Max measurement time for high resolution mode
        
    def _read_raw(self) -> int:
        """Read raw 16-bit value from sensor.
        
        Returns:
            int: Raw light level value (0-65535)
        """
        data = bytearray(2)
        self._i2c.readfrom_into(self._address, data)
        return (data[0] << 8) | data[1]
    
    def read_light_level(self) -> float:
        """Read light level in lux.
        
        This method reads instantly without blocking since the sensor is in
        continuous measurement mode and constantly updates its internal register.
        
        Returns:
            float: Light level in lux
        """
        raw_value = self._read_raw()
        # Formula from datasheet: lux = raw_value / 1.2
        # Using integer math: raw_value * 10 / 12
        lux = (raw_value * 10) / _SENSITIVITY_FACTOR
        return lux * self._resolution_factor
    
    def set_mode_high_res(self) -> None:
        """Set high resolution mode (1 lx resolution, 120ms update).
        
        Note: This method blocks for 180ms while the sensor takes its first
        measurement in the new mode. Subsequent reads via read_light_level()
        will be instant.
        """
        self._mode_cmd = _CMD_CONTINUOUS_HIGH_RES
        self._resolution_factor = 1.0
        self._i2c.writeto(self._address, bytes([_CMD_CONTINUOUS_HIGH_RES]))
        sleep_ms(180)
    
    def set_mode_high_res2(self) -> None:
        """Set high resolution mode 2 (0.5 lx resolution, 120ms update).
        
        Note: This method blocks for 180ms while the sensor takes its first
        measurement in the new mode. Subsequent reads via read_light_level()
        will be instant.
        """
        self._mode_cmd = _CMD_CONTINUOUS_HIGH_RES2
        self._resolution_factor = 0.5
        self._i2c.writeto(self._address, bytes([_CMD_CONTINUOUS_HIGH_RES2]))
        sleep_ms(180)
    
    def set_mode_low_res(self) -> None:
        """Set low resolution mode (4 lx resolution, 16ms update).
        
        Note: This method blocks for 24ms while the sensor takes its first
        measurement in the new mode. Subsequent reads via read_light_level()
        will be instant.
        """
        self._mode_cmd = _CMD_CONTINUOUS_LOW_RES
        self._resolution_factor = 1.0
        self._i2c.writeto(self._address, bytes([_CMD_CONTINUOUS_LOW_RES]))
        sleep_ms(24)
    
    def power_down(self) -> None:
        """Put sensor into power-down mode to save energy."""
        self._i2c.writeto(self._address, bytes([_CMD_POWER_DOWN]))
    
    def power_on(self) -> None:
        """Wake sensor from power-down mode."""
        self._i2c.writeto(self._address, bytes([_CMD_POWER_ON]))
        sleep_ms(10)
    
    def reset(self) -> None:
        """Reset the sensor data register.
        
        Note: This only works in power-on mode.
        """
        self._i2c.writeto(self._address, bytes([_CMD_RESET]))
    
    def get_reading(self) -> dict[str, float]:
        """Get sensor reading in SMIBHID format.
        
        This method is compatible with the asyncio event loop and will not
        block since the sensor is in continuous measurement mode.
        
        Returns:
            dict: Dictionary with key 'light' and value in lux
        """
        return {
            "light": round(self.read_light_level(), 2)
        }
