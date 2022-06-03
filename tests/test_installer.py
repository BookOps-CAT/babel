"""
Tests installer application.
"""

import keyring
import pytest

from babel.installer import has_creds_config_in_user_data, has_creds_in_vault


def test_has_creds_config_in_user_data_missing_key(mock_user_data_file):
    u = mock_user_data_file
    u.pop("babel", None)

    assert has_creds_config_in_user_data(u) is False


@pytest.mark.parametrize(
    "arg,expectation", [("spam", True), (None, False), ("", False)]
)
def test_has_creds_config_in_user_key_validation(mock_user_data_file, arg, expectation):
    u = mock_user_data_file
    u["babel"] = arg
    assert has_creds_config_in_user_data(u) == expectation


def test_has_creds_in_vault_success(mock_vault):
    assert has_creds_in_vault("babeldev", "babel") is True


def test_has_creds_in_vault_fail(mock_no_vault):
    result = keyring.get_password("foo", "bar")
    assert has_creds_in_vault("babeldev", "babel") is False
