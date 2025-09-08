from fastapi import APIRouter
from .models import version_responses, hostname_responses, wlan_mac_responses, reset_responses


system_router = APIRouter(tags=["System"])

@system_router.get(
    "/version",
    name="Get SMIBHID Firmware Version",
    response_model=str,
    responses=version_responses,
)
async def get_version() -> str:
    """ Returns the firmware_files version of the SMIBHID device """
    ...

@system_router.get(
    "/hostname",
    name="Get SMIBHID Hostname",
    response_model=str,
    responses=hostname_responses,
)
async def get_hostname() -> str:
    """ Returns the hostname of the SMIBHID device """
    ...

@system_router.get(
    "/wlan/mac",
    name="Get SMIBHID WLAN MAC Address",
    response_model=str,
    responses=wlan_mac_responses,
)
async def get_wlan_mac() -> str:
    """ Returns the WLAN MAC address of the SMIBHID device """
    ...

@system_router.post('/reset', summary="Reset SMIBHID Device",
                 description="Resets the SMIBHID device - **request will hang and timeout**",
                 responses=reset_responses, tags=["Firmware Files"])
async def reset() -> None:
    """ Resets the SMIBHID device """
    ...