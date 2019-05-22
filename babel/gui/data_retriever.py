"""
Methods to retrieve data from Babel datastore
"""

from data.datastore import session_scope
from data.datastore_worker import get_column_values


def get_list(model, column, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, column, **kwargs)
        values = [x.column for x in res]
    return values
