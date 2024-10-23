from ulogging import uLogger
import lib.config.config_template as config_template
import config

class ConfigManagement:
    """
    Ensure config file contains all items in config_template and that the values are of the correct type.
    Apply defaults from config_template where values are missing in config.
    """
    def __init__(self) -> None:
        self.log = uLogger("ConfigManagement")
        self.error_count = 0
    
    def configure_error_handling(self) -> None:
        """
        Register errors with the error handler for the configuration management module.
        """
        from lib.error_handling import ErrorHandler
        self.error_handler = ErrorHandler("ConfigManagement")
        self.errors = {
            "CFG": "Config errors found, check logs"
        }

        for error_key, error_message in self.errors.items():
            self.error_handler.register_error(error_key, error_message)
        
        return
        
    def check_config(self) -> int:
        self.log.info("Checking config file")
        
        for key in dir(config_template):
            if not hasattr(config, key):
                self.log.error(f"Missing config item in config.py: {key}, setting default value: {getattr(config_template, key)}")
                setattr(config, key, getattr(config_template, key))
                self.error_count += 1
            else:
                if not isinstance(getattr(config, key), type(getattr(config_template, key))) and getattr(config_template, key) is not None:
                    self.log.error(f"Config item in config.py has incorrect type: {key}")
                    setattr(config, key, getattr(config_template, key))
                    self.error_count += 1
        
        self.log.info(f"Config file check complete. Errors encountered: {self.error_count}")
        
        if self.error_count > 0:
            self.log.error("Please correct the above errors in config.py and restart SMIBHID")
            return -1
        
        return 0
    
    def enable_error(self) -> None:
        self.error_handler.enable_error("CFG")
        
        return
