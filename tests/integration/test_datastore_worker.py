from sqlalchemy.engine.cursor import CursorResult

from babel.data.datastore import datastore_url, session_scope, System
from babel.data.datastore_worker import construct_report_query_stmn, get_column_values


def test_get_column_values(dev_user_data, mock_db_creds_from_vault):
    with session_scope() as session:
        query = get_column_values(session, System, "name")
        result = [r.name for r in query]
        assert result == ["BPL", "NYP"]


def test_execution_of_construct_report_query_stmn(
    dev_user_data, mock_db_creds_from_vault
):
    with session_scope() as session:
        stmn = construct_report_query_stmn(None, None, [], "2022-04-01", "2022-04-11")
        result = session.execute(
            stmn,
        )
        assert isinstance(result, CursorResult)
        assert result.first() is not None
