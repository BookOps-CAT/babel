import os

# Windows
if os.name == "nt":
    USER_NAME = os.environ['USERNAME']
    APP_DIR = 'C:\\Babel2'
    APP_DATA_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Babel')
    DEV_LOG_PATH = os.path.join(APP_DATA_DIR, 'log/dev_babellog.out')
    PROD_LOG_PATH = os.path.join(APP_DATA_DIR, 'log/babellog.out')
    MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
    USER_DATA = os.path.join(APP_DATA_DIR, 'user_data')

# Mac
elif os.name == "posix":
    print(os.environ)
    USER_NAME = os.environ["USER"]
    APP_DIR = os.path.join(os.environ["HOME"], "Applications/Babel")
    APP_DATA_DIR = os.path.join(os.environ["HOME"], "AppData/Babel")
    DEV_LOG_PATH = os.path.join(APP_DATA_DIR, "log/dev_babellog.out")
    PROD_LOG_PATH = os.path.join(APP_DATA_DIR, "log/babellog.out")
    MY_DOCS = os.path.join(os.environ["HOME"], "Documents")
    USER_DATA = os.path.join(APP_DATA_DIR, "user_data")
