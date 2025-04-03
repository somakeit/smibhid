from lib.display import Display
from lib.ulogging import uLogger

class ErrorHandler:
    """
    Register a module for error handling and provide methods for registering, enabling, disabling, and getting error messages.
    If a display is available, ensure your display handling module registers the display instance with the error handler using configure_display().
    The error handler will then ensure the display update status method is called when errors are enabled or disabled, passing in all enabled errors.
    """
    
    error_handler_registry = {}

    @classmethod
    def register_error_handler(cls, error_handler_name: str, error_handler_instance) -> None:
        cls.error_handler_registry[error_handler_name] = error_handler_instance

    @classmethod
    def get_error_handler_class(cls, error_handler_name: str) -> None:
        return cls.error_handler_registry.get(error_handler_name)
    
    @classmethod
    def configure_display(cls, display: Display) -> None:
        cls.display = display

    @classmethod
    def update_errors_on_display(cls) -> None:
        errors = []
        for error_handler in cls.error_handler_registry:
            errors.extend(cls.error_handler_registry[error_handler].get_all_errors())
        cls.display.update_errors(errors)

    def __init__(self, module_name: str) -> None:
        """Creates a new error handler instance for a module and registers it with the error handler registry."""
        self.log = uLogger(f"ErrorHandling - {module_name}")
        self.errors = {}
        self.register_error_handler(module_name, self)
        
    def register_error(self, key: str, message: str):
        """Register a new error with its key, message, and enabled status."""
        if key not in self.errors:
            self.errors[key] = {'message': message, 'enabled': False}
            self.log.info(f"Registered error '{key}' with message '{message}'")
        else:
            raise ValueError(f"Error key '{key}' already registered.")

    def enable_error(self, key: str):
        """Enable an error."""
        if key in self.errors:
            self.errors[key]['enabled'] = True
            self.log.info(f"Enabled error '{key}'")
            if hasattr(self, 'display'):
                self.update_errors_on_display()
        else:
            raise ValueError(f"Error key '{key}' not registered.")

    def disable_error(self, key: str):
        """Disable an error."""
        if key in self.errors:
            self.errors[key]['enabled'] = False
            self.log.info(f"Disabled error '{key}'")
            self.update_errors_on_display()
        else:
            raise ValueError(f"Error key '{key}' not registered.")

    def get_error_message(self, key: str) -> str:
        """Get the error message for a given key."""
        if key in self.errors:
            return self.errors[key]['message']
        else:
            raise ValueError(f"Error key '{key}' not registered.")

    def is_error_enabled(self, key: str) -> bool:
        """Check if an error is enabled."""
        if key in self.errors:
            return self.errors[key]['enabled']
        else:
            raise ValueError(f"Error key '{key}' not registered.")
    
    def get_all_errors(self) -> list:
        """Return a list of all enabled errors."""
        errors = []
        for error in self.errors:
            if self.errors[error]['enabled']:
                errors.append(self.errors[error]['message'])
        return errors
        