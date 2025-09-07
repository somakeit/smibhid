from fastapi import APIRouter
from .models import version_responses, hostname_responses, wlan_mac_responses

api_router = APIRouter(prefix="/api", tags=["System"])

# To get nice documentation:
#   We have to do it this nasty way as the response is just a string, not a json object.
@api_router.get(
    "/version",
    name="Get SMIBHID Firmware Version",
    response_model=str,
    responses=version_responses,
)
async def get_version() -> str:
    """ Returns the firmware version of the SMIBHID device """
    ...

@api_router.get(
    "/hostname",
    name="Get SMIBHID Hostname",
    response_model=str,
    responses=hostname_responses,
)
async def get_hostname() -> str:
    """ Returns the hostname of the SMIBHID device """
    ...

@api_router.get(
    "/wlan/mac",
    name="Get SMIBHID WLAN MAC Address",
    response_model=str,
    responses=wlan_mac_responses,
)
async def get_wlan_mac() -> str:
    """ Returns the WLAN MAC address of the SMIBHID device """
    ...

@api_router.post('/reset', summary="Reset SMIBHID Device")
async def reset() -> None:
    """ Resets the SMIBHID device """
    ...




