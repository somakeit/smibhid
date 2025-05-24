# SMIBHID
## Overview
SMIBHID is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activities of the Jupiter Mining Core.

This device run on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

Space_open and space_closed LEDs show current state as set on the S.M.I.B. slack server. If the space_state is set to None on the server i.e. no state has been specifically set, then both LEDs will be off.

Press the space_open or space_closed buttons to call the smib server endpoint appropriately. The target state LED will flash to show it's attempting to communicate and confirm successful state update to provide feedback to the user. In normal operation the request should complete and update the LED in a couple of seconds.

## Features
- Space open and closed buttons with LED feedback that calls the S.M.I.B. space_open/space_closed endpoint
- Press the open button multiple times to set the number of hours the space will be open for
- LED flashes while trying to set state so you know it's trying to do something
- Confirms the space state after change by calling space_state
- Regularly polls for space state (polling period configurable in config.py) and updates the SMIBHID status appropriately to sync with other space state controls
- Flashes both space state LEDs at 2Hz if space state cannot be determined
- 2x16 character I2C LCD display support (Space state)
- 32x128 I2C OLED display support (Sensors)
- Error information shown on connected displays where configured in modules using ErrorHandler class
- UI Logger captures timestamps of button presses and uploads to SMIB for logging and review of usage patterns
- Space open relay pin optionally sets a GPIO to high or low when the space is open
- Config file checker against config template - useful for upgrades missing config of new features
- Over the air firmware updates - Web based management and display output on status
- Web server for admin functions (Check info log messages or DHCP server for IP and default port is 80)
  - Home page with list of available functions
  - API page that details API endpoints available and their usage
  - Update page for performing over the air firmware updates and remote reset to apply them
- Pinger watchdog - Optionally ping an IP address and toggle a GPIO pin on ping failure. Useful for network device monitoring and reset.
- Extensible sensor module framework for async polling of I2C sensors and presentation of sensors and readings on the web API and recording to log file
  - Supported sensors
    - SGP30 (Equivalent CO2 and VOC)
    - BME280
    - SCD30
  - Calibration of the SCD30 CO2 sensor via the API or web admin console
  - CO2 alarm where SCD30 module present

### Sensors
SMIBHID can be used for environmental monitoring. At present only I2C sensors are supported, although the framework could be easily extended to accept other connectivity into the driver framework.

Once the sensors are configured they will poll at a regular interval and store to log files if configured.

Future intent is to have the sensor data pushed to SMIB at each poll and only cache data that has yet to be pushed as even the Pico 2 has RAM limitations that prevent processing of large data files easily.

The API allows querying of the sensors in realtime and SMIB has a slack command to query the sensors and report that realtime data back to the slack channel via the "/howfresh" command.

The SGP30 CO2 sensor needs calibration from time to time and this can be achieved by posting the current CO2 level as measured by a reference sensor to the calibration API endpoint or by using the sensors web management page. Full instructions are available by following links from the main admin web page at http://<smibhid IP>:80

The SGP30 module also allows configuration of a buzzer and LED alarm. On each poll (once per minute), the LED and alarm buzzer will trigger at the PPM threshold (configurable) in the config file and will remain triggered until the level drops below the reset threshold (configurable). A snooze button is provided to silence the audible alarm for 5 minutes (configurable) while an open window lowers the measured PPM, but the alarm LED will remain lit while the reset threshold is exceeded.

The CO2 reading can be output onto the 32x128 OLED display if attached. There is a 5 second auto off on the OLED display to prevent pixel burnout/in. The snooze button becomes a screen wake button if the screen is fitted and powered off and snooze on a subsequent press while the screen is powered on.

## Circuit diagram
### Pico W Connections
![Circuit diagram](images/SMIBHID%20circuit%20diagram.drawio.png)

### Pico 2 W pinout
![Pico 2 W pinout](images/pico_2_w_pinout.png)

### Example breadboard build
![Breadboard photo](images/breadboard.jpg)

## Hardware
Below is a list of hardware and links for my specific build:
- [Raspberry Pi Pico W](https://thepihut.com/products/raspberry-pi-pico-w?variant=41952994754755)
- [Prototype board](https://thepihut.com/products/pico-proto-pcb?variant=41359085568195)
- [LED push button switch - Red](https://thepihut.com/products/rugged-metal-pushbutton-with-red-led-ring?variant=27740444561)
- [LED push button switch - Green](https://thepihut.com/products/rugged-metal-pushbutton-with-green-led-ring?variant=27740444625)
- [JST connectors](https://www.amazon.co.uk/dp/B07449V33P)
- [2x16 Character I2C display](https://thepihut.com/products/lcd1602-i2c-module?variant=42422810083523)
- [Monochrome 0.91" 128x32 I2C OLED Display](https://shop.pimoroni.com/products/monochrome-0-91-128x32-i2c-oled-display-stemma-qt-qwiic-compatible?variant=31209617784915)
- [4 Pin JST-SH Cable (Qwiic, STEMMA QT, Qw/ST)](https://shop.pimoroni.com/products/jst-sh-cable-qwiic-stemma-qt-compatible?variant=40407104290899)
- [SGP30 I2C sensor](https://thepihut.com/products/sgp30-air-quality-sensor-breakout)
- [BME280 sensor](https://thepihut.com/products/bme280-breakout-temperature-pressure-humidity-sensor)
- [SCD30 sensor](https://thepihut.com/products/adafruit-scd-30-ndir-co2-temperature-and-humidity-sensor)
- [Buzzer](https://shop.pimoroni.com/products/mini-active-buzzer?variant=40257468694611)

## Deployment
Copy the files from the smibhib folder into the root of a Pico 2 W running Micropython (minimum Pico 2 W Micropython firmware v1.25.0-preview.365 https://micropython.org/download/RPI_PICO2_W/) and update values in config.py as necessary.

This project should work on a Pico W on recent firmware, but we have moved development, testing and our production SMIBHIDs to Pico 2 Ws.

### Configuration
- See the log level section below for logging config
- Ensure the pins for the space open/closed LEDs and buttons are correctly specified for your wiring
- Configure the space open relay pin if required or else set to None, also choose if space open sets pin high or low
- Populate Wifi SSID and password
- Configure the pinger watchdog and associated pin (example relay with transistor for coil current provided in circuit diagram)
- Configure the webserver hostname/IP and port as per your smib.webserver configuration
- Set the space state poll frequency in seconds (>= 5), set to 0 to disable the state poll
- Configure I2C pins for the display and sensors if using, display will detect automatically or disable if not found
- Populate the sensors list with sensors in use (must have appropriate driver module)
  - Configure sensor log file caching if required
  - If SGP30 present, configure optional CO2 alarm thresholds and buzzer, LED and snooze button pins
- Populate the display list with displays in use (must have appropriate driver module)
- Enable UI logging if required
- Adjust the overclocking value if needed, although maximum safe values are defaulted. The standard frequency for maximum stability is 133000000 and 150000000 for pico and pico 2 respectively

If you miss any configuration options, a default will be applied, an error output in the log detailing the configuration item missed including the default value configured and if connected, an error displayed on displays.

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

#### Log Handlers
Populate the LOG_HANDLERS list in config.py with zero or more of the following log output handlers (case sensitive): "Console", "File"

Example: `LOG_HANDLERS = ["Console", "File"]`

#### Log file max size
Set the LOG_FILE_MAX_SIZE value in config.py to set the maximum size of the log file in bytes before rotating. The log rotator will create a maximum of 2 files at this size, so configure appropriately for anticipated flash free space.

Example: `LOG_FILE_MAX_SIZE = 10240`

### Error handling
Create a new instance of the ErrorHandling class in a module to register a list of possible errors for that module and enable or disable them for display on connected screens using class methods. See the space state module for an example of implementation.

### Adding functionality
Refer to the [SMIBHID contribution guidelines](https://github.com/somakeit/smibhid/contribute) for more info on contributing.

Use existing space state buttons, lights, slack API wrapper and watchers as an example for how to implement:
- Create or use an existing (such as button) appropriate module and class with coroutine to watch for input or other appropriate event
- In the HID class
  - Instantiate the object instance, passing an asyncio event to the watcher and add the watcher coroutine to the loop
  - Configure another coroutine to watch for the event and take appropriate action on event firing
  - Add new API endpoint methods as needed as the API is upgraded to support them
- Display drivers can be added by creating a new display driver module
  - Ensure the driver registers itself with the driver registry, use LCD1602 as an example
  - Import the new driver module in display.py
  - Update the config.py file to include the option for your new driver
- I2C Sensor boards can be added by providing a driver module that extends the SensorModule base class
  - Copy an appropriate python driver module into the sensors sub folder
  - Ensure the init method takes one mandatory parameter for the I2C interface
  - Modify the driver module to extend SensorModule
  - Provide a list of sensor names on this module to class super init
  - Ensure the init method raises an error if device not found or has any configuration error to be caught by the sensors module driver load method
  - Overload the get_reading() method to return a dictionary of sensor name - reading value pairs
  - Update the config.py file to include the option for your new driver
  - Add the module import to sensors.\_\_init\_\_.py
  - Copy and adjust appropriately the try except block in sensors.\_\_init\_\_.load_modules method
- UIState machine
  - A state machine exists and can be extended by various modules such as space_state to manage the state of the buttons and display output
  - The current state instance is held in hid.ui_state_instance
  - Enter a new UI state by calling the transition_to() method on a UIstate instance and pass any arguments needed by that state
  - You will need to pass any core objects needed by the base UIState class and apply using super() as normal. These are currently HID (for managing the current state instance) and SpaceState so that the open and close buttons are available in all UIs with default space open/closed behaviour.

#### Config template update
If you add a new feature that has configuration options, ensure you set the constant and default value in the config.py file as well as in the config.config_template.py file to allow automated checking of config files to catch upgrade error and misconfigurations.

### Web server
The admin web interface is hosted by a customised version of [tinyweb](https://github.com/belyalov/tinyweb) server which is a flask like implementation of a asyncio web server in MicroPython.
The website configuration and API definition is built out from the website.py module and all HTML/CSS/JS etc lives in the www subfolder.

### OTA firmware updates
- Load the admin web page and navigate to /update
- Add files to update
  - Enter a URL to download the raw python file that will be moved into the lib folder overwriting any existing files with that name (Best approach is reference the raw file version on a github branch)
  - Press "Add"
  - Repeat above as needed until all files are staged
  - Select a file and press "Remove" to remove a URL if not needed or to correct an error and re-add the URL
  - When all files are staged ready to update, press "Restart" to reboot SMIBHID
  - Display will show update status and result before restarting into normal mode with the new firmware

If any files are staged (.updating file exists in updates folder on the device) SMIBHID will reboot into update mode, download, copy over, then clear out the staging directory and restart again.

If errors are encountered such as no wifi on the update process, the staging file is deleted and SMIBHID will reboot back into normal mode.

### UI State diagram
The space state UI state machine is described in this diagram:

![Space state UI state machine diagram](images/SMIBHID_UI_state_diagram.drawio.png)
