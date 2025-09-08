from fastapi import APIRouter
from .system import system_router
from .firmware_files import firmware_files_router
from .sensors import sensors_router

api_router = APIRouter(prefix="/api")
api_router.include_router(system_router)
api_router.include_router(firmware_files_router)
api_router.include_router(sensors_router)





