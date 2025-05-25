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

def test_firmware_endpoint_returns_current_firmware_version():
    """
    Test that the firmware endpoint returns the current firmware version.
    """
    from json import dumps
    from lib.ulogging import uLogger
    from lib.hid import HID
    log = uLogger("test_firmware_endpoint")
    hid = HID()
    from smibhid_http.website import Version
    version = Version()
    response = version.get("", hid, log)    
    assert response == dumps("1.4.0"), f"Expected '\"1.4.0\"', got '{response}'"
