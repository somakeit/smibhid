## Logging
# Level 0-4: 0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info
LOG_LEVEL = 2
# Handlers: Populate list with zero or more of the following log output handlers (case sensitive): "Console", "File"
LOG_HANDLERS = ["Console", "File"]
LOG_FILE_MAX_SIZE = 10240

## IO
SPACE_OPEN_BUTTON = 12
SPACE_CLOSED_BUTTON = 13
SPACE_OPEN_LED = 15
SPACE_CLOSED_LED = 16

## WIFI
WIFI_SSID = ""
WIFI_PASSWORD = ""
WIFI_COUNTRY = "GB"
WIFI_CONNECT_TIMEOUT_SECONDS = 10
WIFI_CONNECT_RETRIES = 1
WIFI_RETRY_BACKOFF_SECONDS = 5

## Web host
WEBSERVER_HOST = ""
WEBSERVER_PORT = "80"

## Space state
# Set the space state poll frequency in seconds (>= 5), set to 0 to disable the state poll
space_state_poll_frequency_s = 5

## I2C
SDA_PIN = 8
SCL_PIN = 9
I2C_ID = 0