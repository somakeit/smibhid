## Logging
# Level 0-4: 0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info
LOG_LEVEL = 2
# Handlers: Populate list with zero or more of the following log output handlers (case sensitive): "Console", "File"
LOG_HANDLERS = ["Console", "File"]
# Max log file size in bytes, there will be a maximum of 2 files at this size created
LOG_FILE_MAX_SIZE = 10240

## IO
SPACE_OPEN_BUTTON = 12
SPACE_CLOSED_BUTTON = 13
SPACE_OPEN_LED = 15
SPACE_CLOSED_LED = 16
# Set to None if no relay/transistor is connected
SPACE_OPEN_RELAY = None
SPACE_OPEN_RELAY_ACTIVE_HIGH = True

## WIFI
WIFI_SSID = ""
WIFI_PASSWORD = ""
WIFI_COUNTRY = "GB"
WIFI_CONNECT_TIMEOUT_SECONDS = 10
WIFI_CONNECT_RETRIES = 1
WIFI_RETRY_BACKOFF_SECONDS = 5
# Leave as none for MAC based unique hostname or specify a custom hostname string
CUSTOM_HOSTNAME = None

NTP_SYNC_INTERVAL_SECONDS = 86400

## Web host
WEBSERVER_HOST = ""
WEBSERVER_PORT = "80"

## Space state
# Set the space state poll frequency in seconds (>= 5), set to 0 to disable the state poll
space_state_poll_frequency_s = 5
# How long to wait for button press to accept extra hours when opening space
ADD_HOURS_INPUT_TIMEOUT = 3

## I2C
SDA_PIN = 8
SCL_PIN = 9
I2C_ID = 0

## Displays - Populate driver list with connected displays from this supported list: ["LCD1602"]
DISPLAY_DRIVERS = ["LCD1602"]
# Scroll speed for text on displays in characters per second
SCROLL_SPEED = 4

## RFID reader
RFID_ENABLED = False
RFID_SCK = 18
RFID_MOSI = 19
RFID_MISO = 16
RFID_RST = 21
RFID_CS = 17

ENABLE_UI_LOGGING_UPLOAD = False
