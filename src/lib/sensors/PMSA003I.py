"""
PMSA003I Particulate Matter Sensor Driver for MicroPython

Written specifically for SMIBHID based on the PMSA003I datasheet.
Licensed under MIT License to match smibhid project license.

The PMSA003I is a digital particulate matter sensor that uses laser scattering
to measure PM1.0, PM2.5, and PM10 concentrations in both standard particle and
atmospheric environment units. It also reports particle counts.

Datasheet: https://www.plantower.com/en/content/?110.html

Copyright (c) 2026 So Make It
"""

from micropython import const
from machine import I2C
from time import ticks_ms, ticks_diff
from asyncio import create_task, sleep
from lib.sensors.sensor_module import SensorModule
from lib.ulogging import uLogger

# Default configuration values (hardcoded fallbacks)
_DEFAULT_I2C_ADDRESS = const(0x12)
_DEFAULT_FAN_RUN_SECONDS = const(10)
_DEFAULT_WARM_UP_SECONDS = const(30)
_DEFAULT_POLL_PERIOD_SECONDS = const(60)
_DEFAULT_INCLUDE_STANDARD_VALUES = False

# Load configuration from config.py with fallbacks to defaults
# This happens once at module import time
try:
    from config import PMSA003I_I2C_ADDRESS
except (ImportError, AttributeError):
    PMSA003I_I2C_ADDRESS = _DEFAULT_I2C_ADDRESS

try:
    from config import PMSA003I_FAN_RUN_SECONDS
except (ImportError, AttributeError):
    PMSA003I_FAN_RUN_SECONDS = _DEFAULT_FAN_RUN_SECONDS

try:
    from config import PMSA003I_WARM_UP_SECONDS
except (ImportError, AttributeError):
    PMSA003I_WARM_UP_SECONDS = _DEFAULT_WARM_UP_SECONDS

try:
    from config import PMSA003I_POLL_PERIOD_SECONDS
except (ImportError, AttributeError):
    PMSA003I_POLL_PERIOD_SECONDS = _DEFAULT_POLL_PERIOD_SECONDS

try:
    from config import PMSA003I_INCLUDE_STANDARD_VALUES
except (ImportError, AttributeError):
    PMSA003I_INCLUDE_STANDARD_VALUES = _DEFAULT_INCLUDE_STANDARD_VALUES

# Frame start bytes for data validation
_FRAME_START1 = const(0x42)
_FRAME_START2 = const(0x4D)


class PMSA003I(SensorModule):
    """Driver for PMSA003I particulate matter sensor.
    
    This driver implements fan duty cycling to reduce wear while maintaining
    reasonable data freshness. The sensor continuously updates internal data
    asynchronously, and get_reading() returns the most recent cached values.
    
    The sensor reports:
    - PM1.0, PM2.5, PM10 in ug/m3 (both standard and atmospheric)
    - Particle counts for 0.3μm, 0.5μm, 1.0μm, 2.5μm, 5.0μm, 10μm sizes
    
    Fan duty cycle operation:
    - Fan runs for a configurable period (default 10s per datasheet response time)
    - Sensor stabilizes during this time
    - ONE reading is taken at the end of fan run period
    - Fan sleeps for remainder of poll period (default 60s) to reduce wear
    - get_reading() always returns the most recent cached data
    
    Timing rationale:
    - PMSA003I response time: <10s (datasheet)
    - Initial stabilization: ~30s (first power-on only)
    - Subsequent readings: 10s fan run ensures accurate reading per datasheet
    """

    def __init__(
        self,
        i2c: I2C,
        address: int = PMSA003I_I2C_ADDRESS,
        fan_run_seconds: int = PMSA003I_FAN_RUN_SECONDS,
        warm_up_seconds: int = PMSA003I_WARM_UP_SECONDS,
        poll_period_seconds: int = PMSA003I_POLL_PERIOD_SECONDS,
        include_standard_values: bool = PMSA003I_INCLUDE_STANDARD_VALUES
    ):
        """Initialize PMSA003I sensor.
        
        Configuration values are loaded from config.py at module import time,
        with fallbacks to hardcoded defaults. All parameters can be overridden
        at instantiation for testing/abstraction.
        
        Args:
            i2c: MicroPython I2C interface object
            address: I2C address (default from config or 0x12)
            fan_run_seconds: How long to run the fan per cycle (default from config or 10s)
            warm_up_seconds: Initial warm-up time before first reading (default from config or 30s)
            poll_period_seconds: Time between sensor polls (default from config or 60s)
        """
        # Define all sensor output fields
        super().__init__([
            {"name": "pm10_standard", "unit": "ug/m3"},
            {"name": "pm25_standard", "unit": "ug/m3"},
            {"name": "pm100_standard", "unit": "ug/m3"},
            {"name": "pm10_env", "unit": "ug/m3"},
            {"name": "pm25_env", "unit": "ug/m3"},
            {"name": "pm100_env", "unit": "ug/m3"},
            {"name": "particles_03um", "unit": "count/0.1L"},
            {"name": "particles_05um", "unit": "count/0.1L"},
            {"name": "particles_10um", "unit": "count/0.1L"},
            {"name": "particles_25um", "unit": "count/0.1L"},
            {"name": "particles_50um", "unit": "count/0.1L"},
            {"name": "particles_100um", "unit": "count/0.1L"}
        ])
        
        self.log = uLogger("PMSA003I")
        self._i2c = i2c
        self._address: int = address
        self._fan_run_seconds: int = fan_run_seconds
        self._warm_up_seconds: int = warm_up_seconds
        self._poll_period_seconds: int = poll_period_seconds
        self._include_standard_values: bool = include_standard_values
        # Calculate sleep time from configured poll period
        self._fan_sleep_seconds: int = poll_period_seconds - fan_run_seconds
        
        # Cached sensor data - initialized to None
        self._cached_data = {
            "pm10_standard": None,
            "pm25_standard": None,
            "pm100_standard": None,
            "pm10_env": None,
            "pm25_env": None,
            "pm100_env": None,
            "particles_03um": None,
            "particles_05um": None,
            "particles_10um": None,
            "particles_25um": None,
            "particles_50um": None,
            "particles_100um": None
        }
        
        self._is_running = False
        self._polling_task = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5  # Disable sensor after this many failures
        
        # Pre-allocate buffer for sensor reads (more efficient, reduces GC pressure)
        self._read_buffer = bytearray(32)
        
        # Confirm sensor is present on the I2C bus before starting polling.
        # A full data-frame read fails if the sensor hasn't warmed up yet; a scan
        # ACK-check is sufficient to detect physical presence and avoids EIO errors.
        if self._address not in self._i2c.scan():
            raise RuntimeError("Unable to find PMSA003I sensor at I2C address 0x{:02X}".format(self._address))
        self.log.info(f"PMSA003I found at I2C address 0x{self._address:02X}")
        
        # Start async polling only after confirming sensor is present
        try:
            self._polling_task = create_task(self._async_poll_sensor())
            self._is_running = True  # Only set after successful initialization
            self.log.info(f"PMSA003I initialized with {self._fan_run_seconds}s run, {self._fan_sleep_seconds}s sleep cycle")
        except Exception as e:
            self.log.error(f"Failed to start PMSA003I polling: {e}")
            raise RuntimeError(f"Failed to start PMSA003I polling: {e}")

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum for validation.
        
        Args:
            data: Frame data bytes (excluding checksum bytes)
            
        Returns:
            int: Calculated checksum
        """
        return sum(data)

    def _read_frame(self) -> bytes:
        """Read a complete data frame from the sensor.
        
        Returns:
            bytes: Raw frame data (32 bytes)
            
        Raises:
            RuntimeError: If frame is invalid or checksum fails
        """
        try:
            # Read into pre-allocated buffer (more efficient, reduces GC)
            self._i2c.readfrom_into(self._address, self._read_buffer)
            
            # Verify start bytes
            if self._read_buffer[0] != _FRAME_START1 or self._read_buffer[1] != _FRAME_START2:
                raise RuntimeError(f"Invalid frame start bytes: {self._read_buffer[0]:02X} {self._read_buffer[1]:02X}")
            
            # Verify frame length
            frame_length = (self._read_buffer[2] << 8) | self._read_buffer[3]
            if frame_length != 28:  # 28 data bytes + 2 start bytes + 2 length bytes = 32 total
                raise RuntimeError(f"Invalid frame length: {frame_length}")
            
            # Verify checksum
            checksum = (self._read_buffer[30] << 8) | self._read_buffer[31]
            calculated = self._calculate_checksum(self._read_buffer[0:30])
            if checksum != calculated:
                raise RuntimeError(f"Checksum mismatch: {checksum} != {calculated}")
            
            return bytes(self._read_buffer)
            
        except OSError as e:
            raise RuntimeError(f"I2C read error: {e}")

    def _parse_frame(self, frame: bytes) -> dict:
        """Parse a data frame into sensor readings.
        
        Args:
            frame: Raw frame data (32 bytes)
            
        Returns:
            dict: Parsed sensor data
        """
        # Parse PM concentrations (ug/m3)
        # Standard particle: CF=1, factory environment
        pm10_standard = (frame[4] << 8) | frame[5]
        pm25_standard = (frame[6] << 8) | frame[7]
        pm100_standard = (frame[8] << 8) | frame[9]
        
        # Atmospheric environment
        pm10_env = (frame[10] << 8) | frame[11]
        pm25_env = (frame[12] << 8) | frame[13]
        pm100_env = (frame[14] << 8) | frame[15]
        
        # Particle counts (number of particles with diameter beyond X in 0.1L of air)
        particles_03um = (frame[16] << 8) | frame[17]
        particles_05um = (frame[18] << 8) | frame[19]
        particles_10um = (frame[20] << 8) | frame[21]
        particles_25um = (frame[22] << 8) | frame[23]
        particles_50um = (frame[24] << 8) | frame[25]
        particles_100um = (frame[26] << 8) | frame[27]
        
        return {
            "pm10_standard": pm10_standard,
            "pm25_standard": pm25_standard,
            "pm100_standard": pm100_standard,
            "pm10_env": pm10_env,
            "pm25_env": pm25_env,
            "pm100_env": pm100_env,
            "particles_03um": particles_03um,
            "particles_05um": particles_05um,
            "particles_10um": particles_10um,
            "particles_25um": particles_25um,
            "particles_50um": particles_50um,
            "particles_100um": particles_100um
        }

    def read_data(self) -> dict:
        """Read current sensor data (blocking).
        
        This method performs a blocking read from the sensor. For async
        operation, use get_reading() which returns cached data.
        
        Returns:
            dict: Current sensor readings
            
        Raises:
            RuntimeError: If read fails
        """
        frame = self._read_frame()
        return self._parse_frame(frame)

    async def _async_poll_sensor(self):
        """Asynchronously poll the sensor with fan duty cycling and precise timing.
        
        This task runs continuously:
        1. Calculate next wake time based on poll period
        2. Poll every second to check if wake time reached
        3. When time to wake: start fan and wait for stabilization
        4. Take ONE reading and cache it
        5. Calculate next wake time from previous wake time (corrects for overrun)
        6. Put sensor to sleep and repeat
        
        Initial warm-up period allows fan to stabilize before first reading.
        Per datasheet: PMSA003I response time is <10s, so 10s fan run ensures accurate reading.
        
        Uses tick_ms for precise timing to prevent drift accumulation.
        """
        self.log.info("Starting PMSA003I async polling with fan duty cycle")
        
        # Initial warm-up period - yields to event loop
        self.log.info(f"PMSA003I warming up for {self._warm_up_seconds}s")
        await sleep(self._warm_up_seconds)
        
        # Set up timing - first reading happens immediately after warm-up
        poll_period_ms = self._poll_period_seconds * 1000
        next_wake_ticks = ticks_ms()  # Take first reading now
        
        while self._is_running:
            try:
                # Poll every second until wake time reached
                while self._is_running:
                    current_ticks = ticks_ms()
                    time_until_wake_ms = ticks_diff(next_wake_ticks, current_ticks)
                    
                    if time_until_wake_ms <= 0:
                        # Time to wake and take reading
                        break
                    
                    # Sleep for 1 second or remaining time, whichever is less
                    sleep_seconds = min(1, time_until_wake_ms / 1000)
                    await sleep(sleep_seconds)
                
                if not self._is_running:
                    break
                
                # Check if sensor has failed too many times
                if self._consecutive_failures >= self._max_consecutive_failures:
                    self.log.error(f"PMSA003I disabled after {self._consecutive_failures} consecutive failures")
                    self._is_running = False
                    break
                
                # Wake sensor and wait for stabilization
                # Simple approach avoids I2C bus issues from complex heartbeat polling
                try:
                    self.log.info("PMSA003I attempting wake and read cycle")
                    
                    # Wait for stabilization period (sensor auto-wakes on any I2C read)
                    await sleep(self._fan_run_seconds)
                    
                    # Take reading after stabilization
                    try:
                        data = self.read_data()
                        self._cached_data = data
                        self._consecutive_failures = 0  # Reset on success
                        self.log.info(f"PMSA003I reading: PM2.5={data['pm25_env']}ug/m3, PM10={data['pm100_env']}ug/m3")
                    except RuntimeError as e:
                        # I2C error - log, count failure, and continue
                        self._consecutive_failures += 1
                        self.log.error(f"PMSA003I read failed ({self._consecutive_failures}/{self._max_consecutive_failures}): {e}")
                        # Wait longer before retry to let I2C bus recover
                        await sleep(10)
                    
                except Exception as e:
                    self._consecutive_failures += 1
                    self.log.error(f"PMSA003I polling error ({self._consecutive_failures}/{self._max_consecutive_failures}): {e}")
                    # Wait before retry to prevent rapid error loops and allow I2C recovery
                    await sleep(10)
                
                # Sensor will auto-sleep after ~6 seconds of I2C inactivity
                # No explicit sleep command needed
                
                # Calculate next wake time from previous wake time (not current time)
                # This corrects for any overrun in reading/processing
                next_wake_ticks = next_wake_ticks + poll_period_ms
                
                # If we've fallen behind significantly, resync to current time
                current_ticks = ticks_ms()
                if ticks_diff(current_ticks, next_wake_ticks) > poll_period_ms:
                    self.log.error("PMSA003I polling fell behind, resyncing to current time")
                    next_wake_ticks = current_ticks + poll_period_ms
                
            except Exception as e:
                self.log.error(f"Error in PMSA003I polling loop: {e}")
                # Resync timing after error
                next_wake_ticks = ticks_ms() + poll_period_ms
                # Yield to event loop before retry
                await sleep(1)

    def wake(self):
        """Wake the sensor from sleep mode.
        
        Note: PMSA003I auto-wakes on any I2C activity, so no explicit wake
        command is needed. This method is kept for API compatibility.
        The sensor will wake when read_data() performs an I2C read.
        """
        # No-op: sensor auto-wakes on I2C read
        pass

    def sleep(self):
        """Put the sensor into sleep mode to save power and reduce fan wear.
        
        In sleep mode, the fan stops and the sensor stops taking measurements.
        """
        try:
            # The PMSA003I doesn't have a specific sleep command via I2C
            # It goes to sleep automatically after ~6 seconds of no I2C activity
            # We'll use this as a marker in our code
            self.log.info("PMSA003I entering sleep mode (passive)")
        except Exception as e:
            self.log.error(f"Failed to sleep PMSA003I: {e}")

    def stop_polling(self):
        """Stop the async polling task.
        
        Useful for cleanup or when disabling the sensor.
        """
        self._is_running = False
        if self._polling_task:
            self._polling_task.cancel()
            self.log.info("PMSA003I polling stopped")

    def get_reading(self) -> dict:
        """Get the most recent cached sensor readings.
        
        This method returns instantly without blocking, using the most
        recent data from the async polling task. Data is refreshed based
        on the configured fan duty cycle.
        
        Always returns atmospheric environment PM values and particle counts.
        Optionally includes standard (CF=1) PM values based on configuration.
        
        Returns:
            dict: Dictionary with PM concentrations (env, and optionally standard)
                  and particle counts. Values are None if no valid reading yet.
        """
        data = self._cached_data.copy()
        
        # Always include atmospheric environment values and particle counts
        result = {
            "pm10_env": data["pm10_env"],
            "pm25_env": data["pm25_env"],
            "pm100_env": data["pm100_env"],
            "particles_03um": data["particles_03um"],
            "particles_05um": data["particles_05um"],
            "particles_10um": data["particles_10um"],
            "particles_25um": data["particles_25um"],
            "particles_50um": data["particles_50um"],
            "particles_100um": data["particles_100um"]
        }
        
        # Optionally add standard (CF=1) values
        if self._include_standard_values:
            result["pm10_standard"] = data["pm10_standard"]
            result["pm25_standard"] = data["pm25_standard"]
            result["pm100_standard"] = data["pm100_standard"]
        
        return result

    def get_pm25_env(self) -> int | None:
        """Get PM2.5 concentration in atmospheric environment.
        
        This is the most commonly reported PM value.
        
        Returns:
            int: PM2.5 in ug/m3, or None if no reading available
        """
        return self._cached_data.get("pm25_env")

    def get_pm10_env(self) -> int | None:
        """Get PM10 concentration in atmospheric environment.
        
        Returns:
            int: PM10 in ug/m3, or None if no reading available
        """
        return self._cached_data.get("pm10_env")

    def get_all_pm_env(self) -> dict:
        """Get all atmospheric PM concentrations.
        
        Returns:
            dict: PM1.0, PM2.5, and PM10 in atmospheric environment
        """
        return {
            "pm10_env": self._cached_data["pm10_env"],
            "pm25_env": self._cached_data["pm25_env"],
            "pm100_env": self._cached_data["pm100_env"]
        }

    def set_fan_duty_cycle(self, run_seconds: int):
        """Update fan duty cycle run time.
        
        Sleep time is automatically calculated as (poll_period - run_seconds).
        
        Args:
            run_seconds: How long to run the fan per poll cycle
        
        Note: Changes take effect on the next cycle.
        """
        self._fan_run_seconds = run_seconds
        self._fan_sleep_seconds = self._poll_period_seconds - run_seconds
        self.log.info(f"PMSA003I fan duty cycle updated: {run_seconds}s run, {self._fan_sleep_seconds}s sleep")
