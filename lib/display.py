from ulogging import uLogger
from registry import driver_registry
from LCD1602 import LCD1602

class Display:
    """
    Display management for SMIBHID to drive displays via driver classes abstracting display constraints from the messaging required.
    Provides functions to clear display and print top or bottom line text.
    Currently supports 2x16 character LCD display.
    """
    def __init__(self, log_level: int, drivers: list) -> None:
        """Attempt to configure screens defined in config file."""
        self.log = uLogger("Display", log_level)
        self.log.info("Init display")
        self.enabled = False
        self.screens = []
        
        for driver in drivers:
            try:
                driver_class = driver_registry.get_driver_class(driver)

                if driver_class is None:
                    raise ValueError(f"Display driver class '{driver}' not registered.")

                self.screens.append(driver_class(log_level))

            except Exception as e:
                print(f"An error occurred while confguring display driver '{driver}': {e}")
                raise
                
        if len(self.screens) > 0:
            self.log.info(f"Display functionality enabled: {len(self.screens)} screens configured.")
        else:
            self.log.info("No screens configured successfully; Display functionality disabled.")
            self.enabled = False

    def execute_command(self, command: str, *args) -> None:
        for screen in self.screens:
            if hasattr(screen, command):
                method = getattr(screen, command)
                if callable(method):
                    method(*args)

    def clear(self) -> None:
        self.execute_command("clear")
    
    def print_startup(self, version: str) -> None:
        self.execute_command("print_startup", version)

    def print_space_state(self, state: str) -> None:
        self.execute_command("print_space_state", state)