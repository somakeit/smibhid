from lib.ulogging import uLogger
import os
import machine
import requests
from gc import collect
from lib.networking import WirelessNetwork
from asyncio import run

class Updater:
    def __init__(self) -> None:
        self.log = uLogger("Updater")
        self.update_path = "/updates/"

    def enter_update_mode(self) -> bool:
        """
        Enter update mode.
        """
        self.log.info("Entering update mode")
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
                
                for url in urls:
                    self.download_file(url)
                
                #self.apply_files() # TODO: Disabling applying files while connected to the device
                #self.reset()
                return True
            
            except Exception as e:
                self.log.error(f"Failed to apply updates: {e}")
                self.exit_with_failure()
                return False

    def exit_with_failure(self) -> None:
        """
        Clears update flag and restores backups if present to reboot into best
        known normal run state.
        """
        self.log.error("Cannot apply updates - future code will revert to backed up files - clearing update flag to reboot into normal mode")
        #os.remove(self.update_path + ".updating") #TODO Disabling removing the update flag while connected to the device
        #self.reset() #TODO Disabling reset while connected to the device

    def process_update_file(self) -> list:
        """
        Process updates.
        """
        self.log.info("Processing updates")
        with open(self.update_path + ".updating", "r") as f:
            update_data = f.read()
        self.log.info(f"Update data: {update_data}")
        urls = []
        for update in update_data.split("\n"):
            urls.append(update)
        self.log.info(f"URLs: {urls}")
        return urls
    
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
            self.log.info(f"Data: {data}")
            with open(self.update_path + filename, "wb") as f:
                f.write(data)
            self.log.info(f"File saved: {filename}")
            return True
        except Exception as e:
            self.log.error(f"Failed to save file '{filename}': {e}")
            return False
    
    # def upload_file(self, file) -> bool:
    #     """
    #     Upload a file to the /updates/ directory.
    #     """
    #     self.log.info(f"Uploading file: {file}")
    #     try:
    #         with open(self.update_path + file, "wb") as f:
    #             f.write(file)
    #         self.log.info(f"File uploaded: {file}")
    #         return True
    #     except Exception as e:
    #         self.log.error(f"Failed to upload file: {e}")
    #         return False
    
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