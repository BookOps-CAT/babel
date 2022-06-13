from contextlib import nullcontext as does_not_raise

import pytest
from bookops_nypl_platform import PlatformToken

from babel.sierra_adapters.middleware import NypPlatform


@pytest.mark.parametrize("arg", [None, "branch", "research"])
def test_NypPlatform_valid_library_arg(
    arg, mock_user_data, mock_vault, mock_platform_post_token_response_200http
):
    with does_not_raise():
        session = NypPlatform(arg)

        assert session.library == arg
        assert session.agent == "BookOps/Babel"


@pytest.mark.parametrize("arg", ["", "foo", 1])
def test_NypPlatform_invalid_library_arg(arg, mock_vault):
    with pytest.raises(ValueError) as exc:
        NypPlatform(arg)

    assert "Invalid library argument passed" in str(exc.value)


def test_NypPlatform_get_credentials(mock_platform):
    result = mock_platform._get_credentials()
    assert isinstance(result, tuple)
    assert result == ("platform-client", "babel_key", "oauth_server")


def test_NypPlatfrom_get_token(mock_platform):
    token = mock_platform._get_token("platform-client", "babel_key", "oauth_server")
    assert isinstance(token, PlatformToken)
