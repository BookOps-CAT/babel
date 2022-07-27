"""
Tests installer application.
"""

import keyring
import os
import pytest
import shelve

from babel.installer import (
    has_creds_config_in_user_data,
    has_creds_in_vault,
    is_configured,
)
from babel.paths import USER_DATA


def test_has_creds_config_in_user_data_missing_key(tmpdir):
    user_data = shelve.open(os.path.join(tmpdir, "user_data"))

    assert has_creds_config_in_user_data(user_data) is False

    user_data.close()


@pytest.mark.parametrize(
    "arg,expectation", [({"foo": "spam"}, True), (None, False), ({}, False)]
)
def test_has_creds_config_in_user_key_validation(tmpdir, arg, expectation):
    user_data = shelve.open(os.path.join(tmpdir, "user_data"))
    user_data["db_config"] = arg

    assert has_creds_config_in_user_data(user_data) == expectation

    user_data.close()


def test_has_creds_in_vault_success(mock_vault):
    assert has_creds_in_vault("babel", "babeldev") is True


def test_has_creds_in_vault_fail(mock_no_vault):
    result = keyring.get_password("foo", "bar")
    assert has_creds_in_vault("babeldev", "babeldev") is False


def test_is_configured():
    print(is_configured())
