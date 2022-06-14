import os
import shelve

from bookops_nypl_platform import PlatformToken
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
def dummy_user_data_handle(tmpdir):
    return os.path.join(tmpdir, "user_data")


@pytest.fixture
def dummy_user_data(dummy_user_data_handle, mock_platform_post_token_response_200http):
    user_data = shelve.open(dummy_user_data_handle)
    user_data["db_config"] = dict(
        DB_NAME="babeltest", DB_HOST="localhost", DB_USER="test", DB_PORT="3306"
    )
    user_data["nyp_platform"] = dict(
        PLATFORM_OAUTH_SERVER="oauth_server", PLATFORM_CLIENT_ID="platform-client"
    )
    user_data["platform_token"] = PlatformToken(
        "platform-client", "platform-secret", "oauth_server"
    )
    user_data["bpl_solr"] = dict(SOLR_ENDPOINT="solr_url")
    user_data.close()
    return dummy_user_data_handle


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


class MockPlatformSessionGetBibResponseSuccess:
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


class MockPlatformSessionGetBibResponseDeletedRecord:
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


class MockPlatformSessionGetListResponseSuccess:
    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {
            "data": [
                {
                    "id": "21776219",
                    "nyplSource": "sierra-nypl",
                    "nyplType": "bib",
                    "updatedDate": "2021-11-13T09:43:26-05:00",
                    "createdDate": "2019-04-11T14:08:06-04:00",
                    "deletedDate": None,
                    "deleted": False,
                    "locations": [
                        {"code": "mal", "name": "SASB - Service Desk Rm 315"}
                    ],
                    "suppressed": False,
                    "lang": {"code": "eng", "name": "English"},
                    "title": "The ABC of It : why children's books matter",
                    "author": "Marcus, Leonard S., 1950- author.",
                    "materialType": {"code": "a  ", "value": "BOOK/TEXT"},
                    "bibLevel": {"code": "m", "value": "MONOGRAPH"},
                    "publishYear": 2019,
                    "catalogDate": "2019-09-25",
                    "country": {"code": "mnu", "name": "Minnesota"},
                    "normTitle": "abc of it why childrens books matter",
                    "normAuthor": "marcus leonard s 1950 author",
                    "standardNumbers": ["9781517908010", "1517908019"],
                    "controlNumber": "1076512835",
                    "fixedFields": {
                        "24": {
                            "label": "Language",
                            "value": "eng",
                            "display": "English",
                        },
                    },
                    "varFields": [
                        {
                            "fieldTag": "a",
                            "marcTag": "100",
                            "ind1": "1",
                            "ind2": " ",
                            "content": None,
                            "subfields": [
                                {"tag": "a", "content": "Marcus, Leonard S.,"},
                                {"tag": "d", "content": "1950-"},
                                {"tag": "e", "content": "author."},
                            ],
                        },
                        {
                            "fieldTag": "o",
                            "marcTag": "001",
                            "ind1": " ",
                            "ind2": " ",
                            "content": "1076512835",
                            "subfields": None,
                        },
                        {
                            "fieldTag": "t",
                            "marcTag": "245",
                            "ind1": "1",
                            "ind2": "4",
                            "content": None,
                            "subfields": [
                                {"tag": "a", "content": "The ABC of It :"},
                                {
                                    "tag": "b",
                                    "content": "why children's books matter /",
                                },
                                {
                                    "tag": "c",
                                    "content": "Leonard S. Marcus ; foreword by Lisa Von Drasek.",
                                },
                            ],
                        },
                        {
                            "fieldTag": "y",
                            "marcTag": "910",
                            "ind1": " ",
                            "ind2": " ",
                            "content": None,
                            "subfields": [{"tag": "a", "content": "RL"}],
                        },
                        {
                            "fieldTag": "_",
                            "marcTag": None,
                            "ind1": None,
                            "ind2": None,
                            "content": "00000cam a2200517 i 4500",
                            "subfields": None,
                        },
                    ],
                },
                {
                    "id": "21742979",
                    "nyplSource": "sierra-nypl",
                    "nyplType": "bib",
                    "updatedDate": "2022-02-07T03:33:12-05:00",
                    "createdDate": "2019-02-13T16:29:19-05:00",
                    "deletedDate": None,
                    "deleted": False,
                    "locations": [
                        {"code": "fta", "name": "53rd Street Adult"},
                        {"code": "fea", "name": "58th Street Adult"},
                        {"code": "ssa", "name": "67th Street Adult"},
                        {"code": "bca", "name": "Bronx Library Center Adult"},
                        {"code": "bta", "name": "Battery Park Adult "},
                        {"code": "dya", "name": "Spuyten Duyvil Adult "},
                        {"code": "epa", "name": "Epiphany Adult"},
                        {"code": "hka", "name": "Huguenot Park Adult"},
                        {"code": "mla", "name": "Mulberry Street Adult"},
                        {"code": "moa", "name": "Mosholu Adult"},
                        {"code": "nda", "name": "New Dorp Adult"},
                        {"code": "pka", "name": "Parkchester Adult"},
                        {"code": "rsa", "name": "Riverside Adult"},
                        {"code": "rta", "name": "Richmondtown Adult"},
                        {"code": "sga", "name": "St. George Adult"},
                        {"code": "tha", "name": "Todt Hill-Westerleigh Adult"},
                        {"code": "tsa", "name": "Tompkins Square Adult"},
                        {"code": "wla", "name": "Woodlawn Heights Adult"},
                    ],
                    "suppressed": False,
                    "lang": {"code": "eng", "name": "English"},
                    "title": "The ABC of It : why children's books matter",
                    "author": "Marcus, Leonard S., 1950- author.",
                    "materialType": {"code": "a  ", "value": "BOOK/TEXT"},
                    "bibLevel": {"code": "m", "value": "MONOGRAPH"},
                    "publishYear": 2019,
                    "catalogDate": "2019-03-25",
                    "country": {"code": "mnu", "name": "Minnesota"},
                    "normTitle": "abc of it why childrens books matter",
                    "normAuthor": "marcus leonard s 1950 author",
                    "standardNumbers": ["9781517908010", "1517908019"],
                    "controlNumber": "1076512835",
                    "fixedFields": {
                        "24": {
                            "label": "Language",
                            "value": "eng",
                            "display": "English",
                        },
                    },
                    "varFields": [
                        {
                            "fieldTag": "a",
                            "marcTag": "100",
                            "ind1": "1",
                            "ind2": " ",
                            "content": None,
                            "subfields": [
                                {"tag": "a", "content": "Marcus, Leonard S.,"},
                                {"tag": "d", "content": "1950-"},
                                {"tag": "e", "content": "author."},
                            ],
                        },
                        {
                            "fieldTag": "c",
                            "marcTag": "091",
                            "ind1": " ",
                            "ind2": " ",
                            "content": None,
                            "subfields": [
                                {"tag": "a", "content": "809.8928"},
                                {"tag": "c", "content": "M"},
                            ],
                        },
                        {
                            "fieldTag": "o",
                            "marcTag": "001",
                            "ind1": " ",
                            "ind2": " ",
                            "content": "1076512835",
                            "subfields": None,
                        },
                        {
                            "fieldTag": "t",
                            "marcTag": "245",
                            "ind1": "1",
                            "ind2": "4",
                            "content": None,
                            "subfields": [
                                {"tag": "a", "content": "The ABC of It :"},
                                {
                                    "tag": "b",
                                    "content": "why children's books matter /",
                                },
                                {
                                    "tag": "c",
                                    "content": "Leonard S. Marcus ; foreword by Lisa Von Drasek.",
                                },
                            ],
                        },
                        {
                            "fieldTag": "_",
                            "marcTag": None,
                            "ind1": None,
                            "ind2": None,
                            "content": "00000cam a22004818i 4500",
                            "subfields": None,
                        },
                    ],
                },
            ],
            "count": 2,
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
def mock_platform_session_get_bib_response_200http(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionGetBibResponseSuccess()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_get_bib_response_200http_deleted_record(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionGetBibResponseDeletedRecord()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_response_404http_not_found(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionResponseNotFound()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform(
    dummy_user_data, mock_vault, mock_platform_post_token_response_200http
):
    with NypPlatform("branch", dummy_user_data) as middleware:
        yield middleware
