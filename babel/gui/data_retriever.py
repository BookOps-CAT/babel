"""
Methods to retrieve data from Babel datastore
"""
from decimal import Decimal
import logging
import sys

from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.inspection import inspect


from data.datastore import session_scope
from data.datastore_worker import (get_column_values, retrieve_record,
                                   retrieve_records,
                                   insert_or_ignore, delete_record,
                                   update_record,
                                   retrieve_cart_order_ids)

from errors import BabelError
from logging_settings import format_traceback

mlogger = logging.getLogger('babel')


def convert4display(record):
    state = inspect(record)
    for attr in state.attrs:
        if attr.loaded_value is None:
            setattr(record, attr.key, '')
        if type(attr.loaded_value) == Decimal:
            setattr(record, attr.key, f'{attr.loaded_value:.2f}')
    return record


def convert4datastore(kwargs):
    for key, value in kwargs.items():
        if value == '':
            kwargs[key] = None
    return kwargs


def get_names(model, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, 'name', **kwargs)
        for x in res:
            values = sorted([x.name for x in res])
    return values


def get_codes(model, **kwargs):
    values = []
    with session_scope() as session:
        res = get_column_values(
            session, model, 'code', **kwargs)
        values = [x.code for x in res]
    return values


def get_record(model, **kwargs):
    with session_scope() as session:
        instance = retrieve_record(session, model, **kwargs)
        try:
            session.expunge_all()
            return instance
        except UnmappedInstanceError:
            pass
        finally:
            return instance


def get_records(model, **kwargs):
    with session_scope() as session:
        instances = retrieve_records(session, model, **kwargs)
        session.expunge_all()
        return instances


def get_order_ids(cart_id):
    ids = []
    with session_scope() as session:
        order_ids = retrieve_cart_order_ids(session, cart_id)
        for i in order_ids:
            ids.append(i[0])
    return ids


def create_name_index(model, **kwargs):
    """
    Creates an value/id index of the model
    args:
        model: datatstore class, babel datastore table
        kwargs: dict, filters to be applied to query
    returns:
        idx: dict, {column value: datastore id}
    """
    idx = {}
    with session_scope() as session:
        instances = retrieve_records(session, model, **kwargs)
        for i in instances:
            if i.name is None:
                idx[i.did] = ''
            else:
                idx[i.did] = i.name
    return idx


def create_code_index(model, **kwargs):
    """
    Creates an value/id index of the model
    args:
        model: datatstore class, babel datastore table
        kwargs: dict, filters to be applied to query
    returns:
        idx: dict, {column value: datastore id}
    """
    idx = {}
    with session_scope() as session:
        instances = retrieve_records(session, model, **kwargs)
        for i in instances:
            if i.code is None:
                idx[i.did] = ''
            else:
                idx[i.did] = i.code
    return idx


def save_data(model, did=None, **kwargs):
    kwargs = convert4datastore(kwargs)

    try:
        with session_scope() as session:
            if did:
                update_record(session, model, did, **kwargs)
            else:
                insert_or_ignore(session, model, **kwargs)

    except IntegrityError as e:
        mlogger.error(
            f'DB IntegrityError while saving {model.__name__} '
            f'record with parameters {kwargs}')
        raise BabelError(e)


def delete_data(record):
    try:

        with session_scope() as session:
            model = type(record)
            delete_record(session, model, did=record.did)
        mlogger.debug('Deleted {} record did={}'.format(
            model.__name__, record.did))

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error cart deletion.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def delete_data_by_did(model, did):
    try:

        with session_scope() as session:
            delete_record(session, model, did=did)
        mlogger.debug('Deleted {} record did={}'.format(
            model.__name__, did))

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error cart deletion.'
            f'Traceback: {tb}')
        raise BabelError(exc)
