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

## Circuit diagram
### Pico W Connections
![Circuit diagram](images/SMIBHID%20circuit%20diagram.drawio.png)

### Pico W pinout
![Pico W pinout](images/pico_w_pinout.png)

### Example breadboard build
![Breadboard photo](images/breadboard.jpg)

## Deployment
Copy the files from the smibhib folder into the root of a Pico W running Micropython and update values in config.py as necessary
### Configuration
- Ensure the pins for the space open/closed LEDs and buttons are correctly specified for your wiring
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
SMIB uses a class abstracted approach running an async loop using the builtin uasyncio, a static copy of the uaiohttpclient for making async requests and my custom logging module.

### Logging
Set the loglevel argument for the HID object in \_\_main\_\_.py for global log level output where: 0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info

### Adding functionality
Refer to the [S.M.I.B. contribution guidelines](https://github.com/somakeit/S.M.I.B./contribute) for more info on contributing.

Use existing space state buttons, lights, slack APi wrapper and watchers as an example for how to implement:
- Create or use an existing (such as button) appropriate module and class with coroutine to watch for input or other appropriate event
- In the HID class
  - Instantiate the object instance, passing an asyncio event to the watcher and add the watcher coroutine to the loop
  - Configure another coroutine to watch for the event and take appropriate action on event firing
  - Add new API endpoint methods as needed as the API is upgraded to support them