import gc

class uLogger:
    
    def __init__(self, module_name: str, log_level: int = 0) -> None:
        """
        Init with module name to log and session debug level, that defaults to 2 and can be overidden globally using log_level=x in config.py
        Raise a debug message using the appropriate function for the severity
        Debug level 0-3: Each level adds more verbosity
        0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info
        """
        self.module_name = module_name
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

    def info(self, message) -> None:
        if self.log_level > 3:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][Info][{self.module_name}]: {message}") 

    def warn(self, message) -> None:
        if self.log_level > 2:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][Warning][{self.module_name}]: {message}")

    def error(self, message) -> None:
        if self.log_level > 1:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][*Error*][{self.module_name}]: {message}")

    def critical(self, message) -> None:
        if self.log_level > 0:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][!Critical!][{self.module_name}]: {message}")