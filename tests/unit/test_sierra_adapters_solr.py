from contextlib import nullcontext as does_not_raise
import logging
import shelve

import pytest


from babel.sierra_adapters.solr import BplSolr
from babel.errors import BabelError


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
