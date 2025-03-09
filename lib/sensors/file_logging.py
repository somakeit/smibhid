#TODO: Add max file size limit to log files
#TODO: Add smib last upload preserve cache to minute log
#TODO: Test hour logger
#TODO: Add file data GETs to API

from lib.ulogging import uLogger
from os import listdir, mkdir
from time import time, localtime
from json import dumps

class FileLogger:
    def __init__(self):
        self.log = uLogger("file_logger")
        self.check_and_create_folder("/", "data")
        self.check_and_create_folder("/data/", "sensors")
        self.last_hour_log_timestamp = None
    
    def check_and_create_folder(self, path: str, folder: str) -> bool:
        """
        Check if a directory exists on a given path.
        Path should be a string with a closing slash.
        """
        self.log.info(f"Checking for {folder} in {path}")
        try:
            if folder not in listdir(path [0:-1]):
                self.log.info(f"{folder} does not exist in {path} - creating")
                mkdir(path + folder)
                self.log.info(f"{path + folder} folder created")
            else:
                self.log.info(f"{folder} exists in {path}")
            return True
        except Exception as e:
            self.log.error(f"Failed to check for {folder} in {path}: {e}")
            return False
    
    def log_minute_entry(self, data: dict) -> None:
        """
        Add a unixtime and tuple timestamp to the provided minute log entries in and append to the minute_log.txt file.
        """
        self.log.info(f"Logging minute entry {data}")
        unixtime = time()
        timestamp = localtime(unixtime)
        entry = dumps({"unixtime": unixtime, "timestamp": timestamp, "data": data})
        try:
            with open("/data/sensors/minute_log.txt", "a") as f:
                f.write(entry)
            self.log.info(f"Minute entry logged {entry}")
        except Exception as e:
            self.log.error(f"Failed to log minute entry: {e}")
        
        if self.is_it_time_generate_hour_log():
            try:
                self.log.info("Generating hour log")
                self.process_hour_logs()
                self.log.info("Hour log generated")
            except Exception as e:
                self.log.error(f"Failed to generate hour log: {e}")
    
    def process_hour_logs(self) -> None:
        """
        Create min, max and averge values for each sensor in the minute log and append to the hour log.
        Truncate the minute log to last 60 minutes.
        """
        new_minute_log = []
        hour_data = []
        with open("/data/sensors/minute_log.txt", "r") as f:
            minute_log = f.read()
        minute_log = minute_log.split("\n")
        
        minute_log = [eval(entry) for entry in minute_log if entry != ""]
        hour_log = {}
        for entry in minute_log:
            if entry["unixtime"] < time() - 3600:
                new_minute_log.append(entry)
                for module in entry["data"]:
                    for sensor in module:
                        hour_data[module][sensor].append(entry["data"][module][sensor])
        
        hour_log_data = self.process_hour_data_values(hour_data)
        hour_log = {"unixtime": time(), "timestamp": localtime(time()), "data": hour_log_data}
        
        with open("/data/sensors/hour_log.txt", "a") as f:
            f.write(dumps(hour_log) + "\n")
        
        with open("/data/sensors/minute_log.txt", "w") as f:
            f.write("")
        with open("/data/sensors/minute_log.txt", "a") as f:
            for entry in new_minute_log:
                f.write(dumps(entry) + "\n")
    
    def process_hour_data_values(self, data: list) -> list:
        """
        Process the min, max and average values for each sensor in the hour log.
        """
        processed_data = []
        
        for module in data:
            for sensor in module:
                min_value = min(module[sensor])
                max_value = max(module[sensor])
                average_value = sum(module[sensor]) / len(module[sensor])
                processed_data[module][sensor] = {"min": min_value, "max": max_value, "average": average_value}

        return processed_data
    
    def is_it_time_generate_hour_log(self) -> bool:
        """
        Return True if current time is greater than the last hour log timestamp + 3600 seconds.
        """
        if self.last_hour_log_timestamp is None:
            self.last_hour_log_timestamp = time()
            return False
        
        if time() > self.last_hour_log_timestamp + 3600:
            self.last_hour_log_timestamp = time()
            return True
        return False
