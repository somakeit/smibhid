import gc

class uLogger:
    
    def __init__(self, module_name: str, log_level: int = 0, handlers: list = []) -> None:
        """
        Init with module name to log and session debug level, that defaults to 2 and can be overidden globally using log_level=x in config.py
        Raise a debug message using the appropriate function for the severity
        Debug level 0-3: Each level adds more verbosity
        0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info
        """
        self.module_name = module_name
        self.configure_log_level(log_level)
        self.configure_handlers(handlers)

    def configure_log_level(self, log_level: int) -> None:
        self.log_level = 0
        
        if log_level > 0:
            self.log_level = log_level
        else:
            try:
                from config import log_level as config_log_level
                self.log_level = config_log_level
            except ImportError:
                print("config.py not found. Using default log level.")
            except AttributeError:
                print("log_level not found in config.py. Using default log level.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Using default log level.")

    def configure_handlers(self, handlers: list) -> None: # TODO make this DRY with above.
        self.handlers = []
        
        if len(handlers) > 0:
            self.handlers = handlers
        else:
            try:
                from config import log_handlers as config_log_handlers
                self.handlers = config_log_handlers
            except ImportError:
                print("config.py not found. Using default output handler.")
            except AttributeError:
                print("log_handlers not found in config.py. Using default output handler.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Using default output handler.")

    def decorate_message(self, message: str, level: str) -> str:
        decorated_message = f"[Mem: {round(gc.mem_free() / 1024)}kB free][{level}][{self.module_name}]: {message}"
        return decorated_message
    
    def process_handlers(self, message: str) -> None:
        for handler in self.handlers:
            try:
                handler_class = globals().get(handler)
                
                if handler_class is None:
                    raise ValueError(f"Handler class '{handler}' not found.")
                
                handler = handler_class()
                handler.emit(message)
            except Exception as e:
                print(f"An error occurred while processing handler '{handler}': {e}")
                raise
    
    def info(self, message: str) -> None:
        if self.log_level > 3:
            self.process_handlers(self.decorate_message(message, "Info"))

    def warn(self, message: str) -> None:
        if self.log_level > 2:
            self.process_handlers(self.decorate_message(message, "Warning"))

    def error(self, message: str) -> None:
        if self.log_level > 1:
            self.process_handlers(self.decorate_message(message, "Error"))

    def critical(self, message: str) -> None:
        if self.log_level > 0:
            self.process_handlers(self.decorate_message(message, "Critical"))

class console:
    def __init__(self) -> None:
        pass
    
    def emit(self, message) -> None:
        print(message)

class file:
    def __init__(self) -> None:
        # Setup file for streaming
        pass
    
    def emit(self, message) -> None:
        print(f"Dummy file output: {message}")

    def check_for_rotate(self) -> None:
        pass

    def rotate_file(self) -> None:
        pass