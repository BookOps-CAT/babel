"""
Methods to retrieve data from Babel datastore
"""
from datetime import datetime
import logging

from sqlalchemy.exc import IntegrityError, InternalError
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.inspection import inspect


from data.datastore import (session_scope, Audn, Branch, Fund, FundAudnJoiner,
                            FundLibraryJoiner, FundMatTypeJoiner,
                            FundBranchJoiner, Library, MatType, DistGrid,
                            GridLocation, Resource, Cart, Order)
from data.datastore_worker import (get_column_values, retrieve_record,
                                   retrieve_records, insert,
                                   insert_or_ignore, delete_record,
                                   update_record, get_cart_data_view_records)
from errors import BabelError
from gui.utils import get_id_from_index
from ingest.xlsx import ResourceDataReader


mlogger = logging.getLogger('babel_logger')


def convert4display(record):
    state = inspect(record)
    for attr in state.attrs:
        if attr.loaded_value is None:
            setattr(record, attr.key, '')
        # if type(attr.loaded_value) == int
    return record


def convert4datastore(kwargs):
    for key, value in kwargs.items():
        if value == '':
            kwargs[key] = None
    return kwargs


def create_resource_reader(template_record, sheet_fh):
    record = template_record

    # convert any empty strings back to None
    state = inspect(record)
    for attr in state.attrs:
        if attr.loaded_value == '':
            setattr(record, attr.key, None)

    mlogger.debug('Applying following sheet template: {}'.format(record))

    reader = ResourceDataReader(
        sheet_fh,
        header_row=record.header_row,
        title_col=record.title_col,
        author_col=record.author_col,
        series_col=record.series_col,
        publisher_col=record.publisher_col,
        pub_date_col=record.pub_date_col,
        pub_place_col=record.pub_place_col,
        summary_col=record.summary_col,
        isbn_col=record.isbn_col,
        upc_col=record.upc_col,
        other_no_col=record.other_no_col,
        price_list_col=record.price_list_col,
        price_disc_col=record.price_disc_col,
        desc_url_col=record.desc_url_col,
        misc_col=record.misc_col)

    return reader


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
        raise BabelError(e)


def create_cart(
        cart_name, system_id, profile_id,
        resource_data, progbar):

    with session_scope() as session:

        # create Cart record
        name_exists = True
        n = 0
        while name_exists and n < 10:
            name_exists = retrieve_record(
                session, Cart, name=cart_name)
            if name_exists:
                n += 1
                if '(' in cart_name:
                    end = cart_name.index('(')
                    cart_name = cart_name[:end]
                cart_name = f'{cart_name}({n})'

        cart_rec = insert(
            session, Cart,
            name=cart_name,
            created=datetime.now(),
            updated=datetime.now(),
            system_id=system_id,
            user_id=profile_id)

        progbar['value'] += 1
        progbar.update()

        # create Resource records
        for d in resource_data:
            res_rec = insert(
                session, Resource,
                title=d.title,
                author=d.author,
                series=d.series,
                publisher=d.publisher,
                pub_date=d.pub_date,
                summary=d.summary,
                isbn=d.isbn,
                upc=d.upc,
                other_no=d.other_no,
                price_list=d.price_list,
                price_disc=d.price_disc,
                desc_url=d.desc_url,
                misc=d.misc)

            insert(
                session, Order,
                cart_id=cart_rec.did,
                resource_id=res_rec.did)

            progbar['value'] += 1
            progbar.update()


def save_grid_data(**kwargs):
    # first update existing gridlocations
    library_id = get_id_from_index(kwargs['library'], kwargs['lib_idx'])
    lang_id = get_id_from_index(kwargs['lang'], kwargs['lang_idx'])
    vendor_id = get_id_from_index(kwargs['vendor'], kwargs['vendor_idx'])
    audn_id = get_id_from_index(kwargs['audn'], kwargs['audn_idx'])
    matType_id = get_id_from_index(kwargs['matType'], kwargs['mattype_idx'])

    locs = []
    for loc in kwargs['gridlocs']:
        branch_id = get_id_from_index(loc['branch'], kwargs['branch_idx'])
        shelf_id = get_id_from_index(loc['shelf'], kwargs['shelf_idx'])
        if loc['gridloc_id']:
            locs.append(
                GridLocation(
                    did=loc['gridloc_id'],
                    distgrid_id=loc['distgrid_id'],
                    branch_id=branch_id,
                    shelfcode_id=shelf_id,
                    qty=loc['qty']))
        else:
            if loc['distgrid_id']:
                locs.append(
                    GridLocation(
                        distgrid_id=loc['distgrid_id'],
                        branch_id=branch_id,
                        shelfcode_id=shelf_id,
                        qty=loc['qty']
                    ))
            else:
                locs.append(
                    GridLocation(
                        branch_id=branch_id,
                        shelfcode_id=shelf_id,
                        qty=loc['qty']
                    ))

    with session_scope() as session:
        try:
            if kwargs['grid_did']:
                update_record(
                    session,
                    DistGrid,
                    kwargs['grid_did'],
                    name=kwargs['name'],
                    distset_id=kwargs['distset_id'],
                    library_id=library_id,
                    lang_id=lang_id,
                    vendor_id=vendor_id,
                    audn_id=audn_id,
                    matType_id=matType_id,
                    gridlocations=locs)
            else:
                insert(
                    session,
                    DistGrid,
                    name=kwargs['name'],
                    distset_id=kwargs['distset_id'],
                    library_id=library_id,
                    lang_id=lang_id,
                    vendor_id=vendor_id,
                    audn_id=audn_id,
                    matType_id=matType_id,
                    gridlocations=locs)
        except IntegrityError as e:
            raise BabelError(e)
        except InternalError as e:
            raise BabelError(e)


def get_fund_data(fund_rec):
    """
    Retrieves fund record and related data
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


def update_fund(**kwargs):
    pass


def delete_data(record):
    with session_scope() as session:
        model = type(record)
        delete_record(session, model, did=record.did)
    mlogger.debug('Deleted {} record did={}'.format(
        model.__name__, record.did))


def delete_data_by_did(model, did):
    with session_scope() as session:
        delete_record(session, model, did=did)
    mlogger.debug('Deleted {} record did={}'.format(
        model.__name__, did))


def get_carts_data(
        system_id, user='All users', status=''):
    data = []
    with session_scope() as session:
        recs = get_cart_data_view_records(
            session,
            system_id, user, status)
        for r in recs:
            data.append((r.cart_id, (
                r.cart_name,
                f'{r.cart_date:%y-%m-%d %H:%M}',
                r.cart_status,
                r.cart_owner)))
    return data
