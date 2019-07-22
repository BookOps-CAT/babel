# datastore transactions of CartsView

from datetime import datetime, date
import logging
import os
import sys

from pandas import read_sql


from data.datastore import (session_scope, Audn, Branch, Cart, Fund, Order,
                            OrderLocation, Lang, Library, MatType, Resource,
                            ShelfCode, User, Vendor)
from data.datastore_worker import (count_records, get_cart_data_view_records,
                                   insert,
                                   retrieve_record, retrieve_records,
                                   retrieve_cart_details_view_stmn)
from errors import BabelError
from logging_settings import format_traceback
from gui.utils import get_id_from_index
from marc.marc21 import make_bib


mlogger = logging.getLogger('babel_logger')


def get_carts_data(
        system_id, user='All users', status=''):
    data = []

    try:
        with session_scope() as session:
            recs = get_cart_data_view_records(
                session,
                system_id, user, status)
            for r in recs:
                data.append((
                    r.cart_id,
                    r.cart_name,
                    f'{r.cart_date:%y-%m-%d %H:%M}',
                    r.cart_status,
                    r.cart_owner))
        return data

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on cart data retrieval.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def export_orders_to_marc_file(fh, saving_status, cart_rec, progbar):
    # this has to be rewritten to make it more transparent
    # and easier to maintain

    try:
        progbar['value'] = 0

        # overwrite existing files
        if os.path.isfile(fh):
            try:
                os.remove(fh)
            except WindowsError as e:
                raise BabelError(
                    f'File in use. Error: {e}')

        with session_scope() as session:
            rec_count = count_records(session, Order, cart_id=cart_rec.did)
            progbar['maximum'] = rec_count

            selector = retrieve_record(
                session, User, did=cart_rec.user_id)
            blanketPO = cart_rec.blanketPO
            # determine some global values
            if cart_rec.system_id == 1:
                oclc_code = 'BKL'
                selector_code = selector.bpl_code
                library_code = None
            elif cart_rec.system_id == 2:
                oclc_code = 'NYP'
                selector_code = selector.nyp_code
                lib_rec = retrieve_record(
                    session, Library, did=cart_rec.library_id)
                library_code = lib_rec.code

            ord_recs = retrieve_records(session, Order, cart_id=cart_rec.did)

            for order in ord_recs:
                mat_rec = retrieve_record(
                    session, MatType, did=order.matType_id)
                ven_rec = retrieve_record(session, Vendor, did=order.vendor_id)

                if cart_rec.system_id == 1:
                    order.mat_bib = mat_rec.bpl_bib_code
                    order.mat_ord = mat_rec.bpl_ord_code
                    order.vendor = ven_rec.bpl_code
                elif cart_rec.system_id == 2:
                    order.mat_bib = mat_rec.nyp_bib_code
                    order.mat_ord = mat_rec.nyp_ord_code
                    order.vendor = ven_rec.nyp_code

                # retrieve joined values
                rec = retrieve_record(session, Audn, did=order.audn_id)
                order.audn = rec.code
                rec = retrieve_record(session, Lang, did=order.lang_id)
                order.lang = rec.code

                copies = 0
                locs = []
                funds = []
                for loc in order.locations:
                    rec = retrieve_record(session, Branch, did=loc.branch_id)
                    branch = rec.code
                    try:
                        rec = retrieve_record(
                            session, ShelfCode, did=loc.shelfcode_id)
                        shelfcode = rec.code
                        shelf_with_audn = rec.includes_audn
                    except AttributeError:
                        shelfcode = ''
                        shelf_with_audn = False
                    try:
                        rec = retrieve_record(session, Fund, did=loc.fund_id)
                        fund = rec.code
                    except AttributeError:
                        fund = ''
                    copies += loc.qty

                    if shelf_with_audn:
                        loc_str = f'{branch}{order.audn}{shelfcode}/{loc.qty}'
                    else:
                        loc_str = f'{branch}{shelfcode}/{loc.qty}'
                    locs.append(loc_str)

                    fund_str = f'{fund}/{loc.qty}'
                    funds.append(fund_str)

                order.copies = str(copies)
                order.locs = ','.join(locs)
                order.funds = ','.join(funds)
                order.order_date = datetime.strftime(date.today(), '%m-%d-%Y')

                make_bib(
                    fh, oclc_code, library_code, blanketPO,
                    selector_code, order)
                progbar['value'] += 1
                progbar.update()

        saving_status.set('Data saved to MARC file successfully.')

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on saving to MARC.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def get_cart_details_as_dataframe(cart_id):
    with session_scope() as session:
        stmn = retrieve_cart_details_view_stmn(cart_id)
        df = read_sql(stmn, session.bind)
        return df


def get_cart_data_for_order_sheet(cart_id):
    try:
        data_set = []
        with session_scope() as session:
            cart_rec = retrieve_record(session, Cart, did=cart_id)
            order_recs = retrieve_records(session, Order, cart_id=cart_id)
            for rec in order_recs:
                data = []
                data.append(rec.resource.other_no)
                data.append(rec.resource.isbn)
                data.append(rec.resource.title)
                data.append(rec.resource.author)
                total_cost = 0
                total_qty = 0
                for loc in rec.locations:
                    total_cost += loc.qty * rec.resource.price_disc
                    total_qty += loc.qty
                data.append(f'{rec.resource.price_disc:.2f}')
                data.append(total_qty)
                data.append(total_cost)
                data.append(rec.oid)
                data.append(cart_rec.blanketPO)
                data_set.append(data)
            session.expunge_all()

        return data_set

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error cart data retrieval.'
            f'Traceback: {tb}')
        raise BabelError(exc)


def create_cart_copy(
        cart_id, system, user, profile_idx,
        cart_name, status):
    """
    Creates a copy of a cart
    args:
        cart_id: int, datastore cart did
        system: str, NYPL or BPL
        user: str, profile/user name
        profile_idx: dict, dictionary of user_id (key) and names
        cart_name: str, new cart name
        status: tkinter StringVar
    """
    valid = True
    if not cart_id:
        valid = False
        status.set('Invalid cart id')
    elif not system:
        valid = False
        status.set('Failed. Missing system parameter.')
    elif not user:
        valid = False
        status.set('Failed. Missing profile prameter.')
    elif not cart_name:
        valid = False
        status.set('Failed. Missing new cart name.')

    try:
        with session_scope() as session:
            if cart_id and system and user and cart_name:
                # verify name/user not used:
                if system == 'BPL':
                    system_id = 1
                elif system == 'NYPL':
                    system_id = 2

                rec = retrieve_record(
                    session, Cart,
                    system_id=system_id,
                    user_id=get_id_from_index(
                        user, profile_idx),
                    name=cart_name)
                if rec:
                    valid = False
                    status.set(
                        'Failed. A cart with the same name'
                        'already exists.\nPlease change the name.')
            if valid:
                # create copy of the original cart
                old_cart = retrieve_record(
                    session,
                    Cart,
                    did=cart_id)

                old_orders = retrieve_records(
                    session,
                    Order,
                    cart_id=cart_id)

                new_orders = []
                for order in old_orders:

                    resource = Resource(
                        title=order.resource.title,
                        add_title=order.resource.add_title,
                        author=order.resource.author,
                        series=order.resource.series,
                        publisher=order.resource.publisher,
                        pub_place=order.resource.pub_place,
                        summary=order.resource.summary,
                        isbn=order.resource.isbn,
                        upc=order.resource.upc,
                        other_no=order.resource.other_no,
                        price_list=order.resource.price_list,
                        price_disc=order.resource.price_disc,
                        desc_url=order.resource.desc_url,
                        misc=order.resource.misc)

                    locations = []
                    for loc in order.locations:
                        locations.append(
                            OrderLocation(
                                branch_id=loc.branch_id,
                                shelfcode_id=loc.shelfcode_id,
                                qty=loc.qty,
                                fund_id=loc.fund_id))

                    new_orders.append(
                        Order(
                            lang_id=order.lang_id,
                            audn_id=order.audn_id,
                            vendor_id=order.vendor_id,
                            matType_id=order.matType_id,
                            poPerLine=order.poPerLine,
                            note=order.note,
                            comment=order.comment,
                            resource=resource,
                            locations=locations))

                new_cart = insert(
                    session,
                    Cart,
                    name=cart_name,
                    user_id=get_id_from_index(
                        user, profile_idx),
                    system_id=system_id,
                    orders=new_orders)

                status.set('Cart copied successfully.')

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error on cart copy.'
            f'Traceback: {tb}')
        raise BabelError(exc)
