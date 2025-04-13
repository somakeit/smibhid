from lib.ulogging import uLogger
from config import (
    CO2_ALARM_THRESHOLD_PPM,
    CO2_ALARM_RESET_THRESHOLD_PPM,
    CO2_ALARM_SNOOZE_DURATION_S,
    CO2_ALARM_LED_PIN,
    CO2_ALARM_BUZZER_PIN,
    CO2_ALARM_SNOOZE_BUTTON_PIN
    )
from machine import Pin
from asyncio import create_task, run, sleep, Event, CancelledError
from lib.button import Button
from time import time

class Alarm:
    """
    Alarm class to handle sensor alarms.
    """
    def __init__(self) -> None:
        self.log = uLogger("Alarm")
        self.log.info("Alarm module initialized")
        self.co2_alarm_buzzer = Pin(CO2_ALARM_BUZZER_PIN, Pin.OUT)
        self.co2_alarm_led = Pin(CO2_ALARM_LED_PIN, Pin.OUT)
        run(self.async_test_co2_alarm())
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
        self.co2_alarm_buzzer.on()
        self.co2_alarm_led.on()
        await sleep(0.5)
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
        Asynchronously loop to sound the CO2 alarm buzzer.
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
            self.snooze_co2_alarm()
    
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

    def snooze_co2_alarm(self) -> None:
        """
        Snooze the CO2 alarm for a specified duration.
        """
        self.log.info("Snoozing CO2 alarm")
        create_task(self.async_stop_alarm())
        self.co2_alarm_buzzer_snooze_set_time = time()    

    def set_co2_alarm_buzzer(self) -> None:
        """
        Set the CO2 alarm buzzer state.
        """
        self.log.info("Setting CO2 alarm buzzer state")
        if self.co2_alarm_buzzer_snooze_set_time is None or time() - self.co2_alarm_buzzer_snooze_set_time >= CO2_ALARM_SNOOZE_DURATION_S:
            self.log.info("CO2 above threshold and alarm not snoozed, ensuring alarm is on")
            
            if not self.alarm_task or self.alarm_task.done():
                self.log.info("Setting CO2 alarm buzzer")
                create_task(self.async_start_alarm())
                    
        else:
            self.log.info("CO2 alarm buzzer snoozed, not setting buzzer")
            if self.alarm_task and not self.alarm_task.done():
                self.log.warn("CO2 alarm task running when it shouldn't be, cancelling CO2 alarm task")
                create_task(self.async_stop_alarm())
