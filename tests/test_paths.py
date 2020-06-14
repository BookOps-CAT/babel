import os

import pytest


if os.name == "posix":
    def test_mac_paths(mock_mac):
        from babel import paths
        assert paths.USER_NAME == "testuser"
        assert paths.APP_DIR == "/Users/testuser/Applications/Babel"
        assert paths.APP_DATA_DIR == "/Users/testuser/AppData/Babel"
        assert paths.DEV_LOG_PATH == "/Users/testuser/AppData/Babel/log/dev_babellog.out"
        assert paths.PROD_LOG_PATH == "/Users/testuser/AppData/Babel/log/babellog.out"
        assert paths.USER_DATA == "/Users/testuser/AppData/Babel/user_data"


if os.name == "nt":
    def test_windows_paths(mock_windows):
        from babel import paths
        assert paths.USER_NAME == "testuser"
        assert paths.APP_DIR == "C:/Babel2"
        assert paths.APP_DATA_DIR == "C:/Users/testuser/AppData/Local/Babel"
        assert paths.DEV_LOG_PATH == "C:/Users/testuser/AppData/Local/Babel/log/dev_babellog.out"
        assert paths.PROD_LOG_PATH == "C:/Users/testuser/AppData/Local/Babel/log/babellog.out"
        assert paths.MY_DOCS == "C:/Users/testuser/Documents"
        assert paths.USER_DATA == "C:/Users/testuser/AppData/Local/user_data"