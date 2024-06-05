# SMIBHID
## Overview
SMIBHID is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device run on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Space_open and space_closed LEDs show current state as set on the S.M.I.B. slack server. If the space_state is set to None on the server i.e. no state has been specifically set, then both LEDs will be off.

Press the space_open or space_closed buttons to call the smib server endpoint appropriately. The target state LED will flash to show it's attempting to communicate and confirm successful state update to provide feedback to the user. In normal operation the request should complete and update the LED in a couple of seconds.

## Features
- Space open and closed buttons with LED feedback that calls the S.M.I.B. space_open/space_closed endpoint
- LED flashes while trying to set state so you know it's trying to do something
- Confirms the space state after change by calling space_state
- Regularly polls for space state (polling period configurable in config.py) and updates the SMIBHID status appropriately to sync with other space state controls
- Flashes both space state LEDs at 2Hz if space state cannot be determined
- 2x16 character LCD display support

## Circuit diagram
### Pico W Connections
![Circuit diagram](images/SMIBHID%20circuit%20diagram.drawio.png)

### Pico W pinout
![Pico W pinout](images/pico_w_pinout.png)

### Example breadboard build
![Breadboard photo](images/breadboard.jpg)

### Example prototype build


## Hardware
Below is a list of hardware ad links for my specific build:
- [Raspberry Pi Pico W](https://thepihut.com/products/raspberry-pi-pico-w?variant=41952994754755)
- [Prototype board](https://thepihut.com/products/pico-proto-pcb?variant=41359085568195)
- [LED push button switch - Red](https://thepihut.com/products/rugged-metal-pushbutton-with-red-led-ring?variant=27740444561)
- [LED push button switch - Green](https://thepihut.com/products/rugged-metal-pushbutton-with-green-led-ring?variant=27740444625)
- [JST connectors](https://www.amazon.co.uk/dp/B07449V33P)
- [2x16 Character I2C display](https://thepihut.com/products/lcd1602-i2c-module?variant=42422810083523)

## Deployment
Copy the files from the smibhib folder into the root of a Pico W running Micropython and update values in config.py as necessary
### Configuration
- Ensure the pins for the space open/closed LEDs and buttons are correctly specified for your wiring
- Configure I2C pins for the display if using, display will detect automatically or disable if not found
- Populate Wifi SSID and password
- Configure the webserver hostname/IP and port as per your smib.webserver configuration
- Set the space state poll frequency in seconds (>= 5), set to 0 to disable the state poll

## Onboard status LED
The LED on the Pico W board is used to give feedback around network connectivity if you are not able to connect to the terminal output for logs.
* 1 flash at 2 Hz: successful connection
* 2 flashes at 2 Hz: failed connection
* Constant 4Hz flash: in backoff period before retrying connection
* No LED output: normal operation

## Developers
SMIB uses a class abstracted approach running an async loop using the built in asyncio library, a static copy of the uaiohttpclient for making async requests and my custom logging module.

### Logging

#### Log level
Set the LOG_LEVEL value in config.py for global log level output configuration where: 0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info

Example: `LOG_LEVEL = 2`

#### Handlers
Populate the LOG_HANDLERS list in config.py with zero or more of the following log output handlers (case sensitive): "Console", "File"

Example: `LOG_HANDLERS = ["Console", "File"]`

#### Log file max size
Set the LOG_FILE_MAX_SIZE value in config.py to set the maximum size of the log file in bytes before rotating. The log rotater will create a maximum of 2 files at this size, so configure appropiately for anticpated flash free space.

Example: `LOG_FILE_MAX_SIZE = 10240`

### Adding functionality
Refer to the [S.M.I.B. contribution guidelines](https://github.com/somakeit/S.M.I.B./contribute) for more info on contributing.

Use existing space state buttons, lights, slack API wrapper and watchers as an example for how to implement:
- Create or use an existing (such as button) appropriate module and class with coroutine to watch for input or other appropriate event
- In the HID class
  - Instantiate the object instance, passing an asyncio event to the watcher and add the watcher coroutine to the loop
  - Configure another coroutine to watch for the event and take appropriate action on event firing
  - Add new API endpoint methods as needed as the API is upgraded to support them
- Display drivers can be added by creating a new display driver module
  - Ensure the driver registers itself with the driver registry, use LCD1602 as an example
  - Import the new driver module in display.py
  - Update the config.py file to cinlude the option for your new driver 

## Version
Ensure that the `HID` class version attribute is updated to match the version in `pyproject.toml`

> [!IMPORTANT]
> This version needs to match the release when it goes into the `master` branch.
