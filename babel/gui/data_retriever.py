"""
Methods to retrieve data from Babel datastore
"""

from sqlalchemy.exc import IntegrityError


from data.datastore import (session_scope, Audn, Branch, Fund, FundAudnJoiner,
                            FundLibraryJoiner, FundMatTypeJoiner, FundBranchJoiner,
                            Library, MatType)
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


def save_fund(**kwargs):
    # if something goes wrong this method should rollback all
    # inserts; figure out and test!!!!

    for k, v in kwargs.items():
        if not v:
            kwargs[k] = None

    with session_scope() as session:
        fund_rec = insert_or_ignore(
            session, Fund,
            code=kwargs['code'],
            describ=kwargs['describ'],
            system_id=kwargs['system_id'])
        session.flush()

        if kwargs['system_id'] == 2:
            for name in kwargs['library']:
                lib_rec = retrieve_record(session, Library, name=name)
                insert_or_ignore(
                    session, FundLibraryJoiner,
                    fund_id=fund_rec.did,
                    library_id=lib_rec.did)

        for name in kwargs['audn']:
            audn_rec = retrieve_record(
                session, Audn, name=name)
            insert_or_ignore(
                session, FundAudnJoiner,
                fund_id=fund_rec.did,
                audn_id=audn_rec.did)

        for code in kwargs['branch']:
            branch_rec = retrieve_record(
                session, Branch, code=code)
            insert_or_ignore(
                session, FundBranchJoiner,
                fund_id=fund_rec.did,
                branch_id=branch_rec.did)

        for name in kwargs['mattype']:
            mattype_rec = retrieve_record(
                session, MatType,
                name=name)
            insert_or_ignore(
                session, FundMatTypeJoiner,
                fund_id=fund_rec.did,
                matType_id=mattype_rec.did)


def delete_records(records):
    with session_scope() as session:
        for record in records:
            model = type(record)
            delete_record(session, model, did=record.did)
