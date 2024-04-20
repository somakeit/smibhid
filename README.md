# SMIBHID

## Overview
SMIBHID is the So Make It Bot Human Interface Device and definitely not a mispronunciation of any insults from a popular 90s documentary detailing the activites of the Jupiter Mining Core.

This device run on a Raspberry Pi Pico W and provides physical input and output to humans for the SMIB project; Buttons, LEDs, that sort of thing.

## Features
- Space open and closed buttons with LED feedback that calls the SMIB space_open endpoint

## Circuit diagram
![Circuit diagram](images/SMIBHID%20circuit%20diagram.drawio.png)

## Developers
SMIB uses a class abstracted approach running an async loop using the builtin uasyncio, a static copy of the uaiohttpclient for making async requests and my custom logging module.

### Logging
Set the loglevel argument for the HID object in \_\_main\_\_.py for global log level output where: 0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info

### Adding functionality
Refer to existing space state buttons, lights and watchers as an example for how to implement:
- Create or use an existing (such as button) appropriate module and class with coroutine to watch for input or other appropriate event
- In the HID class
  - instantiate the object instance, passing an asyncio event to the watcher and add the watcher coroutine to the loop
  - Configure another coroutine to watch for the event and take appropriate action on event firing