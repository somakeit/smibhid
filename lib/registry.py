class DriverRegistry:
    """
    Object for driver modules to register, so code can look up a driver class from the driver name.
    Driver modules should import driver_registry and call register_driver to map the driver class object to the driver name.
    Example: driver_registry.register_driver("LCD1602", LCD1602).
    Calling code imports driver_registry and uses get_register_class to obtain the class to create a new driver object.
    Example: driver_class = driver_registry.get_driver_class("LCD1602")
    """
    def __init__(self):
        self._registry = {}

    def register_driver(self, driver_name: str, driver_class):
        self._registry[driver_name] = driver_class

    def get_driver_class(self, driver_name: str):
        return self._registry.get(driver_name)
    
driver_registry = DriverRegistry()