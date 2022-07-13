from contextlib import nullcontext as does_not_raise
from babel.data.datastore import session_scope


def test_dev_session_scope(mock_db_creds_from_vault, dev_user_data):
    with does_not_raise():
        with session_scope() as session:
            pass
