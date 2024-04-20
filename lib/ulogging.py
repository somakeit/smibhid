import gc

class uLogger:
    
    def __init__(self, module_name: str, debug_level: int) -> None:
        """
        Init with module name to log and session debug level
        Raise a debug message using the appropriate function for the severity
        Debug level 0-3: Each level adds more verbosity
        0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info
        """
        self.module_name = module_name
        self.debug_level = debug_level

    def info(self, message) -> None:
        if self.debug_level > 3:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][Info][{self.module_name}]: {message}") 

    def warn(self, message) -> None:
        if self.debug_level > 2:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][Warning][{self.module_name}]: {message}")

    def error(self, message) -> None:
        if self.debug_level > 1:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][*Error*][{self.module_name}]: {message}")

    def critical(self, message) -> None:
        if self.debug_level > 0:
            print(f"[Mem: {round(gc.mem_free() / 1024)}kB free][!Critical!][{self.module_name}]: {message}")