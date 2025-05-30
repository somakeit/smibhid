from lib.ulogging import uLogger
from lib.registry import driver_registry
from lib.displays.LCD1602 import LCD1602 # Importing the module registers the driver - do not remove this  # noqa: F401
from lib.displays.SSD1306 import SSD1306 # Importing the module registers the driver - do not remove this  # noqa: F401
from config import DISPLAY_DRIVERS
class Display:
    """
    Abstracted display capabilities for supported physical displays.
    Display drivers must be provided as modules and included in this module to be made available for loading in config.py
    All abstracted functions should be defined in this module and will be passed to each configured display (if supported) for the driver to interpret.
    
    Example:
    If an LCD1602 driver is configured to load, then issuing the command Display.print_startup() will render startup information appropriately on the 2x16 display if connected.
    """
    def __init__(self, i2c) -> None:
        self.log = uLogger("Display")
        self.drivers = DISPLAY_DRIVERS
        self.log.info("Init display")
        self.enabled = False
        self.screen_name = "all"
        self.i2c = i2c
        self.screens = []
        self._load_configured_drivers()
        self.state = "Unknown"
        self.errors = {}
        
    def _load_configured_drivers(self) -> None:
        for driver in self.drivers:
            try:
                driver_class = driver_registry.get_driver_class(driver)

                if driver_class is None:
                    raise ValueError(f"Display driver class '{driver}' not registered.")

                self.screens.append(driver_class(self.i2c))

            except Exception as e:
                print(f"An error occurred while confguring display driver '{driver}': {e}")
                
        if len(self.screens) > 0:
            self.log.info(f"Display functionality enabled: {len(self.screens)} screen objects configured: {self.screens}")
            self.enabled = True
        else:
            self.log.info("No screens configured successfully; Display functionality disabled.")
            self.enabled = False

    def _execute_command(self, command: str, *args) -> dict:
        """Execute a command on specified screen, defaults to all screens."""
        results = {}
        self.log.info(f"Executing command {command} on screen {self.screen_name}, with arguments: {args}")
        for screen in self.screens:
            screen_name = screen.__class__.__name__
            self.log.info(f"Checking screen: {screen_name} against {self.screen_name}.")
            if self.screen_name == "all" or self.screen_name == screen_name:
                if hasattr(screen, command):
                    method = getattr(screen, command)
                    self.log.info(f"Executing command on screen: {screen.__class__.__name__}")
                    if callable(method):
                        results[screen_name] = method(*args)
        self.screen_name = "all"
        
        return results
    
    def set_screen_for_next_command(self, screen_name: str) -> bool:
        """
        Set the screen to execute the next command on. If the screen is not found, retain all screens.
        Returns True if the screen was found and set, False if not.
        """
        self.log.info(f"Setting screen for next command to {screen_name}")
        if any(screen.__class__.__name__ == screen_name for screen in self.screens):
            self.log.info(f"Screen {screen_name} found, setting for next command.")
            self.screen_name = screen_name
            return True
        else:
            self.log.warn(f"Screen {screen_name} not found, retaining all screens and returning screen missing error.")
            self.screen_name = "all"
            return False

    def clear(self) -> None:
        """Clear all screens."""
        self._execute_command("clear")
    
    def print_update_startup(self) -> None:
        """Display update startup information on all screens."""
        self._execute_command("print_update_startup")

    def print_download_progress(self, current: int, total: int) -> None:
        """Display download progress information on all screens."""
        self._execute_command("print_download_progress", current, total)
    
    def print_update_status(self, status: str) -> None:
        """Display update status information on all screens."""
        self._execute_command("print_update_status", status)
    
    def print_startup(self, version: str) -> None:
        """Display startup information on all screens."""
        self._execute_command("print_startup", version)

    def _update_status(self) -> None:
        """Update state and error information on all screens."""
        self.log.info("Updating status on all screens")
        self._execute_command("update_status", {"state": self.state, "errors": self.errors})

    def update_state(self, state: str) -> None:
        self.state = state
        self._update_status()
    
    def update_errors(self, errors: list) -> None:
        self.errors = errors
        self._update_status()

    def set_busy_output(self) -> None:
        """Set all screens to busy output."""
        self.log.info("Setting all screens to busy output")
        self._execute_command("set_busy_output")
    
    def clear_busy_output(self) -> None:
        """Clear all screens from busy output."""
        self.log.info("Clearing all screens of busy output")
        self._execute_command("clear_busy_output")

    def add_hours(self, open_for_hours: int) -> None:
        """Display a screen for adding open for hours information."""
        self.log.info("Adding hours screen")
        self._execute_command("add_hours", open_for_hours)
    
    def cancelling(self) -> None:
        """Display cancelling text."""
        self.log.info("Cancelling")
        self._execute_command("cancelling")
    
    def update_co2(self, co2: str) -> None:
        """Update CO2 information on all screens."""
        self.log.info(f"Updating CO2 information: {co2}")
        self._execute_command("update_co2", co2)

    def update_alarm(self, alarm: str) -> None:
        """Update alarm information on all screens."""
        self.log.info(f"Updating alarm information: {alarm}")
        self._execute_command("update_alarm", alarm)
    
    def get_power_state(self) -> dict:
        """Get power state information on all screens."""
        self.log.info("Getting power state information")
        results = self._execute_command("get_power_state")
        self.log.info(f"Power state information: {results}")
        return results
    
    def power_on(self) -> None:
        """Power on all screens."""
        self.log.info("Powering on all screens")
        self._execute_command("power_on")
