from contextlib import nullcontext as does_not_raise
import logging
import shelve

import pytest
from bookops_nypl_platform import PlatformToken


from babel import paths
from babel.errors import BabelError
from babel.sierra_adapters.middleware import NypPlatform


from tests.conftest import MockPlatformSessionGetListResponseSuccess


@pytest.mark.parametrize("arg", [None, "branches", "research"])
def test_valid_library_arg(
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

            session.close()

    assert "Initiating session with Platform." in caplog.text


@pytest.mark.parametrize("arg", ["", "foo", 1])
def test_invalid_library_arg(caplog, arg, dummy_user_data, mock_vault):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BabelError) as exc:
            NypPlatform(arg, dummy_user_data)

        assert "Invalid library argument passed" in str(exc.value)

    assert (
        f"Invalid library argument passed to NypPlatform. Unable to open Platfrom session."
        in caplog.text
    )


def test_get_credentials(caplog, dummy_user_data, mock_platform):
    user_data = shelve.open(dummy_user_data)
    with caplog.at_level(logging.DEBUG):
        result = mock_platform._get_credentials(user_data)
    assert "Obtaining Platform credentials." in caplog.text
    assert result == ("platform-client", "babel_key", "oauth_server")


def test_get_credentials_user_data_malformed(caplog, dummy_user_data, mock_platform):
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


def test_get_token_in_user_data(caplog, mock_platform):
    with caplog.at_level(logging.DEBUG):
        token = mock_platform._get_token()
    assert isinstance(token, PlatformToken)
    assert "Obtaining Platform access token." in caplog.text
    assert "Found Platform access token in user_data."


def test_get_token_not_in_user_data(caplog, dummy_user_data, mock_platform):
    with caplog.at_level(logging.DEBUG):
        user_data = shelve.open(dummy_user_data)
        user_data.pop("platform_token", None)
        user_data.close()

        token = mock_platform._get_token()

    assert "Failed to find access token in user_data." in caplog.text
    assert "Requesting new Platform access token." in caplog.text
    assert isinstance(token, PlatformToken)


def test_get_bib_nos(mock_platform):
    response = MockPlatformSessionGetListResponseSuccess()
    result = mock_platform._get_bib_nos(response)
    assert result == ["21776219", "21742979"]


@pytest.mark.parametrize(
    "target,response,expectation",
    [
        (None, True, True),
        (None, False, True),
        ("branches", True, False),
        ("branches", False, True),
        ("research", True, True),
        ("research", False, False),
    ],
)
def test_is_library_match(mock_platform, target, response, expectation):
    mock_platform.library = target
    assert mock_platform._is_library_match(response) == expectation


def test_determine_library_matches_research_true(
    mock_platform, mock_platform_session_is_research_response_200http_true
):
    mock_platform.library = "research"
    bib_nos = ["21776219", "21742979"]
    assert mock_platform._determine_library_matches(bib_nos) == ["21776219", "21742979"]


def test_determine_library_matches_branches_true(
    mock_platform, mock_platform_session_is_research_response_200http_false
):
    mock_platform.library = "branches"
    bib_nos = ["21776219", "21742979"]
    assert mock_platform._determine_library_matches(bib_nos) == ["21776219", "21742979"]


def test_determine_library_matches_research_false(
    mock_platform, mock_platform_session_is_research_response_200http_false
):
    mock_platform.library = "research"
    bib_nos = ["21776219", "21742979"]
    assert mock_platform._determine_library_matches(bib_nos) == []


def test_determine_library_matches_branches_false(
    mock_platform, mock_platform_session_is_research_response_200http_true
):
    mock_platform.library = "branches"
    bib_nos = ["21776219", "21742979"]
    assert mock_platform._determine_library_matches(bib_nos) == []


def test_search_success(
    mock_platform,
    mock_platform_determine_library_matches,
    mock_platform_session_get_list_response_200http,
):
    result = mock_platform.search(["isbn", "upc"])
    assert isinstance(result, tuple)
    assert result[0] is True
    assert result[1] == "21742979"


def test_search_no_matches_at_all(
    mock_platform, mock_platform_session_response_404http_not_found
):
    result = mock_platform.search(["isbn", "upc"])
    assert isinstance(result, tuple)
    assert result[0] is False
    assert result[1] is None


def test_search_no_matching_library(
    mock_platform,
    mock_platform_session_get_list_response_200http,
    mock_platform_determine_library_matches_none,
):
    result = mock_platform.search(["isbn", "upc"])
    assert isinstance(result, tuple)
    assert result[0] is False
    assert result[1] is None


def test_search_exception_on_search_standardnos_request(
    caplog, mock_platform, mock_platform_error
):
    with does_not_raise():
        with caplog.at_level(logging.WARNING):
            result = mock_platform.search(["isbn", "upc"])

    assert isinstance(result, tuple)
    assert result[0] is None
    assert result[1] is None

    assert "Encountered problem with Platform request. Skipping." in caplog.text


def test_search_exception_on_is_research_request(
    caplog,
    mock_platform,
    mock_platform_session_get_list_response_200http,
    mock_platform_determine_library_matches_error,
):
    with does_not_raise():
        with caplog.at_level(logging.WARNING):
            result = mock_platform.search(["isbn", "upc"])

    assert isinstance(result, tuple)
    assert result[0] is None
    assert result[1] is None

    assert "Encountered problem with Platform request. Skipping." in caplog.text


def test_store_token(mock_platform, dummy_user_data_handle):
    # make sure no token is stored in user_data
    mock_platform.library = "research"
    user_data = shelve.open(dummy_user_data_handle)
    user_data.pop("platform_token", None)
    user_data.close()

    mock_platform._store_token()

    user_data = shelve.open(dummy_user_data_handle)
    assert isinstance(user_data["platform_token"], PlatformToken)

    user_data.close()


def test_closing_platform_session(
    dummy_user_data_handle,
    dummy_user_data,
    mock_platform_post_token_response_200http,
    mock_vault,
):
    user_data = shelve.open(dummy_user_data_handle)
    user_data.pop("platform_token", None)
    user_data.close()

    with NypPlatform("branches", dummy_user_data) as platform:
        pass

    user_data = shelve.open(dummy_user_data_handle)
    assert isinstance(user_data["platform_token"], PlatformToken)
    user_data.close()
