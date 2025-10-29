from gc import mem_free
from os import stat, remove, rename
from time import gmtime, time

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
                from config import LOG_LEVEL as config_log_level
                self.log_level = config_log_level
            except ImportError:
                print("LOG_LEVEL not found in config.py not found. Using default log level.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Using default log level.")

    def configure_handlers(self, handlers: list) -> None:
        self.handlers = []
        self.handler_objects = []
        
        if len(handlers) > 0:
            self.handlers = handlers
        else:
            try:
                from config import LOG_HANDLERS as config_log_handlers
                self.handlers = config_log_handlers
            except ImportError:
                print("LOG_HANDLERS not found in config.py not found. Using default output handler.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Using default output handler.")
        
        for handler in self.handlers:
            try:
                handler_class = globals().get(handler)
                
                if handler_class is None:
                    raise ValueError(f"Handler class '{handler}' not found.")
                
                handler = handler_class()
                self.handler_objects.append(handler)
            except Exception as e:
                print(f"An error occurred while confguring handler '{handler}': {e}")
                raise

    def decorate_message(self, message: str, level: str) -> str:
        time_str = gmtime(time())
        timestamp = f"{time_str[0]}-{time_str[1]}-{time_str[2]} {time_str[3]}:{time_str[4]}:{time_str[5]}"
        decorated_message = f"[{timestamp}][Mem: {round(mem_free() / 1024)}kB free][{level}][{self.module_name}]: {message}"
        return decorated_message
    
    def process_handlers(self, message: str) -> None:
        for handler in self.handler_objects:
            try:
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

class Console:
    def __init__(self) -> None:
        pass
    
    def emit(self, message) -> None:
        print(message)

class File:
    def __init__(self) -> None:
        self.log_file = "log.txt"
        self.second_log_file = "log2.txt"
        from config import LOG_FILE_MAX_SIZE
        self.LOG_FILE_MAX_SIZE = LOG_FILE_MAX_SIZE
    
    def emit(self, message) -> None:
        with open(self.log_file, "a") as log_file:
            log_file.write(message + "\n")
        self.check_for_rotate()

    def check_for_rotate(self) -> None:
        log_file_size = stat(self.log_file)[6]
        if log_file_size > self.LOG_FILE_MAX_SIZE:
            self.rotate_file()

    def rotate_file(self) -> None:
        try:
            remove(self.second_log_file)
        except OSError:
            print(f"{self.second_log_file} did not exist to be deleted.")
        
        rename(self.log_file, self.second_log_file)
    
    def read_logs(self) -> str:
        """ 
        Read both log files and return their contents as a single string.
        """
        logs = ""
        try:
            with open(self.second_log_file, "r") as log_file:
                logs += log_file.read()
        except OSError:
            pass
        
        try:
            with open(self.log_file, "r") as log_file:
                logs += log_file.read()
        except OSError:
            pass
        
        return logs
    