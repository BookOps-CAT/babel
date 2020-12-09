import os
import shelve

from babel.installer import (
    is_configured,
    has_user_data_file,
    has_creds_in_vault,
    has_db_config_in_user_data,
)


import pytest


def test_has_user_data_file():
    # assert has_user_data_file() is True
    has_user_data_file() is True


def test_has_db_config_in_user_true(tmpdir):
    u = os.path.join(tmpdir, "user_data")
    u = shelve.open(u)
    u["db_config"] = {"db_name": "test_app"}

    assert has_db_config_in_user_data(u) is True
    u.close()


def test_has_db_config_in_user_false(tmpdir):
    u = os.path.join(tmpdir, "user_data")
    u = shelve.open(u)
    u["foo"] = {"bar"}

    assert has_db_config_in_user_data(u) is False
    u.close()


@pytest.mark.parametrize(
    "arg1,arg2,expectation", [("test_app", "test_user", True), ("foo", "bar", False)]
)
def test_has_creds_in_vault(arg1, arg2, expectation, fake_vault_creds):
    assert has_creds_in_vault(arg1, arg2) == expectation


def test_is_configured_true():
    assert is_configured() is True
