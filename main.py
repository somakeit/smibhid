"""
Main file for the SMIB HID pico code. This file is responsible for starting the
HID class and running.
"""
# Built against Pico W Micropython firmware v1.22.2 https://micropython.org/download/RPI_PICO_W/

from lib.hid import HID

hid = HID()
hid.startup()
