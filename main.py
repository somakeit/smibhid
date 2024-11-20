"""
Main file for the SMIB HID pico code. This file is responsible for starting the
HID class and running.
"""
# Built against Pico W Micropython firmware v1.22.2 https://micropython.org/download/RPI_PICO_W/

from os import listdir

updates_dir_list = listdir("/updates/")
if ".updating" in updates_dir_list:
    from lib.updater import Updater
    updater = Updater()
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
