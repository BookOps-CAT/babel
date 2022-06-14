from contextlib import nullcontext as does_not_raise
import logging
import shelve

import pytest
from bookops_nypl_platform import PlatformToken


from babel import paths
from babel.errors import BabelError
from babel.sierra_adapters.middleware import NypPlatform


from tests.conftest import MockPlatformSessionGetListResponseSuccess


@pytest.mark.parametrize("arg", [None, "branch", "research"])
def test_NypPlatform_valid_library_arg(
    caplog,
    arg,
    dummy_user_data,
    mock_vault,
    mock_platform_post_token_response_200http,
):
    with caplog.at_level(logging.INFO):
        with does_not_raise():
            session = NypPlatform(arg, dummy_user_data)

            assert session.library == arg
            assert session.agent == "BookOps/Babel"

    assert "Initiating session with Platform." in caplog.text


@pytest.mark.parametrize("arg", ["", "foo", 1])
def test_NypPlatform_invalid_library_arg(caplog, arg, dummy_user_data, mock_vault):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BabelError) as exc:
            NypPlatform(arg, dummy_user_data)

        assert "Invalid library argument passed" in str(exc.value)

    assert (
        f"Invalid library argument passed to NypPlatform. Unable to open Platfrom session."
        in caplog.text
    )


def test_NypPlatform_get_credentials(caplog, dummy_user_data, mock_platform):
    user_data = shelve.open(dummy_user_data)
    with caplog.at_level(logging.DEBUG):
        result = mock_platform._get_credentials(user_data)
    assert "Obtaining Platform credentials." in caplog.text
    assert result == ("platform-client", "babel_key", "oauth_server")


def test_NypPlatform_get_credentials_user_data_malformed(
    caplog, dummy_user_data, mock_platform
):
    user_data = shelve.open(dummy_user_data)
    user_data.pop("nyp_platform", None)

    with caplog.at_level(logging.ERROR):
        result = mock_platform._get_credentials(user_data)

    assert "Failed to find Platform credentials in user_data." in caplog.text
    assert result == (
        None,
        "babel_key",
        None,
    )  # because of mocking the vault the second value is not usual None
    user_data.close()


def test_NypPlatform_get_token_in_user_data(caplog, mock_platform):
    with caplog.at_level(logging.DEBUG):
        token = mock_platform._get_token()
    assert isinstance(token, PlatformToken)
    assert "Obtaining Platform access token." in caplog.text
    assert "Found Platform access token in user_data."


def test_NypPlatform_get_token_not_in_user_data(caplog, dummy_user_data, mock_platform):
    with caplog.at_level(logging.DEBUG):
        user_data = shelve.open(dummy_user_data)
        user_data.pop("platform_token", None)
        user_data.close()

        token = mock_platform._get_token()

    assert "Failed to find access token in user_data." in caplog.text
    assert "Requesting new Platform access token." in caplog.text
    assert isinstance(token, PlatformToken)


def test_NypPlatform_get_bib_nos(mock_platform):
    response = MockPlatformSessionGetListResponseSuccess()
    result = mock_platform._get_bib_nos(response)
    assert result == ["21776219", "21742979"]
