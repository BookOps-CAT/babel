"""
Methods to retrieve data from Babel datastore
"""
from datetime import datetime
from decimal import Decimal
import logging

from pandas import read_sql
from sqlalchemy.exc import IntegrityError, InternalError

from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.inspection import inspect


from data.datastore import (session_scope, Audn, Branch, Fund, FundAudnJoiner,
                            FundLibraryJoiner, FundMatTypeJoiner, Lang, Fund,
                            FundBranchJoiner, Library, MatType, DistGrid,
                            DistSet, Vendor, ShelfCode, Wlos,
                            GridLocation, Resource, Cart, Order, OrderLocation)
from data.datastore_worker import (get_column_values, retrieve_record,
                                   retrieve_records, insert,
                                   insert_or_ignore, delete_record,
                                   update_record, get_cart_data_view_records,
                                   retrieve_cart_order_ids, count_records,
                                   retrieve_last_record,
                                   retrieve_cart_details_view_stmn,
                                   retrieve_unique_vendors_from_cart)
from data.wlo_generator import wlo_pool
from data.blanket_po_generator import create_blanketPO
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
        add_title_col=record.add_title_col,
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


def get_orders_by_id(order_ids=[]):
    orders = []
    with session_scope() as session:
        for did in order_ids:
            instance = retrieve_record(session, Order, did=did)
            if instance:
                orders.append(instance)
        session.expunge_all()
    return orders


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
            ord_rec = insert(
                session, Order,
                cart_id=cart_rec.did)

            insert(
                session, Resource,
                order_id=ord_rec.did,
                title=d.title,
                add_title=d.add_title,
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

            progbar['value'] += 1
            progbar.update()


def save_new_dist_and_grid(
        system_id, profile_id, grids,
        branch_idx, shelf_idx,
        dist=None, grid=None):
    """
    args:
        system_id: int, did from System table
        profile_id: int, did from User table
        grids: dict, grids element of CartView tracker
        dist: str, name of the new DistSet record
        grid: str, name of the new DistGrid record
    """
    try:
        mlogger.debug(
            'Creating new dist/grid from CartView. '
            f'system: {system_id}, profile: {profile_id}, '
            f'dist: {dist}, grid: {grid}')

        if profile_id is not None:
            with session_scope() as session:
                dist_rec = insert_or_ignore(
                    session,
                    DistSet,
                    system_id=system_id,
                    user_id=profile_id,
                    name=dist)
                mlogger.debug(f'dist_rec: {dist_rec}')

                # check if given grid already exists
                grid_rec = retrieve_record(
                    session, DistGrid, name=grid, distset_id=dist_rec.did)
                mlogger.debug(f'grid_rec: {grid_rec}')

                # determine new gridLocations
                locations = []
                locs = grids['locs']
                for l in locs:
                    if grid_rec:
                        locations.append(
                            GridLocation(
                                distgrid_id=grid_rec.did,
                                branch_id=get_id_from_index(
                                    l['branchCbx'].get(), branch_idx),
                                shelfcode_id=get_id_from_index(
                                    l['shelfCbx'].get(), shelf_idx),
                                qty=int(l['qtyEnt'].get())))
                    else:
                        locations.append(
                            GridLocation(
                                branch_id=get_id_from_index(
                                    l['branchCbx'].get(), branch_idx),
                                shelfcode_id=get_id_from_index(
                                    l['shelfCbx'].get(), shelf_idx),
                                qty=int(l['qtyEnt'].get())))
                mlogger.debug(f'New locations: {locations}')

                if grid_rec:
                    mlogger.debug('Updating existing grid_rec.')
                    update_record(
                        session,
                        DistGrid,
                        grid_rec.did,
                        name=grid,
                        distset_id=dist_rec.did,
                        gridlocations=locations)
                else:
                    mlogger.debug('Inserting new grid_rec.')
                    insert(
                        session,
                        DistGrid,
                        name=grid,
                        distset_id=dist_rec.did,
                        gridlocations=locations)

    except ValueError as e:
        mlogger.error(
            'User attempted to save new grid with incorrect values.'
            f'Error: {e}')
        raise BabelError(
            'Your new grid includes invalid values.\n'
            'Please make sure branch, shelf, and qty are valid.')


def save_grid_data(**kwargs):
    """
    used in GridView
    """
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
                    gridlocations=locs)
            else:
                insert(
                    session,
                    DistGrid,
                    name=kwargs['name'],
                    distset_id=kwargs['distset_id'],
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


def get_ids_for_order_boxes_values(values_dict):
    kwargs = {}
    with session_scope() as session:
        if values_dict['langCbx'].get() not in ('', 'keep current'):
            rec = retrieve_record(
                session, Lang,
                name=values_dict['langCbx'].get())
            kwargs['lang_id'] = rec.did

        if values_dict['vendorCbx'].get() not in ('', 'keep current'):
            rec = retrieve_record(
                session, Vendor,
                name=values_dict['vendorCbx'].get())
            kwargs['vendor_id'] = rec.did

        if values_dict['mattypeCbx'].get() not in ('', 'keep current'):
            rec = retrieve_record(
                session, MatType,
                name=values_dict['mattypeCbx'].get())
            kwargs['matType_id'] = rec.did

        if values_dict['audnCbx'].get() not in ('', 'keep current'):
            rec = retrieve_record(
                session, Audn,
                name=values_dict['audnCbx'].get())
            kwargs['audn_id'] = rec.did

        if 'poEnt' in values_dict:
            if values_dict['poEnt'].get().strip() != '':
                kwargs['poPerLine'] = values_dict['poEnt'].get().strip()

        if 'noteEnt' in values_dict:
            if values_dict['noteEnt'].get().strip() != '':
                kwargs['note'] = values_dict['noteEnt'].get().strip()

        if 'commentEnt' in values_dict:
            if 'commentEnt' in values_dict:
                if values_dict['commentEnt'].get().strip() != '':
                    kwargs['comment'] = values_dict['commentEnt'].get().strip()

        return kwargs


def save_displayed_order_data(tracker_values):
    with session_scope() as session:
        for v in tracker_values:
            order = v['order']
            locs = v['grid']['locs']

            okwargs = {}
            locations = []
            for l in locs:
                mlogger.debug('Saving orderLoc data: order_id:{}, loc_id:{}, frm_id:{}'.format(
                    order['order_id'], l['loc_id'], l['unitFrm'].winfo_id()))
                lkwargs = {}
                if l['loc_id'] is not None:
                    lkwargs['did'] = l['loc_id']
                if l['branchCbx'].get() != '':
                    rec = retrieve_record(
                        session, Branch,
                        code=l['branchCbx'].get())
                    lkwargs['branch_id'] = rec.did
                if l['shelfCbx'].get() != '':
                    rec = retrieve_record(
                        session, ShelfCode,
                        code=l['shelfCbx'].get())
                    lkwargs['shelfcode_id'] = rec.did
                if l['qtyEnt'].get() != '':
                    lkwargs['qty'] = int(l['qtyEnt'].get())
                if l['fundCbx'].get() != '':
                    rec = retrieve_record(
                        session, Fund,
                        code=l['fundCbx'].get())
                    lkwargs['fund_id'] = rec.did
                    # validate here
                if lkwargs:
                    locations.append(OrderLocation(**lkwargs))
                    mlogger.debug(
                        'Saving orderLoc data, params: {}'.format(
                            lkwargs))

            okwargs = get_ids_for_order_boxes_values(order)
            okwargs['locations'] = locations
            mlogger.debug('Saving order data (id:{}), params: {}'.format(
                order['order_id'], okwargs))

            update_record(
                session,
                Order,
                order['order_id'],
                **okwargs)


def apply_fund_to_cart(system_id, cart_id, fund_codes):

    ord_recs = get_records(
        Order, cart_id=cart_id)

    with session_scope() as session:
        for code in fund_codes:
            fund_rec = get_record(
                Fund,
                code=code,
                system_id=system_id)
            fund_audn_ids = [a.audn_id for a in fund_rec.audns]
            mlogger.debug('Fund {} permitted audns: {}'.format(
                code, fund_audn_ids))
            fund_mat_ids = [m.matType_id for m in fund_rec.matTypes]
            mlogger.debug('Fund {} permitted mats: {}'.format(
                code, fund_mat_ids))
            fund_branch_ids = [b.branch_id for b in fund_rec.branches]
            mlogger.debug('Fund {} permitted branches: {}'.format(
                code, fund_branch_ids))

            for orec in ord_recs:
                audn_match = False
                mat_match = False

                if orec.audn_id in fund_audn_ids:
                    audn_match = True
                    mlogger.debug('OrdRec-Fund audn {} match'.format(
                        orec.audn_id))

                if orec.matType_id in fund_mat_ids:
                    mat_match = True
                    mlogger.debug('OrdRec-Fund mat {} match'.format(
                        orec.matType_id))

                for oloc in orec.locations:
                    if oloc.branch_id in fund_branch_ids:
                        mlogger.debug('OrdRec-Fund branch {} match'.format(
                            oloc.branch_id))
                        print(audn_match, mat_match)
                        if audn_match and mat_match:
                            # update
                            mlogger.debug('Full match. Updating OrderLocation.')
                            update_record(
                                session,
                                OrderLocation,
                                oloc.did,
                                fund_id=fund_rec.did)


def apply_globals_to_cart(cart_id, widgets):
    with session_scope() as session:
        # order data
        okwargs = get_ids_for_order_boxes_values(widgets)

        # resource data
        rkwargs = {}

        discount = None
        if 'discEnt' in widgets:
            if widgets['discEnt'].get() != '':
                discount = Decimal(widgets['discEnt'].get())

        if 'priceEnt' in widgets:
            if widgets['priceEnt'].get() != '':
                list_price = Decimal(widgets['priceEnt'].get())
                rkwargs['price_list'] = list_price
                if discount:
                    rkwargs['price_disc'] = list_price - ((
                        list_price * discount) / Decimal(100))
                else:
                    rkwargs['price_disc'] = list_price
        mlogger.debug('Global update to prices: {}, discount: {}'.format(
            rkwargs, discount))

        ord_recs = retrieve_records(
            session, Order, cart_id=cart_id)

        for rec in ord_recs:
            update_record(
                session, Order, rec.did, **okwargs)

            if rkwargs:
                update_record(
                    session, Resource,
                    rec.resource.did,
                    **rkwargs)

            elif discount:
                rkwargs['price_disc'] = rec.resource.price_list - ((
                    rec.resource.price_list * discount) / Decimal(100))
                update_record(
                    session, Resource,
                    rec.resource.did,
                    **rkwargs)
                rkwargs = {}


def get_cart_details_as_dataframe(cart_id):
    with session_scope() as session:
        stmn = retrieve_cart_details_view_stmn(cart_id)
        df = read_sql(stmn, session.bind)
        return df


def get_last_wlo():
    with session_scope() as session:
        last_wlo_record = retrieve_last_record(session, Wlos)
        session.expunge()
        return last_wlo_record.did


def assign_wlo_to_cart(cart_id):
    with session_scope() as session:
        # determne how many wlo are needed and reserve them
        last_wlo_rec = retrieve_last_record(session, Wlos)
        order_count = count_records(session, Order, cart_id=cart_id)
        wlo_numbers = wlo_pool(last_wlo_rec.did, order_count)

        orders = retrieve_records(session, Order, cart_id=cart_id)
        for o in orders:
            wlo = wlo_numbers.__next__()
            if o.wlo is None:
                update_record(
                    session, Order, o.did, wlo=wlo)
                insert(session, Wlos, did=wlo)

def assign_blanketPO_to_cart(cart_id):
    with session_scope() as session:
        res = retrieve_unique_vendors_from_cart(
            session, cart_id)
        vendor_codes = [name[0] for name in res]
        blanketPO = create_blanketPO(vendor_codes)
        unique = True
        n = 0
        while unique:
            try:
                print(blanketPO)
                update_record(
                    session,
                    Cart,
                    cart_id,
                    blanketPO=blanketPO)
                session.flush()
                unique = False
            except IntegrityError:
                session.rollback()
                n += 1
                blanketPO = create_blanketPO(vendor_codes, n)







