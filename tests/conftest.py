import os
import shelve

import pytest

import keyring
from keyring.backends.Windows import WinVaultKeyring


@pytest.fixture
def mock_data_dir(tmpdir):
    local_data_dir = tmpdir
    return local_data_dir


@pytest.fixture
def mock_user_data_file(monkeypatch, mock_data_dir):
    u = shelve.open(os.path.join(mock_data_dir, "user_data"))
    u["db_config"] = {
        "db_config": "test_app",
        "host": "test_host",
        "port": "test_port",
        "user": "test_user",
    }
    u.close()


@pytest.fixture
def mock_env_vars(monkeypatch, mock_data_dir):
    monkeypatch.setenv("LOCALAPPDATA", f"{mock_data_dir}")


@pytest.fixture
def fake_vault_creds():
    keyring.set_keyring(WinVaultKeyring())
    keyring.set_password("test_app", "test_user", "test_passw")
    yield

    keyring.delete_password("test_app", "test_user")
