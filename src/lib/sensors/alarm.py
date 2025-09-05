from lib.ulogging import uLogger
from config import (
    CO2_ALARM_THRESHOLD_PPM,
    CO2_ALARM_RESET_THRESHOLD_PPM,
    CO2_ALARM_SNOOZE_DURATION_S,
    CO2_ALARM_LED_PIN,
    CO2_ALARM_BUZZER_PIN,
    CO2_ALARM_SNOOZE_BUTTON_PIN,
    CO2_ALARM_SILENCE_WINDOW_START_HOUR,
    CO2_ALARM_SILENCE_WINDOW_END_HOUR
    )
from machine import Pin
from asyncio import create_task, sleep, Event, CancelledError
from lib.button import Button
from time import time, localtime
from lib.displays.display import Display
from lib.space_state import SpaceState
from lib.utils import DateTimeUtils

class Alarm:
    """
    Alarm class to handle sensor alarms.
    """
    def __init__(self, display: Display, space_state: SpaceState) -> None:
        self.log = uLogger("Alarm")
        self.log.info("Alarm module initialized")
        self.date_time_utils = DateTimeUtils()
        self.display = display
        self.space_state = space_state
        self.enabled = False
        self.status = 0
        self.status_lookup = {
            0: "Off",
            1: "Triggered",
            2: "Snoozed",
            3: "Silenced"
        }

    def enable(self, ) -> None:
        """
        Enable the CO2 alarm.
        """
        self.log.info("Enabling CO2 alarm")
        self.enabled = True
        self.co2_alarm_buzzer = Pin(CO2_ALARM_BUZZER_PIN, Pin.OUT)
        self.co2_alarm_led = Pin(CO2_ALARM_LED_PIN, Pin.OUT)
        self.co2_alarm_snooze_event = Event()
        self.co2_alarm_snooze_button = Button(CO2_ALARM_SNOOZE_BUTTON_PIN, "CO2 alarm snooze", self.co2_alarm_snooze_event)
        self.co2_alarm_buzzer_snooze_set_time = None
        self.alarm_task = None
        create_task(self.co2_alarm_snooze_button.wait_for_press())
        create_task(self.async_co2_alarm_button_press_watcher())

    async def async_test_co2_alarm(self) -> None:
        """
        Asynchronously test the CO2 alarm by sounding the buzzer and turning on the LED.
        """
        self.log.info("Testing CO2 alarm")
        self.display.update_alarm("Testing")
        self.co2_alarm_buzzer.on()
        self.co2_alarm_led.on()
        await sleep(0.5)
        self.display.update_alarm("Clear")
        self.co2_alarm_buzzer.off()
        self.co2_alarm_led.off()
    
    async def async_start_alarm(self) -> None:
        """
        Asynchronously sound the CO2 alarm.
        """
        self.log.info("Starting CO2 alarm")
        if self.alarm_task and not self.alarm_task.done():
            self.log.error("CO2 alarm task already running, method should not have been called.")
            return

        self.alarm_task = create_task(self.async_alarm_buzzer_loop())

    async def async_alarm_buzzer_loop(self) -> None:
        """
        Asynchronously loop to sound the CO2 alarm buzzer with a pause instead of continuously.
        """
        try:
            while True:
                self.co2_alarm_buzzer.on()
                await sleep(0.5)
                self.co2_alarm_buzzer.off()
                await sleep(0.5)
        
        except CancelledError:
            self.log.info("CO2 alarm task was canceled")

    async def async_stop_alarm(self) -> None:
        """
        Stop the CO2 alarm and task.
        """
        self.log.info("Stopping CO2 alarm")
        if self.alarm_task and not self.alarm_task.done():
            self.alarm_task.cancel()
            try:
                await self.alarm_task  # Wait for the task to finish cleanup
            
            except CancelledError:
                self.log.info("CO2 alarm task cancellation confirmed")
        
        self.alarm_task = None
        self.co2_alarm_buzzer.off()
    
    async def async_co2_alarm_button_press_watcher(self) -> None:
        """
        Asynchronously wait for the CO2 alarm snooze button press event.
        """
        while True:
            await self.co2_alarm_snooze_event.wait()
            self.co2_alarm_snooze_event.clear()
            
            self.log.info("CO2 alarm snooze button pressed")
            power_state = self.are_all_power_managed_displays_powered_on()
                
            if power_state:
                self.snooze_co2_alarm()
            else:
                self.display.power_on()

    def are_all_power_managed_displays_powered_on(self) -> bool:
        """
        Check all returned power states (displays supporting power on/off) from
        the display abstraction layer and return True if all of them are
        powered on.
        If no displays with power states are connected, return True by default.
        """
        power_states = self.display.get_power_state()
        
        for power_state in power_states:
            if power_states[power_state] is False:
                self.log.info(f"{power_state} is powered off, returning False")
                return False

        self.log.info("No displays with power control are powered off; returning True")
        return True

    def assess_co2_alarm(self, readings: dict) -> None:
        """
        Assess the CO2 alarm state based on readings from the SCD30 sensor.
        """
        if "SCD30" in readings and "co2" in readings["SCD30"] and readings["SCD30"]["co2"] != 0:
            self.log.info("Assessing CO2 alarm state")
            co2_ppm = readings["SCD30"]["co2"]
            if co2_ppm >= CO2_ALARM_THRESHOLD_PPM:
                self.log.info(f"CO2 of {co2_ppm} ppm above alarm threshold of ({CO2_ALARM_THRESHOLD_PPM} ppm), setting alarm")
                self.set_co2_alarm()
                
            elif co2_ppm <= CO2_ALARM_RESET_THRESHOLD_PPM:
                self.log.info(f"CO2 of {co2_ppm} ppm below alarm reset threshold of ({CO2_ALARM_RESET_THRESHOLD_PPM} ppm), resetting alarm")
                self.unset_co2_alarm()
                self.status = 0
        else: 
            self.log.error("SCD30 sensor data not found in readings, unable to assess CO2 alarm state")
    
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
        create_task(self.async_stop_alarm())
        self.display.update_alarm("Clear")

    def snooze_co2_alarm(self) -> None:
        """
        Snooze the CO2 alarm.
        """
        self.log.info("Snoozing CO2 alarm")
        create_task(self.async_stop_alarm())
        self.co2_alarm_buzzer_snooze_set_time = time()
        self.display.update_alarm("Snoozed")    

    def alarm_should_sound(self) -> bool:
        """
        Determine if the CO2 alarm should sound based on space state and time
        of day.
        """
        if not self.space_state.get_space_state():
            self.log.info("Space is closed, CO2 alarm should not sound")
            return False

        if self.in_alarm_silence_window():
            self.log.info("Current time is within CO2 alarm silence window, alarm should not sound")
            return False

        return True

    def in_alarm_silence_window(self) -> bool:
        """
        Check if the current time is within the CO2 alarm silence window.
        Handles cases where the silence window spans across midnight (e.g., 22:00 to 08:00).
        """
        self.log.info("Checking if current time is within CO2 alarm silence window")
        current_hour = localtime()[3]

        try:
            if self.date_time_utils.uk_bst():
                current_hour += 1
        except ValueError as e:
            self.log.error(f"Error checking UK BST: {e}, time may be incorrect for BST")

        self.log.info(f"Current hour: {current_hour}")
        self.log.info(f"CO2 alarm silence window start hour: {CO2_ALARM_SILENCE_WINDOW_START_HOUR}, end hour: {CO2_ALARM_SILENCE_WINDOW_END_HOUR}")
        if (CO2_ALARM_SILENCE_WINDOW_START_HOUR is not None and
                CO2_ALARM_SILENCE_WINDOW_END_HOUR is not None):
            
            start_hour = CO2_ALARM_SILENCE_WINDOW_START_HOUR
            end_hour = CO2_ALARM_SILENCE_WINDOW_END_HOUR
            
            if start_hour < end_hour:
                if start_hour <= current_hour < end_hour:
                    self.log.info("Current time is within CO2 alarm silence window")
                    return True
            else:
                if current_hour >= start_hour or current_hour <= end_hour:
                    self.log.info("Current time is within CO2 alarm silence window (crosses midnight)")
                    return True
        
        self.log.info("Current time is outside CO2 alarm silence window")
        return False

    def set_co2_alarm_buzzer(self) -> None:
        """
        Set the CO2 alarm buzzer state.
        """
        self.log.info("Setting CO2 alarm buzzer state")
        if self.co2_alarm_buzzer_snooze_set_time is None or time() - self.co2_alarm_buzzer_snooze_set_time >= CO2_ALARM_SNOOZE_DURATION_S:
            self.log.info("CO2 above threshold and alarm not snoozed")
            if  self.alarm_should_sound():
                self.log.info("CO2 alarm silence window not active and space open, setting alarm buzzer")
                self.status = 1
                
                if not self.alarm_task or self.alarm_task.done():
                    self.log.info("Setting CO2 alarm buzzer")
                    create_task(self.async_start_alarm())
                    self.display.update_alarm("Triggered")
            else:
                self.log.info("CO2 alarm silence window active or space closed, not setting alarm buzzer")
                self.status = 3
                if self.alarm_task and not self.alarm_task.done():
                    self.display.update_alarm("Silenced")
                    self.log.warn("CO2 alarm task running when it shouldn't be, cancelling CO2 alarm task")
                    create_task(self.async_stop_alarm())
                    
        else:
            self.log.info("CO2 alarm buzzer snoozed, not setting buzzer")
            self.display.update_alarm("Snoozed")
            self.status = 2
            if self.alarm_task and not self.alarm_task.done():
                self.log.warn("CO2 alarm task running when it shouldn't be, cancelling CO2 alarm task")
                create_task(self.async_stop_alarm())

    def get_status(self) -> dict:
        """
        Get the current status of the CO2 alarm.
        """
        self.log.info("Getting CO2 alarm status.")
        data = {"status": self.status, "status_text": self.status_lookup.get(self.status, "Unknown")}
        self.log.info(f"Current status value: {data}")
        return data
    
    def get_statuses(self) -> dict:
        """
        Get all possible CO2 alarm statuses.
        """
        self.log.info("Getting CO2 alarm statuses.")
        self.log.info(f"Current CO2 alarm statuses: {self.status_lookup}")
        return self.status_lookup.copy()

    def get_alarm_trigger_threshold(self) -> int:
        """
        Get the CO2 alarm trigger threshold in ppm.
        """
        self.log.info(f"CO2 alarm trigger threshold: {CO2_ALARM_THRESHOLD_PPM} ppm")
        return CO2_ALARM_THRESHOLD_PPM
    
    def get_alarm_reset_threshold(self) -> int:
        """
        Get the CO2 alarm reset threshold in ppm.
        """
        self.log.info(f"CO2 alarm reset threshold: {CO2_ALARM_RESET_THRESHOLD_PPM} ppm")
        return CO2_ALARM_RESET_THRESHOLD_PPM
