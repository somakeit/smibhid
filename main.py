# Built against Pico W Micropython firmware v1.22.2 https://micropython.org/download/RPI_PICO_W/

from lib.hid import HID

hid = HID()
hid.startup()