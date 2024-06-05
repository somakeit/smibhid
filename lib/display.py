from ulogging import uLogger
from registry import driver_registry
from LCD1602 import LCD1602
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
        for screen in self.screens:
            if hasattr(screen, command):
                method = getattr(screen, command)
                if callable(method):
                    method(*args)

    def clear(self) -> None:
        """Clear all screens."""
        self._execute_command("clear")
    
    def print_startup(self, version: str) -> None:
        """Display startup information on all screens."""
        self._execute_command("print_startup", version)

    def print_space_state(self, state: str) -> None:
        """Update space state information on all screens."""
        self._execute_command("print_space_state", state)