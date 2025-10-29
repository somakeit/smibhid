from smibhid_http.webserver import Webserver
from lib.ulogging import uLogger, File
from lib.module_config import ModuleConfig
from json import dumps
from collections import OrderedDict
from asyncio import run, create_task
from lib.updater import UpdateCore
from lib.sensors.file_logging import FileLogger
import config

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from lib.hid import HID
    from lib.displays.display import Display
    from lib.sensors import Sensors
    from lib.networking import WirelessNetwork
    from lib.space_state import SpaceState

class WebApp:

    def __init__(self, module_config: ModuleConfig, hid: 'HID') -> None:
        """
        A web app that provides a web interface to the smibhid device
        leveraging the tinyweb webserver.
        Pass the module_config object to the constructor to allow the webapp to
        access the necessary modules.
        """
        self.log = uLogger("Web app")
        self.log.info("Init webserver")
        self.logging_file = File()
        self.app = Webserver()
        self.hid: 'HID' = hid
        self.wifi: 'WirelessNetwork' = module_config.get_wifi()
        self.display: 'Display' = module_config.get_display()
        self.sensors: 'Sensors' = module_config.get_sensors()
        self.update_core: 'UpdateCore' = UpdateCore()
        self.port = 80
        self.running = False
        self.create_style_css()
        self.create_api_css()
        self.create_update_css()
        self.create_sensors_css()
        self.create_scd30_css()
        self.create_configuration_css()
        self.create_common_js()
        self.create_index_js()
        self.create_sensors_js()
        self.create_update_js()
        self.create_scd30_js()
        self.create_system_js()
        self.create_configuration_js()
        self.create_header_include()
        self.create_footer_include()
        self.create_favicon()
        self.create_homepage()
        self.create_update()
        self.create_sensors()
        self.create_scd30()
        self.create_system()
        self.create_configuration()
        self.create_test_sensors()
        self.create_api()

    def startup(self):
        network_access = run(self.wifi.check_network_access())

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

    def create_api_css(self):
        @self.app.route('/css/api.css')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/css/api.css', content_type='text/css')

    def create_update_css(self):
        @self.app.route('/css/update.css')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/css/update.css', content_type='text/css')

    def create_sensors_css(self):
        @self.app.route('/css/sensors.css')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/css/sensors.css', content_type='text/css')

    def create_scd30_css(self):
        @self.app.route('/css/scd30.css')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/css/scd30.css', content_type='text/css')

    def create_configuration_css(self):
        @self.app.route('/css/configuration.css')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/css/configuration.css', content_type='text/css')

    def create_common_js(self):
        @self.app.route('/js/common.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/common.js', content_type='application/javascript')

    def create_index_js(self):
        @self.app.route('/js/index.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/index.js', content_type='application/javascript')

    def create_sensors_js(self):
        @self.app.route('/js/sensors.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/sensors.js', content_type='application/javascript')

    def create_update_js(self):
        @self.app.route('/js/update.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/update.js', content_type='application/javascript')

    def create_scd30_js(self):
        @self.app.route('/js/scd30.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/scd30.js', content_type='application/javascript')

    def create_system_js(self):
        @self.app.route('/js/system.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/system.js', content_type='application/javascript')

    def create_configuration_js(self):
        @self.app.route('/js/configuration.js')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/js/configuration.js', content_type='application/javascript')
    
    def create_header_include(self):
        @self.app.route('/includes/header.html')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/includes/header.html', content_type='text/html')

    def create_footer_include(self):
        @self.app.route('/includes/footer.html')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/includes/footer.html', content_type='text/html')

    def create_favicon(self):
        @self.app.route('/logo')
        async def logo(request, response):
            # Redirect to the hosted logo image
            await response.redirect('https://raw.githubusercontent.com/somakeit/smibhid/refs/heads/master/images/smibhid_logo.png')
        
        @self.app.route('/favicon.ico')
        async def favicon_ico(request, response):
            # Redirect to the logo route for consistency
            await response.redirect('/logo')
        
        @self.app.route('/favicon.png')
        async def favicon_png(request, response):
            # Redirect to the logo route for consistency
            await response.redirect('/logo')
    
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
    
    def create_scd30(self) -> None:
        @self.app.route('/sensors/scd30')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/sensors/scd30.html')

    def create_system(self) -> None:
        @self.app.route('/system')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/system.html')

    def create_configuration(self) -> None:
        @self.app.route('/configuration')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/configuration.html')

    def create_test_sensors(self) -> None:
        @self.app.route('/test_sensors')
        async def index(request, response):
            await response.send_file('/smibhid_http/www/test_sensors.html')

    def create_api(self) -> None:
        @self.app.route('/api')
        async def api(request, response):
            await response.send_file('/smibhid_http/www/api.html')
        
        self.app.add_resource(WLANMAC, '/api/wlan/mac', wifi = self.wifi, logger = self.log)
        self.app.add_resource(Version, '/api/version', hid = self.hid, logger = self.log)
        self.app.add_resource(Hostname, '/api/hostname', hid = self.hid, logger = self.log)
        
        self.app.add_resource(FirmwareFiles, '/api/firmware_files', update_core = self.update_core, logger = self.log)
        self.app.add_resource(Reset, '/api/reset', update_core = self.update_core, logger = self.log)
        
        self.app.add_resource(Modules, '/api/sensors/modules', sensors = self.sensors, logger = self.log)
        self.app.add_resource(SensorsAPI, '/api/sensors/modules/<module>', sensors = self.sensors, logger = self.log)
        #self.app.add_resource(Readings, '/api/sensors/modules/<module>/readings/latest', sensors = self.sensors, logger = self.log) #TODO: Fix tinyweb to allow for multiple parameters https://github.com/belyalov/tinyweb/pull/51
        self.app.add_resource(Readings, '/api/sensors/readings/latest', module = "", sensors = self.sensors, logger = self.log)
        self.app.add_resource(SensorData, '/api/sensors/readings/log/<log_type>', logger = self.log)
        self.app.add_resource(SCD30, '/api/sensors/modules/SCD30/auto_measure', function = "auto_measure", sensors = self.sensors, logger = self.log)
        self.app.add_resource(SCD30, '/api/sensors/modules/SCD30/auto_measure/<value>', function = "auto_measure", sensors = self.sensors, logger = self.log)
        self.app.add_resource(SCD30, '/api/sensors/modules/SCD30/calibration/<value>', function = "calibration", sensors = self.sensors, logger = self.log)

        self.app.add_resource(Alarm, '/api/sensors/alarm/status', value = 'status', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Alarm, '/api/sensors/alarm/statuses', value = 'statuses', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Alarm, '/api/sensors/alarm/threshold', value = 'threshold', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Alarm, '/api/sensors/alarm/reset_threshold', value = 'reset_threshold', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Alarm, '/api/sensors/alarm/snooze_remaining', value = 'snooze_remaining', sensors = self.sensors, logger = self.log)
        self.app.add_resource(Alarm, '/api/sensors/alarm/snooze', sensors = self.sensors, logger = self.log)

        self.app.add_resource(SpaceStateManagement, '/api/space/state', space_state = self.hid.space_state, logger = self.log)
        self.app.add_resource(SpaceStateManagement, '/api/space/state/open', state = "open", space_state = self.hid.space_state, logger = self.log)
        self.app.add_resource(SpaceStateManagement, '/api/space/state/closed', state = "closed", space_state = self.hid.space_state, logger = self.log)
        
        self.app.add_resource(SpaceStateConfiguration, '/api/space/state/config/poll_period', space_state = self.hid.space_state, logger = self.log)
        self.app.add_resource(SpaceStateConfiguration, '/api/space/state/config/poll_period/<value>', space_state = self.hid.space_state, logger = self.log)

        self.app.add_resource(Logging, '/api/logs/read', logger = self.log, File = self.logging_file)

        self.app.add_resource(SMIBHIDConfiguration, '/api/configuration/list', logger = self.log)
        

class WLANMAC():

    def get(self, data, wifi: 'WirelessNetwork', logger: uLogger) -> str:
        logger.info("API request - wlan/mac")
        html = dumps(wifi.get_mac())
        logger.info(f"Return value: {html}")
        return html
    
class Version():

    def get(self, data, hid: 'HID', logger: uLogger) -> str:
        logger.info("API request - version")
        html = dumps(hid.version)
        logger.info(f"Return value: {html}")
        return html
    
class Hostname():

    def get(self, data, hid: 'HID', logger: uLogger) -> str:
        logger.info("API request - hostname")
        html = dumps(hid.wifi.determine_hostname())
        logger.info(f"Return value: {html}")
        return html

class FirmwareFiles():

    def get(self, data, update_core: 'UpdateCore', logger: uLogger) -> str:
        logger.info("API request - GET Firmware files")
        html = dumps(update_core.process_update_file())
        logger.info(f"Return value: {html}")
        return html
    
    def post(self, data, update_core: 'UpdateCore', logger: uLogger) -> str:
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

    def post(self, data, update_core: 'UpdateCore', logger: uLogger) -> None:
        logger.info("API request - reset")
        update_core.reset()
        return
    
class Modules():

    def get(self, data, sensors: 'Sensors', logger: uLogger) -> str:
        logger.info("API request - sensors/modules")
        html = dumps(sensors.get_modules())
        logger.info(f"Return value: {html}")
        return html

class SensorsAPI():

    def get(self, data, module: str, sensors: 'Sensors', logger: uLogger) -> str:
        logger.info(f"API request - sensors/{module}")
        sensor_list = sensors.get_sensors(module)
        logger.info(f"Available sensors: {sensor_list}")
        html = dumps(sensor_list)
        logger.info(f"Return value: {html}")
        return html

class Readings():

    def get(self, data, module: str, sensors: 'Sensors', logger: uLogger) -> str:
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
        
    def get(self, data, function: str, sensors: 'Sensors', logger: uLogger) -> str:
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
    
    def put(self, data, value, function: str, sensors: 'Sensors', logger: uLogger) -> str:
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
                value = config.DEFAULT_CO2_CALIBRATION_VALUE
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

class Alarm():

    def get(self, data, value: str, sensors: 'Sensors', logger: uLogger) -> str:
        if value == 'status':
            logger.info("API request - sensors/alarm/status")
            html = dumps(sensors.alarm.get_status())
        
        elif value == 'statuses':
            logger.info("API request - sensors/alarm/statuses")
            html = dumps(sensors.alarm.get_statuses())

        elif value == 'threshold':
            logger.info("API request - sensors/alarm/threshold")
            html = dumps(sensors.alarm.get_alarm_trigger_threshold())
        
        elif value == 'reset_threshold':
            logger.info("API request - sensors/alarm/reset_threshold")
            html = dumps(sensors.alarm.get_alarm_reset_threshold())

        elif value == 'snooze_remaining':
            logger.info("API request - sensors/alarm/snooze_remaining")
            html = dumps(sensors.alarm.get_remaining_snooze_time_s())

        else:
            logger.error(f"Invalid URL suffix: {value}")
            html = dumps("Invalid URL suffix")
        
        logger.info(f"Return value: {html}")
        
        return html
    
    def put(self, data, sensors: 'Sensors', logger: uLogger) -> str:
        logger.info("API request - PUT sensors/alarm/snooze")
        sensors.alarm.snooze_co2_alarm()
        html = dumps("Snoozed")
        logger.info(f"Return value: {html}")
        return html

class SpaceStateManagement():
    def get(self, data, space_state: SpaceState, logger: uLogger) -> str:
        logger.info("API request - GET sensors/space/state")
        try:
            html = dumps(space_state.get_space_state())
        except Exception as e:
            logger.error(f"Failed to get space state: {e}")
            html = "Failed to get space state"
        logger.info(f"Return value: {html}")
        return html

    def put(self, data, state: str, space_state: SpaceState, logger: uLogger) -> str:
        if state not in ["open", "closed"]:
            logger.error(f"Invalid URL suffix: {state}")
            return "Invalid URL suffix"
        
        logger.info(f"API request - PUT sensors/space/state/{state}")
        try:
            if state == "open":
                create_task(space_state.async_virtual_press_open_button())
            elif state == "closed":
                create_task(space_state.async_virtual_press_close_button())
            html = dumps("success")
        except Exception as e:
            logger.error(f"Failed to set space state: {e}")
            html = dumps(f"Failed to set space state: {e}")

        logger.info(f"Return value: {html}")
        return html

class SpaceStateConfiguration():
    def get(self, data, space_state: SpaceState, logger: uLogger) -> str:
        logger.info("API request - GET /api/space/state/config/poll_period")
        try:
            poll_period = space_state.get_space_state_poll_period()
            html = dumps({"poll_period_seconds": poll_period})
        except Exception as e:
            logger.error(f"Failed to get space state poll period: {e}")
            html = "Failed to get space state poll period"
        logger.info(f"Return value: {html}")
        return html

    def put(self, data, value: str, space_state: SpaceState, logger: uLogger) -> str:
        logger.info(f"API request - PUT /api/space/state/config/poll_period/{value}")
        try:
            period_s = int(value)
            logger.info(f"Setting poll period to: {period_s}")
            space_state.set_space_state_poll_period(period_s)
            html = dumps("success")
        except Exception as e:
            logger.error(f"Failed to set space state poll period: {e}")
            html = dumps(f"Failed to set space state poll period: {e}")

        logger.info(f"Return value: {html}")
        return html

class SMIBHIDConfiguration():

    def get(self, data, logger: uLogger) -> str:
        """
        Get the current SMIBHID configuration as a JSON object.
        The configuration layout is built dynamically based on the CONFIG_SECTIONS.
        This implementation uses OrderedDict for both the overall configuration and
        each section so the order of sections and the order of variables within
        each section exactly match the order defined in config.CONFIG_SECTIONS.
        """
        logger.info("API request - GET /api/configuration/list")
        try:
            # Use OrderedDict so insertion order (as defined in CONFIG_SECTIONS) is preserved
            configuration = OrderedDict()

            for section_name, config_items in config.CONFIG_SECTIONS.items():
                section_config = OrderedDict()
                for config_item in config_items:
                    try:
                        # Get the value from the config module
                        section_config[config_item] = getattr(config, config_item)
                    except AttributeError:
                        logger.warn(f"Configuration item '{config_item}' not found in config module")
                        section_config[config_item] = None

                configuration[section_name] = section_config

            html = dumps(configuration)
        except Exception as e:
            logger.error(f"Failed to get configuration list: {e}")
            html = dumps({"error": f"Failed to get configuration list: {e}"})

        logger.info(f"Return value: {html}")
        return html

class Logging():
    def get(self, data, logger: uLogger, File: File) -> str:
        logger.info("API request - GET /api/logs/read")
        try:
            log_contents = File.read_logs()
            html = dumps({"log": log_contents})
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            html = dumps(f"Failed to read log file: {e}")
        logger.info("Returning log contents")
        return html
