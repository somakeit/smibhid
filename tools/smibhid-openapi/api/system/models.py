version_responses = {
    200: {
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "title": "SMIBHID Firmware Version",
                    "example": "2.0.0",
                }
            }
        }
    }
}

hostname_responses = {
    200: {
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "title": "SMIBHID Hostname",
                    "example": "smibhid-fan",
                }
            }
        }
    }
}

wlan_mac_responses = {
    200: {
        "content": {
            "application/json": {
                "schema": {
                    "type": "string",
                    "title": "SMIBHID WLAN MAC Address",
                    "example": "1A:2B:3C:4D:5E:6F",
                }
            }
        }
    }
}

# TODO - RESET Does not currently return anything
reset_responses = {}