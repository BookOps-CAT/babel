import json
import os
import shelve

import pytest


from babel.data.datastore import session_scope


@pytest.fixture
def mock_db_creds_from_vault(monkeypatch):
    def _patch(*args, **kwargs):
        with open(
            os.path.join(os.getenv("USERPROFILE"), ".babel/new-babel-prod-db.json"), "r"
        ) as f:
            db = json.load(f)
        return db["password"]

    monkeypatch.setattr("keyring.get_password", _patch)


@pytest.fixture
def dev_user_data(dummy_user_data_handle):
    # config needs to change to real dev db when ready

    user_fh = os.getenv("USERPROFILE")

    with open(os.path.join(user_fh, ".babel/new-babel-prod-db.json"), "r") as f:
        db = json.load(f)

    with open(os.path.join(user_fh, ".cred/.platform/tomasz_platform.json"), "r") as f:
        pl = json.load(f)

    with open(os.path.join(user_fh, ".cred/.solr/bpl-solr-prod.json"), "r") as f:
        sl = json.load(f)

    user_data = shelve.open(dummy_user_data_handle)
    user_data["db_config"] = dict(
        DB_NAME=db["db"], DB_HOST=db["host"], DB_USER=db["user"], DB_PORT=db["port"]
    )
    user_data["nyp_platform"] = dict(
        PLATFORM_OAUTH_SERVER=pl["oauth-server"], PLATFORM_CLIENT_ID=pl["client-id"]
    )
    user_data["platform_token"] = None
    user_data["bpl_solr"] = dict(SOLR_ENDPOINT=sl["endpoint"])
    user_data.close()
    return dummy_user_data_handle
