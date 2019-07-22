from decimal import Decimal
import logging
import sys

from sqlalchemy.exc import IntegrityError


from errors import BabelError
from data.blanket_po_generator import create_blanketPO
from data.datastore import (session_scope, Audn, Branch, Cart, DistSet,
                            DistGrid, Fund, GridLocation, Lang, MatType,
                            Order, OrderLocation, Resource, ShelfCode, Vendor,
                            Wlos)
from data.datastore_worker import (count_records, insert_or_ignore, insert,
                                   retrieve_last_record, retrieve_record,
                                   retrieve_unique_vendors_from_cart,
                                   retrieve_records, update_record)
from data.wlo_generator import wlo_pool
from gui.data_retriever import (get_record, get_records)
from gui.utils import get_id_from_index
from logging_settings import format_traceback


mlogger = logging.getLogger('babel_logger')


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


def get_last_cart():
    """
    retrieves the most recent cart
    """
    with session_scope() as session:
        cart_rec = retrieve_last_record(
            session, Cart)
        session.expunge_all()
        return cart_rec


def get_orders_by_id(order_ids=[]):
    orders = []
    with session_scope() as session:
        for did in order_ids:
            instance = retrieve_record(session, Order, did=did)
            if instance:
                orders.append(instance)
        session.expunge_all()
    return orders


def get_ids_for_order_boxes_values(values_dict):
    try:

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
                        kwargs['comment'] = values_dict[
                            'commentEnt'].get().strip()

            return kwargs

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on getting ids in cart.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def save_displayed_order_data(tracker_values):
    try:
        with session_scope() as session:
            for v in tracker_values:
                order = v['order']
                locs = v['grid']['locs']

                okwargs = {}
                locations = []
                for l in locs:
                    mlogger.debug(
                        'Saving orderLoc data: order_id:{}, '
                        'loc_id:{}, frm_id:{}'.format(
                            order['order_id'], l['loc_id'],
                            l['unitFrm'].winfo_id()))
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

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on saving cart data.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def apply_fund_to_cart(system_id, cart_id, fund_codes):

    try:

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

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on applying funds to cart.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def apply_globals_to_cart(cart_id, widgets):
    try:

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

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on applying globals to cart.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def assign_wlo_to_cart(cart_id):
    try:

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

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on assigning wlo to cart.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def assign_blanketPO_to_cart(cart_id):
    try:

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

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on assigning blanketPo to cart.'
            f'Traceback: {tb}')
        raise BabelError(exc)


# def get_last_wlo():
#     with session_scope() as session:
#         last_wlo_record = retrieve_last_record(session, Wlos)
#         session.expunge()
#         return last_wlo_record.did
