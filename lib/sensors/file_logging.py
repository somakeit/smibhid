#TODO: Add max file size limit to log files - same as logger

from lib.ulogging import uLogger
from os import listdir, mkdir
from time import time, localtime
from json import dumps, loads

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
    
    def localtime_to_iso8601(self, localtime_tuple) -> str:
        """
        Convert a localtime tuple to an ISO 8601 formatted string.
        """
        year, month, day, hour, minute, second, *_ = localtime_tuple
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    
    def log_minute_entry(self, data: dict) -> None:
        """
        Add a unixtime and tuple timestamp to the provided minute log entries in and append to the minute_log.txt file.
        """
        self.log.info(f"Logging minute entry {data}")
        timestamp = time()
        human_timestamp = self.localtime_to_iso8601(localtime(timestamp))
        entry = dumps({"timestamp": timestamp, "human_timestamp": human_timestamp, "data": data}) + "\n"
        self.log.info(f"Minute entry: {entry}")
        try:
            with open("/data/sensors/minute_log.txt", "a") as f:
                f.write(entry)
            self.log.info(f"Minute entry logged {entry}")
        except Exception as e:
            self.log.error(f"Failed to log minute entry: {e}")
        
        if self.is_it_time_to_generate_hour_log():
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
        hour_data = {}
        minute_log: list = self.get_minute_log()
        
        for minute in minute_log:
            if minute["timestamp"] > time() - 3600:
                new_minute_log.append(minute)
            for module, data in minute["data"].items():
                if module not in hour_data:
                    hour_data[module] = {}
                self.log.info(f"Module: {module}")
                self.log.info(f"Data: {data}")
                for sensor, value in data.items():
                    if sensor not in hour_data[module]:
                        hour_data[module][sensor] = []
                    self.log.info(f"Sensor: {sensor}")
                    self.log.info(f"Value: {value}")
                    hour_data[module][sensor].append(value)
        
        self.log.info(f"Hour data: {hour_data}")
        hour_log_data = self.process_hour_data_values(hour_data)
        self.log.info(f"Hour log data: {hour_log_data}")
        hour_log = {"timestamp": time(), "human_timestamp": self.localtime_to_iso8601(localtime(time())), "data": hour_log_data}
        
        with open("/data/sensors/hour_log.txt", "a") as f:
            f.write(dumps(hour_log) + "\n")
        
        with open("/data/sensors/minute_log.txt", "w") as f:
            f.write("")
        with open("/data/sensors/minute_log.txt", "a") as f:
            for entry in new_minute_log:
                f.write(dumps(entry) + "\n")
    
    def process_hour_data_values(self, data: dict) -> dict:
        """
        Process the min, max and average values for each sensor in the hour log.
        """
        processed_data = {}

        for module, sensors in data.items():
            processed_data[module] = {}
            for sensor, values in sensors.items():
                processed_data[module][sensor] = {}
                processed_data[module][sensor]["avg"] = round(sum(values) / len(values), 2)
                processed_data[module][sensor]["max"] = max(values)
                processed_data[module][sensor]["min"] = min(values)

        return processed_data
    
    def is_it_time_to_generate_hour_log(self) -> bool:
        """
        Return True if current time is greater than the last hour log timestamp + 3600 seconds.
        """
        if self.last_hour_log_timestamp is None:
            self.log.info("Setting hour log timestamp from None")
            self.last_hour_log_timestamp = time()
            return False
        
        if time() > self.last_hour_log_timestamp + 3600:
            self.log.info("It's time to generate the hour log")
            self.last_hour_log_timestamp = time()
            self.log.info(f"Last hour log timestamp updated to {self.last_hour_log_timestamp}")
            return True
        else:
            seconds_since_last_hour_log = time() - self.last_hour_log_timestamp
            self.log.info(f"Seconds since last hour log: {seconds_since_last_hour_log}")
            return False

    def get_log(self, log_type: str) -> list:
        """
        Return the requested log as a JSON string.
        """
        if log_type == "minute":
            return self.get_minute_log()
        elif log_type == "hour":
            return self.get_hour_log()
        else:
            return ["Invalid log type"]
    
    def get_minute_log(self) -> list: # TODO: DRY minute and hour log methods
        """
        Return the minute log as a list of data readings dictionaries.
        """
        try:
            data = []
            with open("/data/sensors/minute_log.txt", "r") as f:
                for line in f:
                    data.append(loads(line))
            return data

        except Exception as e:
            self.log.error(f"Failed to get minute log: {e}")
            return ["Failed to get minute log"]
    
    def get_hour_log(self) -> list:
        """
        Return the hour log as a JSON string.
        """
        try:
            data = []
            with open("/data/sensors/hour_log.txt", "r") as f:
                for line in f:
                    self.log.info(f"Hour log line: {line}")
                    data.append(loads(line))
            self.log.info(f"Hour log data: {data}")
            return data

        except Exception as e:
            self.log.error(f"Failed to get hour log: {e}")
            return ["Failed to get hour log"]
