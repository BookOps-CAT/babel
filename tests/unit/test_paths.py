import os

from babel.paths import get_user_data_handle


def test_get_user_data_handle():
    app_data = os.getenv("LOCALAPPDATA")
    user_data_fh = os.path.join(app_data, "Babel\\user_data")
    assert get_user_data_handle() == user_data_fh
