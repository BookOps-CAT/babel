"""
Methods to retrieve data from Babel datastore
"""

from data.datastore import session_scope
from data.datastore_worker import get_column_values


def get_names(model, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, 'name', **kwargs)
        for x in res:
            values = [x.name for x in res]
    return values
