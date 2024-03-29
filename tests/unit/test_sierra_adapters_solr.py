from contextlib import nullcontext as does_not_raise
import logging
import shelve

import pytest

from babel.sierra_adapters.solr import BplSolr
from babel.errors import BabelError

from tests.conftest import MockSolrSessionResponseSuccess


def test_invalid_creds_fh(caplog):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BabelError) as exc:
            BplSolr("foo")

    assert "Invalid creds_fh argument passed." in caplog.text
    assert (
        "Valid path to user_data not provided. Unable to open BPL Solr session."
        in str(exc.value)
    )


def test_initiate_BplSolr(caplog, dummy_user_data):
    with caplog.at_level(logging.INFO):
        with does_not_raise():
            session = BplSolr(dummy_user_data)

    assert isinstance(session, BplSolr)
    assert session.headers["User-Agent"] == "BookOps/Babel"
    assert "Initiating session with BPL Solr." in caplog.text


def test_get_creds(caplog, dummy_user_data, mock_vault):
    with caplog.at_level(logging.DEBUG):
        session = BplSolr(dummy_user_data)

        result = session._get_creds()

    assert isinstance(result, tuple)
    assert result[0] == "solr_url"
    assert result[1] == "babel_key"

    assert "Obtaining Solr secret key." in caplog.text


def test_get_creds_malformed_user_data(caplog, dummy_user_data, mock_vault):
    with caplog.at_level(logging.ERROR):
        session = BplSolr(dummy_user_data)
        user_data = shelve.open(dummy_user_data)
        user_data.pop("bpl_solr", None)
        user_data.close()

        with pytest.raises(BabelError) as exc:
            result = session._get_creds()

    assert "Failed to find BPL Solr endpoint in user_data." in caplog.text
    assert "Unable to obtain BPL Solr credentials." in str(exc.value)


def test_get_creds_missing_client_key_in_vault(caplog, dummy_user_data, mock_no_vault):
    with caplog.at_level(logging.ERROR):
        with pytest.raises(BabelError) as exc:
            session = BplSolr(dummy_user_data)

        assert "Unable to obtain BPL Solr client-key from vault." in caplog.text
        assert "Unable to obtain BPL Solr credentials." in str(exc.value)


def test_get_bib(dummy_solr, mock_solr_search_success):
    result = dummy_solr._get_bib("11499389")

    assert isinstance(result, dict)


def test_get_bib_solr_error(caplog, dummy_solr, mock_solr_error):
    with caplog.at_level(logging.WARNING):
        with does_not_raise():
            result = dummy_solr._get_bib("11499389")

    assert result is None
    assert "Unable to retrieve bib 11499389 data from Solr." in caplog.text


def test_get_bib_nos_success(dummy_solr):
    response = MockSolrSessionResponseSuccess()

    assert dummy_solr._get_bib_nos(response) == ["11499389", "11499399"]


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (
            "880-04 al-Qāhirah : Dār al-Shurūq, 2014.",
            "al-Qāhirah : Dār al-Shurūq, 2014.",
        ),
        (
            "880-03 al-Qāhirah : Dār al-Shurūq, 2014.",
            "al-Qāhirah : Dār al-Shurūq, 2014.",
        ),
        ("New York: Tor, 2016.", "New York: Tor, 2016."),
    ],
)
def test_normalize_publisher(dummy_solr, arg, expectation):
    assert dummy_solr._normalize_publisher(arg) == expectation


def test_parse_bibliographic_data(dummy_solr):
    data = MockSolrSessionResponseSuccess().json()
    assert dummy_solr._parse_bibliographic_data(data) == {
        "bibNo": "11499389",
        "title": "Harry Potter and the half-blood prince",
        "author": "",
        "pubDate": "",
        "pubPlace": "[Burbank, Calif.] : Warner Home Video, [2009] ©2009 ",
    }


def test_parse_item_data(dummy_solr):
    data = MockSolrSessionResponseSuccess().json()
    results = dummy_solr._parse_item_data(data)

    assert isinstance(results, list)

    item = results[0]
    assert item == {
        "locCode": "61jdv",
        "locName": "Wash Irving Juv DVD",
        "status": "DELETE",
        "circ": "n/a",
        "lastCheck": "n/a",
    }


def test_parse_item_data_not_found(dummy_solr):
    # scenario when there is only brief order record without items attached
    data = MockSolrSessionResponseSuccess().json()
    bib = data["response"]["docs"][0]
    bib.pop("sm_item_data", None)
    data["response"]["docs"][0] = bib

    results = dummy_solr._parse_item_data(data)

    assert results == []


@pytest.mark.parametrize("arg", ["isbn"])
def test_search_success(dummy_user_data, mock_solr_search_success, mock_vault, arg):
    with BplSolr(dummy_user_data) as solr:
        result = solr.search(["1419864173"], arg)

    assert result == (True, "11499389,11499399")


def test_search_not_found(dummy_user_data, mock_vault, mock_solr_search_not_found):
    with BplSolr(dummy_user_data) as solr:
        result = solr.search(["1419864173"], "isbn")

    assert result == (False, None)


def test_search_unsupported(caplog, dummy_user_data, mock_vault):
    with caplog.at_level(logging.WARNING):
        with BplSolr(dummy_user_data) as solr:
            result = solr.search(["1419864173"], None)

    assert (
        "Attempting unsupported search in BPL Solr. Only ISBN and UPC searches are permitted."
        in caplog.text
    )
    assert result == (False, None)
