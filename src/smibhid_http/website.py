from smibhid_http.webserver import Webserver
from lib.ulogging import uLogger
from lib.module_config import ModuleConfig
from json import dumps
import uasyncio
from lib.updater import UpdateCore
from lib.sensors.file_logging import FileLogger
from config import DEFAULT_CO2_CALIBRATION_VALUE

class WebApp:

    def __init__(self, module_config: ModuleConfig, hid: object) -> None:
        """
        A web app that provides a web interface to the smibhid device
        leveraging the tinyweb webserver.
        Pass the module_config object to the constructor to allow the webapp to
        access the necessary modules.
        """
        self.log = uLogger("Web app")
        self.log.info("Init webserver")
        self.app = Webserver()
        self.hid = hid
        self.wifi = module_config.get_wifi()
        self.display = module_config.get_display()
        self.sensors = module_config.get_sensors()
        self.update_core = UpdateCore()
        self.port = 80
        self.running = False
        self.create_style_css()
        self.create_update_js()
        self.create_homepage()
        self.create_update()
        self.create_sensors()
        self.create_scd30_js()
        self.create_scd30()
        self.create_api()

    def startup(self):
        network_access = uasyncio.run(self.wifi.check_network_access())

        if network_access:
            self.log.info("Starting web server")
            self.app.run(host='0.0.0.0', port=self.port, loop_forever=False)
            self.log.info(f"Web server started: {self.wifi.get_ip()}:{self.port}")
            self.running = True
        else:
            self.log.error("No network access - web server not started")
    
    def create_style_css(self):
        @self.app.route('/css/style.css')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/css/style.css', content_type='text/css')

    def create_update_js(self):
        @self.app.route('/js/update.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/update.js', content_type='application/javascript')
    
    def create_homepage(self) -> None:
        @self.app.route('/')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/index.html')

    def create_update(self) -> None:
        @self.app.route('/update')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/update.html')
    
    def create_sensors(self) -> None:
        @self.app.route('/sensors')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/sensors/sensors.html')
    
    def create_scd30_js(self) -> None:
        @self.app.route('/js/scd30.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/scd30.js', content_type='application/javascript')
    
    def create_scd30(self) -> None:
        @self.app.route('/sensors/scd30')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/sensors/scd30.html')

    def create_api(self) -> None:
        @self.app.route('/api')
        async def api(request, response):
            await response.send_file('/smibhid_http/www/api.html')
        
        self.app.add_resource(WLANMAC, '/api/wlan/mac', wifi = self.wifi, logger = self.log)
        self.app.add_resource(Version, '/api/version', hid = self.hid, logger = self.log)
        
        self.app.add_resource(FirmwareFiles, '/api/firmware_files', update_core = self.update_core, logger = self.log)
        self.app.add_resource(Reset, '/api/reset', update_core = self.update_core, logger = self.log)
        
        self.app.add_resource(Modules, '/api/sensors/modules', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Sensors, '/api/sensors/modules/<module>', sensors = self.sensors, logger = self.log)
        #self.app.add_resource(Readings, '/api/sensors/modules/<module>/readings/latest', sensors = self.sensors, logger = self.log) #TODO: Fix tinyweb to allow for multiple parameters https://github.com/belyalov/tinyweb/pull/51
        self.app.add_resource(Readings, '/api/sensors/readings/latest', module = "", sensors = self.sensors, logger = self.log)
        self.app.add_resource(SensorData, '/api/sensors/readings/log/<log_type>', logger = self.log)
        self.app.add_resource(SCD30, '/api/sensors/modules/SCD30/auto_measure', function = "auto_measure", sensors = self.sensors, logger = self.log)
        self.app.add_resource(SCD30, '/api/sensors/modules/SCD30/auto_measure/<value>', function = "auto_measure", sensors = self.sensors, logger = self.log)
        self.app.add_resource(SCD30, '/api/sensors/modules/SCD30/calibration/<value>', function = "calibration", sensors = self.sensors, logger = self.log)
    
class WLANMAC():

    def get(self, data, wifi, logger: uLogger) -> str:
        logger.info("API request - wlan/mac")
        html = dumps(wifi.get_mac())
        logger.info(f"Return value: {html}")
        return html
    
class Version():

    def get(self, data, hid, logger: uLogger) -> str:
        logger.info("API request - version")
        html = dumps(hid.version)
        logger.info(f"Return value: {html}")
        return html
    
class Hostname():

    def get(self, data, hid, logger: uLogger) -> str:
        logger.info("API request - hostname")
        html = dumps(hid.wifi.determine_hostname())
        logger.info(f"Return value: {html}")
        return html

class FirmwareFiles():

    def get(self, data, update_core: UpdateCore, logger: uLogger) -> str:
        logger.info("API request - GET Firmware files")
        html = dumps(update_core.process_update_file())
        logger.info(f"Return value: {html}")
        return html
    
    def post(self, data, update_core: UpdateCore, logger: uLogger) -> str:
        logger.info("API request - POST Firmware files")
        logger.info(f"Data: {data}")
        if data["action"] == "add":
            logger.info("Adding update - data: {data}")
            html = update_core.stage_update_url(data["url"])
        elif data["action"] == "remove":
            logger.info("Removing update - data: {data}")
            html = update_core.unstage_update_url(data["url"])
        else:
            html = f"Invalid request: {data['action']}"
        return dumps(html)
    
class Reset():

    def post(self, data, update_core: UpdateCore, logger: uLogger) -> None:
        logger.info("API request - reset")
        update_core.reset()
        return
    
class Modules():

    def get(self, data, sensors, logger: uLogger) -> str:
        logger.info("API request - sensors/modules")
        html = dumps(sensors.get_modules())
        logger.info(f"Return value: {html}")
        return html

class Sensors():

    def get(self, data, module: str, sensors, logger: uLogger) -> str:
        logger.info(f"API request - sensors/{module}")
        sensor_list = sensors.get_sensors(module)
        logger.info(f"Available sensors: {sensor_list}")
        html = dumps(sensor_list)
        logger.info(f"Return value: {html}")
        return html

class Readings():

    def get(self, data, module: str, sensors, logger: uLogger) -> str:
        logger.info(f"API request - sensors/readings - Module: {module}")
        html = dumps(sensors.get_readings(module))
        logger.info(f"Return value: {html}")
        return html

class SensorData():

    def get(self, data, log_type: str, logger: uLogger) -> str:
        logger.info(f"API request - sensors/readings/{log_type}")
        try:
            html = dumps(FileLogger().get_log(log_type))
        except Exception as e:
            logger.error(f"Failed to get {log_type} log: {e}")
            html = "Failed to get log"
        logger.info(f"Return value: {html}")
        return html

class SCD30():
        
        def get(self, data, function: str, sensors, logger: uLogger) -> str:
            if function == "auto_measure":
                logger.info("API request - sensors/scd30/auto_measure")
                try:
                    scd30 = sensors.configured_modules["SCD30"]
                    html = str(scd30.get_status_ready())
                except Exception as e:
                    logger.error(f"Failed to get SCD30 automatic measurement status: {e}")
                    html = "Failed to get automatic measurement status"
                logger.info(f"Return value: {html}")

            return html
        
        def put(self, data, value, function: str, sensors, logger: uLogger) -> str:
            if function == "auto_measure":
                logger.info(f"API request - sensors/scd30/auto_measure/{value}")
                
                if value not in ["start", "stop"]:
                    logger.error(f"Invalid URL suffix: {value}")
                    return "Invalid URL suffix"
                
                try:
                    scd30 = sensors.configured_modules["SCD30"]
                    if value == "start":
                        scd30.start_continuous_measurement()
                    if value == "stop":
                        scd30.stop_continuous_measurement()
                    html = "success"

                except Exception as e:
                    logger.error(f"Failed to start/stop SCD30 measurement: {e}")
                    html = f"Incorrect URL suffix: {value}, expected 'start' or 'stop'"
                
                logger.info(f"Return value: {html}")

            if function == "calibration":
                if not value.isdigit():
                    logger.error(f"Invalid calibration value: {value}")
                    return "Invalid calibration value"
                
                value = int(value)
                
                if value == 0:
                    logger.info("Setting SCD30 calibration to default value")
                    value = DEFAULT_CO2_CALIBRATION_VALUE
                    logger.info(f"Default calibration value: {value}")
                logger.info(f"API request - sensors/scd30/calibration/{value}")
                
                try:
                    scd30 = sensors.configured_modules["SCD30"]
                    scd30.set_forced_recalibration(int(value))
                    html = "success"
                
                except Exception as e:
                    logger.error(f"Failed to set SCD30 calibration: {e}")
                    html = f"Failed to set calibration: {e}"
                
                logger.info(f"Return value: {html}")
            
            return html
