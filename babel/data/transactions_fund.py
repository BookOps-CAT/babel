# FundView datastore transations
import logging
import sys

from data.datastore import (Audn, Branch, Fund, FundAudnJoiner,
                            FundBranchJoiner, FundLibraryJoiner,
                            FundMatTypeJoiner, Library, MatType,
                            session_scope)
from data.datastore_worker import retrieve_record, insert, update_record
from errors import BabelError
from gui.data_retriever import (get_record, )
from logging_settings import format_traceback


mlogger = logging.getLogger('babel')


def create_fund_joiner_objs(session, **kwargs):
    """
    Preps record objects for FundBranchJoiner, FundLibraryJoiner,
    FundAudnJoiner, and FundMatTypeJoiner
    args:
        branches: list of str
        libraries: list of str
        audns: list of str
        matTypes: list of str
    returns:
        tuple of branches, libraries, audns, matTypes record objects
    """
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
        libraries.append(FundLibraryJoiner(library_id=rec.did))

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

    return (branches, libraries, audns, matTypes)


def get_fund_data(fund_rec):
    """
    Retrieves fund record and related data for display
    args:
        fund_rec: Fund obj
    returns:
        fund_data: dict, key(value): did(int), code(str), discrib(str),
                               system_id(int), libraries(list)
                               audns(list), branches(list), mattypes(list)
    """

    if fund_rec:
        if fund_rec.describ is None:
            fund_desc = ''
        else:
            fund_desc = fund_rec.describ

        branches = []
        for rec in fund_rec.branches:
            b = get_record(Branch, did=rec.branch_id)
            branches.append(b.code)
        audns = []
        for rec in fund_rec.audns:
            a = get_record(Audn, did=rec.audn_id)
            audns.append(a.name)
        matTypes = []
        for rec in fund_rec.matTypes:
            m = get_record(MatType, did=rec.matType_id)
            matTypes.append(m.name)
        libraries = []
        for rec in fund_rec.libraries:
            lib = get_record(Library, did=rec.library_id)
            libraries.append(lib.name)

        return dict(
            did=fund_rec.did,
            code=fund_rec.code,
            system_id=fund_rec.system_id,
            describ=fund_desc,
            branches=branches,
            audns=audns,
            matTypes=matTypes,
            libraries=libraries)
    else:
        return


def insert_fund(**kwargs):
    """
    Adds a new fund with all related data
    args:
        system_id: int, datastore did of NYPL or BPL
        fund_code: str, Sierra fund code
        describ: str, fund brief description
        libraries: list, 'branches', 'research' (NYPL only)
        audns: list, list of 'a', 'j', 'y' values applicable for the fund
        matTypes: list, material types applicable for the fund
    """
    try:
        for k, v in kwargs.items():
            if not v:
                if k == 'libraries':
                    kwargs[k] = ['']
                elif k == 'audns':
                    kwargs[k] = []
                elif k == 'branches':
                    kwargs[k] = []
                elif k == 'matTypes':
                    kwargs[k] = []
                else:
                    kwargs[k] = None

        mlogger.info('New fund record parameters: {}'.format(
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
                mlogger.error(msg)
                raise BabelError('Database Error', msg)
            else:
                branches, libraries, audns, matTypes = create_fund_joiner_objs(
                    session, **kwargs)

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
                    f'Added new record {fund_rec}')
            session.expunge_all()

        return fund_rec

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error in add Fund.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def update_fund(**kwargs):
    """
    Adds a new fund with all related data
    args:
        system_id: int, datastore did of NYPL or BPL
        fund_code: str, Sierra fund code
        describ: str, fund brief description
        libraries: list, 'branches', 'research' (NYPL only)
        audns: list, list of 'a', 'j', 'y' values applicable for the fund
        matTypes: list, material types applicable for the fund
    """
    try:
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

        mlogger.info('Existing fund new parameters: {}'.format(
            kwargs))

        with session_scope() as session:
            branches, libraries, audns, matTypes = create_fund_joiner_objs(
                session, **kwargs)
            update_record(
                session, Fund,
                kwargs['did'],
                code=kwargs['code'],
                describ=kwargs['describ'],
                audns=audns,
                branches=branches,
                matTypes=matTypes,
                libraries=libraries)

            fund_rec = retrieve_record(
                session, Fund, did=kwargs['did'])

            mlogger.info(
                f'Updated record {fund_rec}')
    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error in Fund update.'
            f'Traceback: {tb}')
        raise BabelError(exc)
