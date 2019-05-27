"""
Methods to retrieve data from Babel datastore
"""

from sqlalchemy.exc import IntegrityError


from data.datastore import session_scope
from data.datastore_worker import (get_column_values, retrieve_record,
                                   retrieve_records,
                                   insert_or_ignore, delete_record,
                                   update_record)
from errors import BabelError


def get_names(model, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, 'name', **kwargs)
        for x in res:
            values = [x.name for x in res]
    return values


def get_codes(model, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, 'code', **kwargs)
        for x in res:
            values = [x.code for x in res]
    return values


def get_record(model, **kwargs):
    with session_scope() as session:
        instance = retrieve_record(session, model, **kwargs)
        session.expunge(instance)
        return instance


def get_records(model, **kwargs):
    with session_scope() as session:
        instances = retrieve_records(session, model, **kwargs)
        session.expunge(instances)
        return instances


def save_record(model, did=None, **kwargs):
    try:
        with session_scope() as session:
            if did:
                update_record(session, model, did, **kwargs)
            else:
                insert_or_ignore(session, model, **kwargs)
    except IntegrityError as e:
        raise BabelError(e)


def delete_records(records):
    with session_scope() as session:
        for record in records:
            model = type(record)
            delete_record(session, model, did=record.did)
