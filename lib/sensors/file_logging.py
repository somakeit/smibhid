#TODO: Test log rotation

from lib.ulogging import uLogger
from os import listdir, mkdir, stat, remove, rename
from time import time, localtime
from json import dumps, loads
from config import SENSOR_LOG_FILE_MAX_SIZE, SENSOR_LOG_CACHE_ENABLED

class FileLogger:
    def __init__(self, init_files: bool = False) -> None:
        self.log = uLogger("file_logger")
        self.enabled = SENSOR_LOG_CACHE_ENABLED
        if init_files is True:
            self.init_file_structure()
        self.last_hour_log_timestamp = None
        self.minute_log_file = "/data/sensors/minute_log.txt"
        self.hour_log_file = "/data/sensors/hour_log.txt"
        self.LOG_FILE_MAX_SIZE = SENSOR_LOG_FILE_MAX_SIZE
    
    def init_file_structure(self) -> None:
        self.check_and_create_folder("/", "data")
        self.check_and_create_folder("/data/", "sensors")
        self.check_and_create_file("/data/sensors/", "minute_log.txt")
        self.check_and_create_file("/data/sensors/", "minute_log2.txt")
        self.check_and_create_file("/data/sensors/", "hour_log.txt")
        self.check_and_create_file("/data/sensors/", "hour_log2.txt")
    
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
    
    def check_and_create_file(self, path: str, file: str) -> bool:
        """
        Check if a file exists in a given path.
        File should be provided with a fully qualified path as strings.
        """
        self.log.info(f"Checking for {file} in {path}")
        try:
            if file not in listdir(path):
                self.log.info(f"{file} does not exist in {path} - creating")
                with open(path + file, "w") as f:
                    f.write("")
                self.log.info(f"{file} created in {path}")
            else:
                self.log.info(f"{file} exists in {path}")
            return True
        except Exception as e:
            self.log.error(f"Failed to check for {file} in {path}: {e}")
            return False
    
    def localtime_to_iso8601(self, localtime_tuple) -> str:
        """
        Convert a localtime tuple to an ISO 8601 formatted string.
        Assumes UTC time zone for the localtime_tuple.
        """
        try:
            year, month, day, hour, minute, second, *_ = localtime_tuple
        
        except Exception as e:
            self.log.error(f"Failed to convert localtime to ISO 8601: {e}")
            return "0000-00-00T00:00:00Z"
        
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    
    def log_minute_entry(self, data: dict) -> None:
        """
        Add a unixtime and tuple timestamp to the provided minute log entries in and append to the minute_log.txt file.
        """
        if self.enabled is False:
            self.log.info("Sensor log cache is disabled, skipping minute log entry")
            return
        
        self.log.info(f"Logging minute entry {data}")

        self.check_for_log_rotate(self.minute_log_file)

        entry = self.create_minute_timestamped_entry(data)

        try:
            with open("/data/sensors/minute_log.txt", "a") as f:
                f.write(entry)
            self.log.info(f"Minute entry logged {entry}")
        except Exception as e:
            self.log.error(f"Failed to log minute entry: {e}")
        
        if self.is_it_time_to_generate_hour_log():
            try:
                self.log.info("Generating hour log")
                self.process_hour_log()
                self.log.info("Hour log generated")
            except Exception as e:
                self.log.error(f"Failed to generate hour log: {e}")

    def create_minute_timestamped_entry(self, data: dict) -> str:
        """
        Create a timestamped entry for the minute log file.
        """
        timestamp = time()
        human_timestamp = self.localtime_to_iso8601(localtime(timestamp))
        entry = dumps({"timestamp": timestamp, "human_timestamp": human_timestamp, "data": data}) + "\n"
        self.log.info(f"Minute entry: {entry}")

        return entry
    
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
    
    def process_hour_log(self) -> None:
        """
        Create min, max and average values for each sensor in the minute log and append to the hour log.
        Truncate the minute log to last 60 minutes.
        """
        
        minute_log: list = self.get_specific_log(self.minute_log_file)
        
        new_minute_log, hour_data = self.process_minute_log(minute_log)
        self.log.info(f"New minute log: {new_minute_log}")
        self.log.info(f"Hour data: {hour_data}")

        hour_log_data = self.process_hour_data_values(hour_data)
        self.log.info(f"Hour log data: {hour_log_data}")

        hour_log = {"timestamp": time(), "human_timestamp": self.localtime_to_iso8601(localtime(time())), "data": hour_log_data}
        
        self.write_out_logs(new_minute_log, hour_log)
    
    def process_minute_log(self, minute_log: list) -> tuple[list, dict]:
        """
        Process the minute log to return lists of results by sensor and return
        a truncated minute log to the last 60 minutes.
        """
        new_minute_log = []
        hour_data = {}

        try: 
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
        
        except Exception as e:
            self.log.error(f"Failed to process minute log: {e}")
            return minute_log, {}
        
        return new_minute_log, hour_data
    
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
    
    def write_out_logs(self, new_minute_log: list, hour_log: dict) -> None:
        """
        Write out the hour log rotating as necessary.
        Write out the new minute log.
        """
        try:
            with open("/data/sensors/hour_log.txt", "a") as f:
                f.write(dumps(hour_log) + "\n")
            
            self.check_for_log_rotate(self.hour_log_file)
            
            with open("/data/sensors/minute_log.txt", "w") as f:
                f.write("")
            with open("/data/sensors/minute_log.txt", "a") as f:
                for entry in new_minute_log:
                    f.write(dumps(entry) + "\n")

        except Exception as e:
            self.log.error(f"Failed to write out logs: {e}")
            self.check_for_log_rotate(self.hour_log_file)
            self.check_for_log_rotate(self.minute_log_file)
    
    def get_log(self, log_type: str) -> list:
        """
        Return the requested log as a JSON string.
        """
        if self.enabled is False:
            self.log.info("Sensor log cache is disabled - No log data to return")
            return ["Sensor log cache is disabled"]

        if log_type == "minute":
            return self.get_specific_log(self.minute_log_file)
        elif log_type == "hour":
            return self.get_specific_log(self.hour_log_file)
        else:
            return ["Invalid log type"]
    
    def get_specific_log(self, log_file: str) -> list[dict]:
        """
        Return the requested log file (fullly qualified path) as a list of dictionaries.
        """
        self.log.info(f"Getting log file contents: {log_file}")
        try:
            data = []
            with open(log_file, "r") as f:
                for line in f:
                    self.log.info(f"Log line: {line}")
                    data.append(loads(line))
            second_log_file = log_file.replace(".txt", "2.txt")
            with open(second_log_file, "r") as f:
                for line in f:
                    self.log.info(f"Second log line: {line}")
                    data.append(loads(line))
            self.log.info(f"Log data: {data}")
            return data

        except Exception as e:
            self.log.error(f"Failed to get {log_file} log: {e}")
            return [{}]
    
    def check_for_log_rotate(self, log_file: str) -> None:
        try:
            log_file_size = stat(log_file)[6]
            if log_file_size > self.LOG_FILE_MAX_SIZE:
                new_log_file = log_file.replace(".txt", "2.txt")
                self.rotate_file(log_file, new_log_file)
        
        except Exception as e:
            self.log.error(f"Failed to check for and execute log rotation: {e}")

    def rotate_file(self, log_file: str, new_log_file: str) -> None:
        try:
            self.log.info(f"Rotating {log_file} to {new_log_file}")
            remove(new_log_file)
        except OSError:
            print(f"{new_log_file} did not exist to be deleted.")
        
        try:
            rename(log_file, new_log_file)
            with open(log_file, "w") as f:
                f.write("")
        except Exception as e:
            self.log.error(f"Failed to rotate {log_file} to {new_log_file}: {e}")
