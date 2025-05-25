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