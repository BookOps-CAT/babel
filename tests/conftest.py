import os
import shelve

from bookops_nypl_platform import PlatformToken
from bookops_nypl_platform.errors import BookopsPlatformError
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


class MockPlatformException:
    def __init__(self, *args, **kwargs):
        raise BookopsPlatformError


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
    """Simulates NYPL Platform query for single bib successful response"""

    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {
            "data": {
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
            "count": 1,
            "totalCount": 0,
            "statusCode": 200,
            "debugInfo": [],
        }


class MockPlatformSessionGetListResponseSuccess:
    """Simuilates Platform reponse to get list of bib request"""

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


class MockPlatformSessionGetItemsResponseSuccess:
    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {
            "data": [
                {
                    "nyplSource": "sierra-nypl",
                    "bibIds": ["21742979"],
                    "id": "28305229",
                    "nyplType": "item",
                    "updatedDate": "2022-03-21T13:56:59-04:00",
                    "createdDate": "2012-03-06T16:48:11-05:00",
                    "deletedDate": None,
                    "deleted": False,
                    "location": {
                        "code": "sgj0v",
                        "name": "St. George Children's Non-Print Media",
                    },
                    "status": {
                        "code": "c",
                        "display": "CLOSED BRANCH",
                        "duedate": None,
                    },
                    "barcode": "33333291169072",
                    "callNumber": "J DVD TV ELMO",
                    "itemType": None,
                    "fixedFields": {
                        "76": {
                            "label": "Total Checkouts",
                            "value": "29",
                            "display": None,
                        },
                        "77": {
                            "label": "Total Renewals",
                            "value": "21",
                            "display": None,
                        },
                        "78": {
                            "label": "Last Checkout Date",
                            "value": "2020-12-15T21:10:41Z",
                            "display": None,
                        },
                        "79": {
                            "label": "Location",
                            "value": "sgj0v",
                            "display": "St. George Children's Non-Print Media",
                        },
                    },
                },
                {
                    "nyplSource": "sierra-nypl",
                    "bibIds": ["19541524"],
                    "id": "28305235",
                    "nyplType": "item",
                    "updatedDate": "2021-07-29T20:12:25-04:00",
                    "createdDate": "2012-03-06T16:48:00-05:00",
                    "deletedDate": None,
                    "deleted": False,
                    "location": {
                        "code": "bcj0v",
                        "name": "Bronx Library Center Children's Non-Print Media",
                    },
                    "status": {"code": "t", "display": "IN TRANSIT", "duedate": None},
                    "barcode": "33333291169130",
                    "callNumber": "J DVD TV ELMO",
                    "itemType": None,
                    "fixedFields": {
                        "76": {
                            "label": "Total Checkouts",
                            "value": "47",
                            "display": None,
                        },
                        "77": {
                            "label": "Total Renewals",
                            "value": "20",
                            "display": None,
                        },
                        "78": {
                            "label": "Last Checkout Date",
                            "value": "2019-07-31T19:15:49Z",
                            "display": None,
                        },
                        "79": {
                            "label": "Location",
                            "value": "bcj0v",
                            "display": "Bronx Library Center Children's Non-Print Media",
                        },
                    },
                },
            ],
            "count": 2,
            "totalCount": 0,
            "statusCode": 200,
            "debugInfo": [],
        }


class MockPlatformSessionIsResearchResponseSuccessTrue:
    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {"nyplSource": "sierra-nypl", "id": "21776219", "isResearch": True}


class MockPlatformSessionIsResearchResponseSuccessFalse:
    def __init__(self):
        self.status_code = 200
        self.url = "request_url_here"

    def json(self):
        return {"nyplSource": "sierra-nypl", "id": "21742979", "isResearch": False}


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
def mock_platform_session_get_list_response_200http(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionGetListResponseSuccess()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_get_bib_response_200http(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionGetBibResponseSuccess()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_get_items_response_200http(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionGetItemsResponseSuccess()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_is_research_response_200http_true(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionIsResearchResponseSuccessTrue()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_is_research_response_200http_false(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionIsResearchResponseSuccessFalse()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_session_response_404http_not_found(monkeypatch):
    def mock_api_response(*args, **kwargs):
        return MockPlatformSessionResponseNotFound()

    monkeypatch.setattr(requests.Session, "get", mock_api_response)


@pytest.fixture
def mock_platform_error(monkeypatch):
    monkeypatch.setattr(requests.Session, "get", MockPlatformException)


@pytest.fixture
def mock_platform(
    dummy_user_data, mock_vault, mock_platform_post_token_response_200http
):
    with NypPlatform("branches", dummy_user_data) as middleware:
        yield middleware


@pytest.fixture
def mock_platform_determine_library_matches(monkeypatch):
    def _patch(*args, **kwargs):
        return ["21742979"]

    monkeypatch.setattr(
        "babel.sierra_adapters.middleware.NypPlatform._determine_library_matches",
        _patch,
    )


@pytest.fixture
def mock_platform_determine_library_matches_none(monkeypatch):
    def _patch(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "babel.sierra_adapters.middleware.NypPlatform._determine_library_matches",
        _patch,
    )


@pytest.fixture
def mock_platform_determine_library_matches_error(monkeypatch):
    monkeypatch.setattr(
        "babel.sierra_adapters.middleware.NypPlatform._determine_library_matches",
        MockPlatformException,
    )


@pytest.fixture
def mock_platform_get_bib_success(monkeypatch):
    def _patch(*args, **kwargs):
        return MockPlatformSessionGetBibResponseSuccess().json()

    monkeypatch.setattr("babel.sierra_adapters.middleware.NypPlatform._get_bib", _patch)


@pytest.fixture
def mock_platform_get_items_not_found(monkeypatch):
    def _patch(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "babel.sierra_adapters.middleware.NypPlatform._get_items",
        _patch,
    )


@pytest.fixture
def mock_platform_get_bib_not_found(monkeypatch):
    def _patch(*args, **kwargs):
        return None

    monkeypatch.setattr("babel.sierra_adapters.middleware.NypPlatform._get_bib", _patch)
