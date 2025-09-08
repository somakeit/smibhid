from fastapi import APIRouter

from .models import ModuleName, Sensor, SensorDataMap

sensors_router = APIRouter(prefix="/sensors", tags=["Sensors"])

@sensors_router.get("/modules")
async def get_modules() -> list[ModuleName]:
    """ Returns a list of modules that are currently configured on the SMIBHID device"""
    ...

@sensors_router.get("/modules/{module}")
def get_sensor_modules(module: ModuleName) -> list[Sensor]:
    """ Returns a list of sensors for the given module """
    ...

@sensors_router.get("/readings/latest")
def get_latest_sensor_readings() -> SensorDataMap:
    """ Returns the latest sensor readings for all modules """
    ...
