import os
import shelve

import pytest
import keyring
from keyring.backends.Windows import WinVaultKeyring
import requests

from babel.sierra_adapters.middleware import NypPlatform

from babel import paths


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
        user_data = shelve.open(user_data_fh)
        user_data["db_config"] = dict(
            DB_NAME="babeltest", DB_HOST="localhost", DB_USER="test", DB_PORT="3306"
        )
        user_data["nyp_platform"] = dict(
            PLATFORM_OAUTH_SERVER="oauth_server", PLATFORM_CLIENT_ID="platform-client"
        )
        user_data["bpl_solr"] = dict(SOLR_ENDPOINT="solr_url")
        user_data.close()
        return user_data_fh

    monkeypatch.setattr(paths, "get_user_data_handle", _patch)


# NYPL Platform fixtures


class MockPlatformAuthServerResponseSuccess:
    """Simulates oauth server response to successful token request"""

    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
            "access_token": "token_string_here",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "scopes_here",
            "id_token": "token_string_here",
        }


class MockPlatformAuthServerResponseFailure:
    """Simulates oauth server response to successful token request"""

    def __init__(self):
        self.status_code = 400

    def json(self):
        return {"error": "No grant_type specified", "error_description": None}


class MockPlatformSessionResponseSuccess:
    """Simulates NYPL Platform query successful response"""

    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {
            "data": {
                "id": "18578797",
                "deleted": False,
                "suppressed": False,
                "title": "Zendegi",
                "author": "Egan, Greg, 1961-",
                "standardNumbers": ["9781597801744", "1597801747"],
                "controlNumber": "2010074825",
                "fixedFields": {
                    "24": {"label": "Language", "value": "eng", "display": "English"},
                    "107": {"label": "MARC Type", "value": " ", "display": None},
                },
                "varFields": [
                    {
                        "fieldTag": "c",
                        "marcTag": "091",
                        "ind1": " ",
                        "ind2": " ",
                        "content": None,
                        "subfields": [
                            {"tag": "a", "content": "SCI-FI"},
                            {"tag": "c", "content": "EGAN"},
                        ],
                    },
                    {
                        "fieldTag": "o",
                        "marcTag": "001",
                        "ind1": " ",
                        "ind2": " ",
                        "content": "2010074825",
                        "subfields": None,
                    },
                    {
                        "fieldTag": "t",
                        "marcTag": "245",
                        "ind1": "1",
                        "ind2": "0",
                        "content": None,
                        "subfields": [
                            {"tag": "a", "content": "Zendegi /"},
                            {"tag": "c", "content": "Greg Egan."},
                        ],
                    },
                    {
                        "fieldTag": "y",
                        "marcTag": "003",
                        "ind1": " ",
                        "ind2": " ",
                        "content": "OCoLC",
                        "subfields": None,
                    },
                ],
            },
            "count": 1,
            "totalCount": 0,
            "statusCode": 200,
            "debugInfo": [],
        }


class MockPlatformSessionResponseDeletedRecord:
    """Simulates NYPL Platform query response for deleted record"""

    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {
            "data": {
                "id": "19099433",
                "nyplSource": "sierra-nypl",
                "nyplType": "bib",
                "updatedDate": None,
                "createdDate": "2017-08-23T17:59:35-04:00",
                "deletedDate": "2011-09-15",
                "deleted": True,
                "locations": [],
                "suppressed": None,
                "lang": None,
                "title": None,
                "author": None,
                "materialType": None,
                "bibLevel": None,
                "publishYear": None,
                "catalogDate": None,
                "country": None,
                "normTitle": None,
                "normAuthor": None,
                "standardNumbers": [],
                "controlNumber": "",
                "fixedFields": [],
                "varFields": [],
            },
            "count": 1,
            "totalCount": 0,
            "statusCode": 200,
            "debugInfo": [],
        }


class MockPlatformSessionResponseNotFound:
    """Simulates NYPL Platform failed query response"""

    def __init__(self):
        self.status_code = 404
        self.url = "query_url_here"

    def json(self):
        return {
            "statusCode": 404,
            "type": "exception",
            "message": "No record found",
            "error": [],
            "debugInfo": [],
        }


@pytest.fixture
def mock_platform_post_token_response_200http(monkeypatch):
    def mock_oauth_server_response(*args, **kwargs):
        return MockPlatformAuthServerResponseSuccess()

    monkeypatch.setattr(requests, "post", mock_oauth_server_response)


@pytest.fixture
def mock_platform_post_token_response_400http(monkeypatch):
    def mock_oauth_server_response(*args, **kwargs):
        return MockPlatformAuthServerResponseFailure

    monkeypatch.setattr(requests, "post", mock_oauth_server_response)


@pytest.fixture
def mock_platform_session_response_200http(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionResponseSuccess()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_response_200http_deleted_record(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionResponseDeletedRecord()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_response_404http_not_found(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionResponseNotFound()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform(
    mock_user_data, mock_vault, mock_platform_post_token_response_200http
):
    with NypPlatform("branch") as middleware:
        yield middleware
