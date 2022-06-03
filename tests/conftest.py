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
    u["babelprod"] = b"spam"
    yield u

    u.close()


@pytest.fixture
def mock_env_vars(monkeypatch, mock_data_dir):
    monkeypatch.setenv("LOCALAPPDATA", f"{mock_data_dir}")


@pytest.fixture
def mock_vault(monkeypatch):
    def _patch(*args, **kwargs):
        return "babel_key"

    monkeypatch.setattr("keyring.get_password", _patch)


@pytest.fixture
def mock_no_vault(monkeypatch):
    def _patch(*args, **kwargs):
        return None

    monkeypatch.setattr("keyring.get_password", _patch)
