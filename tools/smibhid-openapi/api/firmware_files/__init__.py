from .models import FirmwareFilesRequest
from fastapi import APIRouter

firmware_files_router = APIRouter(tags=["System", "Firmware Files"])

@firmware_files_router.get('/firmware_files')
def get_firmware_files() -> list[str]:
    """ Returns a list of firmware files that are staged for update """
    ...

@firmware_files_router.post('/firmware_files')
async def update_firmware_files(body: FirmwareFilesRequest) -> bool:
    """ Adds or removes the firmware files in the firmware_files list """
    ...

# TODO - Should there be a be a delete method (not in the post)?



