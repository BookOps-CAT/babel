from contextlib import nullcontext as does_not_raise
import logging
import shelve

import pytest
from bookops_nypl_platform import PlatformToken


from babel import paths
from babel.errors import BabelError
from babel.sierra_adapters.platform import NypPlatform


from tests.conftest import (
    MockPlatformSessionGetListResponseSuccess,
    MockPlatformSessionGetBibResponseSuccess,
    MockPlatformSessionGetItemsResponseSuccess,
)


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


@pytest.mark.parametrize("arg", [[], "foo", 1])
def test_invalid_library_arg(caplog, arg, dummy_user_data, mock_vault):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BabelError) as exc:
            NypPlatform(arg, dummy_user_data)

        assert "Invalid library argument passed" in str(exc.value)

    assert (
        f"Invalid library argument passed to NypPlatform. Unable to open Platfrom session."
        in caplog.text
    )


@pytest.mark.parametrize("arg", [None, "", "branches", "research"])
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

    assert f"Initiating session with Platform for {arg}." in caplog.text


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


def test_parse_bibliographic_data(mock_platform):
    response = MockPlatformSessionGetBibResponseSuccess()
    data = response.json()

    assert mock_platform._parse_bibliographic_data(data) == dict(
        bibNo="21742979",
        title="The ABC of It : why children's books matter",
        author="Marcus, Leonard S., 1950- author.",
        pubDate=2019,
        pubPlace="Minnesota",
    )


def test_get_bib_success(mock_platform, mock_platform_session_get_bib_response_200http):
    result = mock_platform._get_bib("21742979")
    assert isinstance(result, dict)


def test_get_bib_failure(
    mock_platform, mock_platform_session_response_404http_not_found
):
    result = mock_platform._get_bib("21742979")
    assert result is None


def test_get_bib_exception(caplog, mock_platform, mock_platform_error):
    with caplog.at_level(logging.WARNING):
        with does_not_raise():
            result = mock_platform._get_bib("21742979")

    assert result is None
    assert "Unable to retireve bib 21742979 data from Platform."


@pytest.mark.parametrize(
    "library,arg,expectation",
    [
        ("branches", ["ca"], True),
        ("branches", ["rc", "ca"], True),
        ("branches", ["sn", "ma"], True),
        ("branches", ["my"], False),
        ("branches", [], True),
        ("branches", ["ia"], True),
        ("research", ["ia"], True),
        ("research", ["ma"], True),
        ("research", ["sn", "ma"], True),
        ("research", ["sn", "ca"], False),
    ],
)
def test_has_matching_location(mock_platform, library, arg, expectation):
    mock_platform.library = library
    assert mock_platform._has_matching_location(arg) == expectation


def test_order_locations(mock_platform):
    response = MockPlatformSessionGetListResponseSuccess().json()
    data = response["data"][0]

    assert mock_platform._order_locations(data) == ["ma"]


def test_parse_item_data(mock_platform):
    response = MockPlatformSessionGetItemsResponseSuccess()
    data = response.json()

    result = mock_platform._parse_item_data(data)

    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, dict)

        assert sorted(item.keys()) == sorted(
            ["locCode", "locName", "status", "circ", "lastCheck"]
        )

    item = result[0]
    assert item["locCode"] == "sgj0v"
    assert item["locName"] == "St. George Children's Non-Print Media"
    assert item["status"] == "CLOSED BRANCH"
    assert item["circ"] == "29+21"
    assert item["lastCheck"] == "2020-12-15"


def test_get_items_success(
    mock_platform, mock_platform_session_get_items_response_200http
):
    result = mock_platform._get_items("21742979")

    assert isinstance(result, dict)


def test_get_items_failed(
    mock_platform, mock_platform_session_response_404http_not_found
):
    result = mock_platform._get_items("21742979")

    assert result is None


def test_get_items_exception(caplog, mock_platform, mock_platform_error):
    with caplog.at_level(logging.WARNING):
        with does_not_raise():
            result = mock_platform._get_items("21742979")

    assert result is None
    assert "Unable to retrieve bib 21742979 item data from Platform." in caplog.text


def test_get_bib_and_item_data_success(
    mock_platform,
    mock_platform_get_bib_success,
    mock_platform_session_get_items_response_200http,
):
    result = mock_platform.get_bib_and_item_data("21742979")
    assert isinstance(result, tuple)
    assert isinstance(result[0], dict)
    assert isinstance(result[1], list)
    for item in result[1]:
        assert isinstance(item, dict)


def test_get_bib_and_item_data_no_items(
    mock_platform,
    mock_platform_session_get_bib_response_200http,
    mock_platform_get_items_not_found,
):
    result = mock_platform.get_bib_and_item_data("21742979")
    assert isinstance(result, tuple)
    assert isinstance(result[0], dict)
    assert result[1] is None


def test_get_bib_and_item_data_no_bib(
    mock_platform,
    mock_platform_get_bib_not_found,
    mock_platform_session_get_items_response_200http,
):
    result = mock_platform.get_bib_and_item_data("21742979")
    assert isinstance(result, tuple)
    assert result[0] is None


def test_get_bib_and_item_data_error(mock_platform, mock_platform_error):
    with does_not_raise():
        result = mock_platform.get_bib_and_item_data("21742979")
        assert result == (None, None)
