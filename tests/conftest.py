import pytest

import keyring
from keyring.backends.Windows import WinVaultKeyring


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


@pytest.fixture
def mock_user_data(monkeypatch, tmpdir):
    def _patch(*args, **kwargs):
        user_data_fh = os.path.join(tmpdir, "user_data")
        user_data = shelve.open()

        user_data.close()
        return user_data_fh

    monkeypatch.setattr("babel.paths.get_user_data_handle", _patch)
