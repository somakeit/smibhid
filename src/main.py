"""
Main file for the SMIB HID pico code. This file is responsible for starting the
HID class and running.
"""
from os import listdir

updates_dir_list = []
try:
    updates_dir_list = listdir("/updates/")
except Exception:
    pass
if ".updating" in updates_dir_list:
    from lib.updater import Updater
    from machine import I2C
    from config import SDA_PIN, SCL_PIN, I2C_ID, I2C_FREQ
    i2c = I2C(I2C_ID, sda = SDA_PIN, scl = SCL_PIN, freq = I2C_FREQ)
    updater = Updater(i2c)
    updater.enter_update_mode()

else:
    from lib.config.config_management import ConfigManagement
    config_management = ConfigManagement()
    config_errors = config_management.check_config()
    
    from lib.hid import HID

    hid = HID()
    if config_errors < 0:
        config_management.configure_error_handling()
        config_management.enable_error()
    hid.startup()
