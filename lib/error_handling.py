from display import Display
from asyncio import Event, create_task
from ulogging import uLogger

class ErrorHandling: # TODO add pytests for this class
    def __init__(self, display: Display, error_event: Event, loaded_modules: list) -> None:
        self.log = uLogger("ErrorHandling")
        self.display = display
        self.error_event = error_event
        self.loaded_modules = loaded_modules
        
    def startup(self) -> None:  
        self.log.info("Starting error monitor watcher")
        create_task(self.async_error_monitor_watcher())

    async def async_error_monitor_watcher(self) -> None: # TODO remove the watcher and call this function when a module raises an error, the module will register itself and specific module errors on init.
        """
        Coroutine to watch for error states set by modules passed the error_event and update current errors from loaded modules. Handlers such as "display" can display
        appropriate error information on attached screens.
        """
        while True:
            self.errors = []
            await self.error_event.wait()
            self.log.info("Error event triggered")
            for module in self.loaded_modules:
                try:
                    self.log.info(f"Checking for errors in module {module.__class__.__name__}")
                    self.errors.extend(module.errors)
                    self.log.info(f"Errors in module: {module.errors}")
                except AttributeError:
                    self.log.info(f"Module {module.__class__.__name__} does not have an attribute of self.errors.")
                except TypeError:
                    self.log.info(f"Module {module.__class__.__name__} attribute self.errors is not of type list.")
                except Exception as e:
                    self.log.error(f"Error processing error in module {module.__class__.__name__}: {e}")
            self.log.info(f"Errors found: {self.errors}")
            self.display.update_errors(self.errors)
            self.error_event.clear()