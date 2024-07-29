from lib.ulogging import uLogger
from lib.registry import driver_registry
from lib.LCD1602 import LCD1602
from config import DISPLAY_DRIVERS

class Display:
    """
    Abstracted display capabilities for supported physical displays.
    Display drivers must be provided as modules and included in this module to be made available for loading in config.py
    All abstracted functions should be defined in this module and will be passed to each configured display (if supported) for the driver to interpret.
    
    Example:
    If an LCD1602 driver is configured to load, then issuing the command Display.print_startup() will render startup information appropriately on the 2x16 display if connected.
    """
    def __init__(self) -> None:
        self.log = uLogger("Display")
        self.drivers = DISPLAY_DRIVERS
        self.log.info("Init display")
        self.enabled = False
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

                self.screens.append(driver_class())

            except Exception as e:
                print(f"An error occurred while confguring display driver '{driver}': {e}")
                
        if len(self.screens) > 0:
            self.log.info(f"Display functionality enabled: {len(self.screens)} screens configured.")
        else:
            self.log.info("No screens configured successfully; Display functionality disabled.")
            self.enabled = False

    def _execute_command(self, command: str, *args) -> None:
        self.log.info(f"Executing command on screen drivers: {command}, with arguments: {args}")
        for screen in self.screens:
            if hasattr(screen, command):
                method = getattr(screen, command)
                self.log.info(f"Executing command on screen: {screen}")
                if callable(method):
                    method(*args)

    def clear(self) -> None:
        """Clear all screens."""
        self._execute_command("clear")
    
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
