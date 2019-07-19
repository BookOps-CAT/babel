"""
Methods to retrieve data from Babel datastore
"""
from decimal import Decimal
import logging
import sys

from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.inspection import inspect


from data.datastore import (session_scope, Audn, Branch,
                            Lang, Fund,
                            MatType,
                            Vendor, ShelfCode, Wlos,
                            Resource, Cart, Order, OrderLocation)
from data.datastore_worker import (get_column_values, retrieve_record,
                                   retrieve_records, insert,
                                   insert_or_ignore, delete_record,
                                   update_record,
                                   retrieve_cart_order_ids, count_records,
                                   retrieve_last_record,
                                   retrieve_unique_vendors_from_cart)
from data.wlo_generator import wlo_pool
from data.blanket_po_generator import create_blanketPO
from errors import BabelError
from logging_settings import format_traceback

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
        for x in res:
            values = sorted([x.code for x in res])
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
                mlogger.debug(
                    'Saving orderLoc data: order_id:{}, loc_id:{}, frm_id:{}'.format(
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
                            mlogger.debug(
                                'Full match. Updating OrderLocation.')
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
