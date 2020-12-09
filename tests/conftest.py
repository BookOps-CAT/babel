import os
import shelve

import pytest

import keyring
from keyring.backends.Windows import WinVaultKeyring


@pytest.fixture
def mock_paths(monkeypatch, tmpdir):
    loc_data_dir = tmpdir
    app_data_dir = os.path.join(loc_data_dir, "babel")
    os.mkdir(app_data_dir)
    u = shelve.open(os.path.join(app_data_dir, "user_data"))
    u["db_config"] = {
        "db_config": "test_app",
        "host": "test_host",
        "port": "test_port",
        "user": "test_user",
    }
    u.close()
    monkeypatch.setenv("LOCALAPPDATA", f"{loc_data_dir}")


@pytest.fixture
def fake_vault_creds():
    keyring.set_keyring(WinVaultKeyring())
    keyring.set_password("test_app", "test_user", "test_passw")
    yield

    keyring.delete_password("test_app", "test_user")
