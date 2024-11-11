from lib.ulogging import uLogger
import os
import machine

class Updater:
    def __init__(self) -> None:
        self.log = uLogger("Updater")
        self.update_path = "/updates/"

    def apply_files(self) -> bool:
        """
        Update SMIBHID with new files from /updates/ directory.
        """
        self.log.info("Updating HID")

        try:
            for file_name in os.listdir(self.update_path):
                self.log.info(f"Updating {file_name}")
                update_path = self.update_path + file_name
                target_path = "/lib/" + file_name
                self.log.info(f"Moving {update_path} to {target_path}")
                os.rename(update_path, target_path)
                self.log.info(f"Updated {file_name}")
            self.log.info("All HID files updated successfully, restart required")
            return True
        except Exception as e:
            self.log.error(f"Failed to update HID: {e}")
            return False
    
    def reset(self) -> None:
        """
        Restart the device.
        """
        self.log.info("Restarting device")
        machine.reset()