import pytest

@pytest.fixture()
def hid_log():
    from lib.ulogging import uLogger
    from lib.hid import HID
    log = uLogger("test_endpoint")
    hid = HID()
    return hid, log

@pytest.fixture()
def hid_log_with_version(hid_log):
    hid, log = hid_log
    test_version = "1.5.0"
    hid.version = test_version
    return hid, log, test_version

@pytest.fixture()
def webapp(hid_log_with_version):
    from smibhid_http.website import WebApp
    hid, log, version = hid_log_with_version
    from lib.module_config import ModuleConfig
    from lib.networking import WirelessNetwork
    from lib.display import Display
    from machine import I2C

    i2c = I2C(0, sda=21, scl=22, freq=100000)
    module_config = ModuleConfig()
    module_config.register_wifi(WirelessNetwork())
    module_config.register_display(Display(i2c))
    module_config.register_sensors(i2c)

    app = WebApp(module_config, hid)
    return app

def test_import_hid():
    """
    Test the import of the HID module.
    """
    try:
        from lib.hid import HID
        assert HID is not None
    except ImportError as e:
        assert False, f"Failed to import HID: {e}"

def test_import_webserver():
    """
    Test the import of the webserver module.
    """
    try:
        from smibhid_http.webserver import Webserver
        assert Webserver is not None
    except ImportError as e:
        assert False, f"Failed to import WebApp: {e}"

def test_import_webapp():
    """
    Test the import of the webapp module.
    """
    try:
        from smibhid_http.website import WebApp
        assert WebApp is not None
    except ImportError as e:
        assert False, f"Failed to import WebApp: {e}"

def test_hid_firmware_version_returned(hid_log_with_version):
    """
    Test that the HID firmware version is returned correctly.
    """
    hid, log, test_version = hid_log_with_version
    expected_version = hid.version
    assert expected_version == test_version, f"Expected firmware version {test_version}, got '{expected_version}'"

def test_firmware_endpoint_returns_current_firmware_version(hid_log_with_version):
    """
    Test that the firmware endpoint returns the current firmware version.
    """
    from smibhid_http.website import Version
    from json import dumps
    hid, log, hid_version = hid_log_with_version
    version = Version()
    response = version.get("", hid, log)
    assert response == dumps(hid_version), f"Expected {dumps(hid_version)}, got '{response}'"

def test_correct_mac_address_returned():
    """
    Test that the correct MAC address is returned.
    """
    from lib.networking import WirelessNetwork
    wlan = WirelessNetwork()
    mac = wlan.get_mac_address()
    assert mac is not None, "MAC address should not be None"
    assert isinstance(mac, str), "MAC address should be a string"
    assert len(mac) == 17, "MAC address should be 17 characters long (including colons)"
    assert mac == "00:11:22:33:44:55"

def test_default_hostname_generation():
    """
    Test that the default hostname is generated correctly.
    """
    from lib.networking import WirelessNetwork
    wlan = WirelessNetwork()
    hostname = wlan.determine_hostname()
    expected_hostname = "smibhid-334455"
    assert hostname == expected_hostname, f"Expected {expected_hostname}, got '{hostname}'"

def test_custom_hostname_generation():
    """
    Test that a custom hostname is generated correctly.
    """
    import config
    from lib.networking import WirelessNetwork
    
    custom_hostname = "custom-hostname"
    config.CUSTOM_HOSTNAME = custom_hostname
    
    wlan = WirelessNetwork()
    expected_hostname = wlan.determine_hostname()
    assert expected_hostname == custom_hostname, f"Expected '{custom_hostname}', got '{expected_hostname}'"

def test_hostname_endpoint_returns_correct_hostname(hid_log):
    """
    Test that the hostname endpoint returns the default device hostname if not configured.
    """
    from json import dumps
    from smibhid_http.website import Hostname
    from lib.networking import WirelessNetwork
    hid, log = hid_log
    hostname = Hostname()
    response = hostname.get("", hid, log)
    wlan = WirelessNetwork()
    expected_hostname = wlan.determine_hostname()
    assert response == dumps(expected_hostname), f"Expected {expected_hostname}, got '{response}'"

def test_hostname_endpoint_is_registered(webapp):
    """
    Test that the hostname endpoint is registered correctly in the web application.
    """
    from smibhid_http.website import Hostname

    app = webapp

    # Access the underlying tinyweb Webserver instance
    tinyweb_app = app.app

    # The explicit_url_map maps url bytes to (handler, params)
    url = b'/api/hostname'
    assert url in tinyweb_app.explicit_url_map, "Hostname endpoint not registered"

    handler, params = tinyweb_app.explicit_url_map[url]
    # The handler should be restful_resource_handler, and params['_callmap'] should map b'GET' to (Hostname.get, ...)
    assert callable(handler), "Handler for /api/hostname is not callable"
    assert b'GET' in params['_callmap'], "GET method not registered for /api/hostname"
    get_handler, kwargs = params['_callmap'][b'GET']
    # The handler should be Hostname.get or a bound method of Hostname
    assert hasattr(get_handler, '__self__'), "GET handler is not a bound method"
    assert isinstance(get_handler.__self__, Hostname), "GET handler is not from Hostname class"

def test_space_light_state_endpoint_is_registered(webapp):
    """
    Test that the space light state endpoint is registered correctly.
    """
    from smibhid_http.website import SpaceLightState

    app = webapp
    tinyweb_app = app.app

    url = b'/api/space/light/state'
    assert url in tinyweb_app.explicit_url_map, "Space light state endpoint not registered"

    handler, params = tinyweb_app.explicit_url_map[url]
    assert callable(handler), "Handler for /api/space/light/state is not callable"
    assert b'GET' in params['_callmap'], "GET method not registered for /api/space/light/state"
    get_handler, kwargs = params['_callmap'][b'GET']
    assert hasattr(get_handler, '__self__'), "GET handler is not a bound method"
    assert isinstance(get_handler.__self__, SpaceLightState), "GET handler is not from SpaceLightState class"

def test_space_light_value_endpoint_is_registered(webapp):
    """
    Test that the space light value endpoint is registered correctly.
    """
    from smibhid_http.website import SpaceLightValue

    app = webapp
    tinyweb_app = app.app

    url = b'/api/space/light/value'
    assert url in tinyweb_app.explicit_url_map, "Space light value endpoint not registered"

    handler, params = tinyweb_app.explicit_url_map[url]
    assert callable(handler), "Handler for /api/space/light/value is not callable"
    assert b'GET' in params['_callmap'], "GET method not registered for /api/space/light/value"
    get_handler, kwargs = params['_callmap'][b'GET']
    assert hasattr(get_handler, '__self__'), "GET handler is not a bound method"
    assert isinstance(get_handler.__self__, SpaceLightValue), "GET handler is not from SpaceLightValue class"

def test_space_light_threshold_endpoint_is_registered(webapp):
    """
    Test that the space light threshold endpoint is registered correctly.
    """
    from smibhid_http.website import SpaceLightThreshold

    app = webapp
    tinyweb_app = app.app

    url = b'/api/space/light/threshold'
    assert url in tinyweb_app.explicit_url_map, "Space light threshold endpoint not registered"

    handler, params = tinyweb_app.explicit_url_map[url]
    assert callable(handler), "Handler for /api/space/light/threshold is not callable"
    assert b'GET' in params['_callmap'], "GET method not registered for /api/space/light/threshold"
    assert b'PUT' in params['_callmap'], "PUT method not registered for /api/space/light/threshold"

def test_space_light_state_endpoint_returns_json(hid_log):
    """
    Test that the space light state endpoint returns JSON with expected keys.
    """
    from smibhid_http.website import SpaceLightState
    from json import loads
    hid, log = hid_log
    space_light_state = SpaceLightState()
    response = space_light_state.get("", hid.space_state, log)
    
    # Parse the JSON response
    response_data = loads(response)
    
    # Assert that the response contains the expected key
    assert "light_state" in response_data, "Response should contain 'light_state' key"

def test_space_light_value_endpoint_returns_json(hid_log):
    """
    Test that the space light value endpoint returns JSON with expected keys.
    """
    from smibhid_http.website import SpaceLightValue
    from json import loads
    hid, log = hid_log
    space_light_value = SpaceLightValue()
    response = space_light_value.get("", hid.space_state, log)
    
    # Parse the JSON response
    response_data = loads(response)
    
    # Assert that the response contains the expected key
    assert "light_value_lux" in response_data, "Response should contain 'light_value_lux' key"

def test_space_light_threshold_endpoint_returns_json(hid_log):
    """
    Test that the space light threshold endpoint returns JSON with expected keys.
    """
    from smibhid_http.website import SpaceLightThreshold
    from json import loads
    hid, log = hid_log
    space_light_threshold = SpaceLightThreshold()
    response = space_light_threshold.get("", hid.space_state, log)
    
    # Parse the JSON response
    response_data = loads(response)
    
    # Assert that the response contains the expected key
    assert "light_threshold_lux" in response_data, "Response should contain 'light_threshold_lux' key"