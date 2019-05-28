"""
Methods to retrieve data from Babel datastore
"""
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import UnmappedInstanceError


from data.datastore import (session_scope, Audn, Branch, Fund, FundAudnJoiner,
                            FundLibraryJoiner, FundMatTypeJoiner,
                            FundBranchJoiner, Library, MatType)
from data.datastore_worker import (get_column_values, retrieve_record,
                                   retrieve_records, insert,
                                   insert_or_ignore, delete_record,
                                   update_record)
from errors import BabelError


mlogger = logging.getLogger('babel_logger')


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
        try:
            session.expunge(instance)
            return instance
        except UnmappedInstanceError:
            pass
        finally:
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


def save_new_fund(**kwargs):
    # if something goes wrong this method should rollback all
    # inserts; figure out and test!!!!

    for k, v in kwargs.items():
        if not v:
            if k == 'libraries':
                kwargs[k] = []
            elif k == 'audns':
                kwargs[k] = []
            elif k == 'branches':
                kwargs[k] = []
            elif k == 'matTypes':
                kwargs[k] = []
            else:
                kwargs[k] = None

    mlogger.info('Saving new fund: {}'.format(
        kwargs))

    with session_scope() as session:
        # check if exists first
        rec = retrieve_record(
            session, Fund,
            code=kwargs['code'],
            system_id=kwargs['system_id'])
        if rec:
            msg = 'Fund record with code: {} already exists.'.format(
                kwargs['code'])
            mlogger.info(msg)
            raise BabelError('Database Error', msg)
        else:
            branches = []
            for code in kwargs['branches']:
                rec = retrieve_record(
                    session, Branch, code=code, system_id=kwargs['system_id'])
                branches.append(
                    FundBranchJoiner(branch_id=rec.did))

            libraries = []
            for name in kwargs['libraries']:
                rec = retrieve_record(
                    session, Library, name=name)
                libraries.append(FundLibraryJoiner, library_id=rec.did)

            audns = []
            for name in kwargs['audns']:
                rec = retrieve_record(
                    session, Audn, name=name)
                audns.append(
                    FundAudnJoiner(audn_id=rec.did))

            matTypes = []
            for name in kwargs['matTypes']:
                rec = retrieve_record(
                    session, MatType, name=name)
                matTypes.append(
                    FundMatTypeJoiner(matType_id=rec.did))

            fund_rec = insert(
                session, Fund,
                code=kwargs['code'],
                describ=kwargs['describ'],
                system_id=kwargs['system_id'],
                audns=audns,
                branches=branches,
                matTypes=matTypes,
                libraries=libraries)

            mlogger.info(
                'Fund {} saved successfully with did={}.'.format(
                    fund_rec.code, fund_rec.did))


def delete_records(records):
    with session_scope() as session:
        for record in records:
            model = type(record)
            delete_record(session, model, did=record.did)
