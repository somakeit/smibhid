from lib.ulogging import uLogger
import os
import machine
import requests
from gc import collect
from lib.networking import WirelessNetwork
from asyncio import run
from lib.display import Display
from time import sleep

class UpdateCore:
    def __init__(self) -> None:
        self.log = uLogger("UpdateCore")
        self.update_path = "/updates"
        self.check_for_updates_folder()

    def check_for_updates_folder(self) -> bool:
        """
        Check if the /updates/ directory exists.
        """
        self.log.info("Checking for updates folder")
        try:
            if self.update_path.strip('/') not in os.listdir('/'):
                self.log.info("Updates folder does not exist - creating")
                os.mkdir(self.update_path)
                self.log.info("Updates folder created")
            else:
                self.log.info("Updates folder exists")
            return True
        except Exception as e:
            self.log.error(f"Failed to check for updates folder: {e}")
            return False

    def stage_update_url(self, url: str) -> bool:
        """
        Stage an update file.
        """
        self.log.info(f"Staging update file: {url}")
        try:
            with open(self.update_path + "/.updating", "a") as f:
                f.write(url + "\n")
            self.log.info("Update file staged")
            return True
        except Exception as e:
            self.log.error(f"Failed to stage update file: {e}")
            return False
        
    def unstage_update_url(self, url: str) -> bool:
        """
        Unstage an update file.
        """
        self.log.info(f"Unstaging update file: {url}")
        try:
            with open(self.update_path + "/.updating", "r") as f:
                update_data = f.read()
            with open(self.update_path + "/.updating", "w") as f:
                line_count = 0
                for update in update_data.split("\n"):
                    if update != url and update != "":
                        line_count += 1
                        f.write(update + "\n")
            self.log.info("Update file unstaged")
            if line_count == 0:
                os.remove(self.update_path + "/.updating")
                self.log.info("No updates staged - removing update file")
            return True
        except Exception as e:
            self.log.error(f"Failed to unstage update file: {e}")
            return False
    
    def process_update_file(self) -> list:
        """
        Process updates.
        """
        self.log.info("Processing updates")
        urls = []
        try:
            with open(self.update_path + "/.updating", "r") as f:
                update_data = f.read()
            self.log.info(f"Update data: {update_data}")
            
            for update in update_data.split("\n"):
                if update != "":
                    urls.append(update)
            self.log.info(f"URLs: {urls}")
        
        except Exception as e:
            self.log.error(f"Failed to process updates: {e}")
        
        finally:
            return urls
    
    def reset(self) -> None:
        """
        Restart the device.
        """
        self.log.info("Restarting device")
        machine.reset()

class Updater(UpdateCore):
    def __init__(self, i2c) -> None:
        super().__init__()
        self.log = uLogger("Updater")
        self.display = Display(i2c)

    def enter_update_mode(self) -> bool:
        """
        Enter update mode.
        """
        self.log.info("Entering update mode")
        self.display.clear()
        self.display.print_update_startup()
        wifi_connected = self.connect_wifi()
        
        if not wifi_connected:
            self.log.warn("No network access - update mode failed")
            self.exit_with_failure()
            return False
        
        else:
            self.log.info("Network access - applying updates")
            try:
                urls = self.process_update_file()
            
                if len(urls) == 0:
                    self.log.warn("No updates to apply")
                    self.exit_with_failure()
                    return False
                
                current_file = 0
                
                for url in urls:
                    current_file += 1
                    self.display.print_download_progress(current_file, len(urls))
                    self.download_file(url)
                
                self.apply_files()
                self.exit_with_success()
                return True
            
            except Exception as e:
                self.log.error(f"Failed to apply updates: {e}")
                self.exit_with_failure()
                return False

    def exit_with_success(self) -> None:
        """
        Clears update flag and reboots into normal run state.
        """
        self.log.info("Updates applied successfully - clearing update flag to reboot into normal mode")
        try:
            os.remove(self.update_path + "/.updating")
        except Exception as e:
            self.log.warn(f"Unable to delete .updating file, may already be removed - this is unusual, but not fatal: {e}")
        self.display.clear()
        self.display.print_update_status("Success")
        sleep(2)
        self.reset()
    
    def exit_with_failure(self) -> None:
        """
        Clears update flag and restores backups if present to reboot into best
        known normal run state.
        """
        self.log.error("Cannot apply updates - future code will revert to backed up files - clearing update flag to reboot into normal mode")
        os.remove(self.update_path + "/.updating")
        self.display.clear()
        self.display.print_update_status("Failed")
        sleep(2)
        self.reset()
    
    def connect_wifi(self) -> bool:
        """
        Connect to wifi.
        """
        self.log.info("Connecting to wifi")
        self.wifi = WirelessNetwork()
        self.wifi.configure_wifi()
        run(self.wifi.connect_wifi())
        
        if self.wifi.get_status() != 3:
            self.log.warn("Failed to connect to wifi")
            return False
        
        self.log.info("Connected to wifi")
        return True

    def download_file(self, url: str) -> bool:
        """
        Download a file from the url given to the /updates/ directory.
        """
        self.log.info(f"Downloading file from: {url}")
        try:
            filename = url.split('/')[-1]
            self.log.info(f"File name: {filename}")
            collect()
            response = requests.get(url)
            
            if response.status_code != 200:
                self.log.error(f"Failed to download file - got status code: {response.status_code}")
                response.close()
                return False
            
            self.save_file(filename, response.text)
            response.close()

            return True
        
        except Exception as e:
            self.log.error(f"Failed to download file: {e}")
            return False

    def save_file(self, filename, data) -> bool:
        """
        Save the data passed to the data variable in the appropriate location
        with the filename passed to the filename variable.
        """
        try:
            self.log.info(f"Saving file: {filename}")
            with open(self.update_path + '/' + filename, "wb") as f:
                f.write(data)
            self.log.info(f"File saved: {filename}")
            return True
        except Exception as e:
            self.log.error(f"Failed to save file '{filename}': {e}")
            return False
    
    def apply_files(self) -> bool:
        """
        Update SMIBHID with new files from /updates/ directory.
        """
        self.log.info("Updating HID")

        try:
            for file_name in os.listdir(self.update_path):
                if file_name == ".updating":
                    continue
                self.log.info(f"Updating {file_name}")
                update_path = self.update_path + '/' + file_name
                target_path = "/lib/" + file_name
                self.log.info(f"Moving {update_path} to {target_path}")
                os.rename(update_path, target_path)
                self.log.info(f"Updated {file_name}")
            self.log.info("All HID files updated successfully, restart required")
            return True
        except Exception as e:
            self.log.error(f"Failed to update HID: {e}")
            return False
