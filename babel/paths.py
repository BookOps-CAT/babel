import os


USER_NAME = os.environ["USERNAME"]
APP_DIR = "C:\\Program Files\\Babel"
APP_DATA_DIR = os.path.join(os.environ["LOCALAPPDATA"], "Babel")
DEV_LOG_PATH = os.path.join(APP_DATA_DIR, "log/dev_babellog.out")
PROD_LOG_PATH = os.path.join(APP_DATA_DIR, "log/babellog.out")
MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
USER_DATA = os.path.join(APP_DATA_DIR, "user_data")


def get_user_data_handle():
    return os.path.join(os.path.join(os.getenv("LOCALAPPDATA"), "Babel"), "user_data")
