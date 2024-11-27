from http.webserver import Webserver
from lib.ulogging import uLogger
from lib.module_config import ModuleConfig
from json import dumps
import uasyncio

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
        self.port = 80
        self.running = False
        self.create_style_css()
        self.create_homepage()
        self.create_api()

    def startup(self):
        network_access = uasyncio.run(self.wifi.check_network_access())

        if network_access == True:
            self.log.info("Starting web server")
            self.app.run(host='0.0.0.0', port=self.port, loop_forever=False)
            self.log.info(f"Web server started: {self.wifi.get_ip()}:{self.port}")
            self.running = True
        else:
            self.log.error("No network access - web server not started")
    
    def create_style_css(self):
        @self.app.route('/css/style.css')
        async def index(request, response):
            await response.send_file('/http/www/css/style.css', content_type='text/css')
    
    def create_homepage(self) -> None:
        @self.app.route('/')
        async def index(request, response):
            await response.send_file('/http/www/index.html')

    def create_api(self) -> None:
        @self.app.route('/api')
        async def api(request, response):
            await response.send_file('/http/www/api.html')
        
        self.app.add_resource(WLANMAC, '/api/wlan/mac', wifi = self.wifi, logger = self.log)
        self.app.add_resource(Version, '/api/version', hid = self.hid, logger = self.log)
    
class WLANMAC():

    def get(self, data, wifi, logger: uLogger):
        logger.info("API request - wlan/mac")
        html = dumps(wifi.get_mac())
        logger.info(f"Return value: {html}")
        return html
    
class Version():

    def get(self, data, hid, logger: uLogger):
        logger.info("API request - version")
        html = dumps(hid.version)
        logger.info(f"Return value: {html}")
        return html