"""
Methods to retrieve data from Babel datastore
"""

from data.datastore import session_scope
from data.datastore_worker import (get_column_values, retrieve_record,
                                   insert_or_ignore, delete_record,
                                   update_record)


def get_names(model, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, 'name', **kwargs)
        for x in res:
            values = [x.name for x in res]
    return values


def get_record(model, **kwargs):
    with session_scope() as session:
        instance = retrieve_record(session, model, **kwargs)
        session.expunge(instance)
        return instance


def save_record(model, exists, **kwargs):
    with session_scope() as session:
        if exists:
            update_record(session, model, **kwargs)
        else:
            insert_or_ignore(session, model, **kwargs)


def delete_records(records):
    with session_scope() as session:
        for record in records:
            model = type(record)
            delete_record(session, model, did=record.did)
