# supports searches in Babel search widget
from datetime import date
from functools import lru_cache
import logging
import sys

from sqlalchemy.sql import text


from data.datastore import (session_scope, Order, Cart, Resource, System,
                            Library, User, Lang, Audn, MatType, Vendor,
                            OrderLocation, Fund, Branch, ShelfCode, Wlos)
from data.datastore_worker import retrieve_record
from logging_settings import format_traceback


mlogger = logging.getLogger('babel')


@lru_cache(maxsize=2)
def get_shelfcode(session, shelfcode_id, audn_code):
    shelfcode = ''
    if shelfcode_id is not None:
        stmn = text("""
            SELECT code, includes_audn FROM shelfcode
            WHERE did=:shelfcode_id
            """)
        stmn = stmn.bindparams(shelfcode_id=shelfcode_id)
        instances = session.execute(stmn)
        shelfcode = ''
        for i in instances:
            if i.includes_audn:
                shelfcode = f'{audn_code}{i.code}'
            else:
                shelfcode = f'{i.code}'
            break
    return shelfcode


@lru_cache(maxsize=10)
def get_fund_code(session, fund_id):
    code = None
    if fund_id is not None:
        stmn = text("""
            SELECT code FROM fund
            WHERE did=:fund_id
            """)
        stmn = stmn.bindparams(fund_id=fund_id)
        instances = session.execute(stmn)
        for i in instances:
            code = i.code
            break
    return code


@lru_cache(maxsize=20)
def get_branch_code(session, branch_id):
    code = None
    if branch_id is not None:
        stmn = text("""
            SELECT code FROM branch
            WHERE did=:branch_id
            """)
        stmn = stmn.bindparams(branch_id=branch_id)
        instances = session.execute(stmn)
        for i in instances:
            code = i.code
            break
    return code


@lru_cache(maxsize=2)
def get_vendor_code(session, vendor_id, system):
    code = None
    if vendor_id is not None:
        if system == 'BPL':
            stmn = text("""
                SELECT bpl_code FROM vendor
                WHERE did=:vendor_id
                """)
        elif system == 'NYP':
            stmn = text("""
                SELECT nyp_code FROM vendor
                WHERE did=:vendor_id
                """)
        stmn = stmn.bindparams(vendor_id=vendor_id)
        instances = session.execute(stmn)
        for i in instances:
            if system == 'BPL':
                code = i.bpl_code
            elif system == 'NYP':
                code = i.nyp_code
            break
        return code


@lru_cache(maxsize=2)
def get_lang_name(session, lang_id):
    name = None
    if lang_id is not None:
        stmn = text("""
            SELECT name FROM lang
            WHERE did=:lang_id
            """)
        stmn = stmn.bindparams(lang_id=lang_id)
        instances = session.execute(stmn)
        for i in instances:
            name = i.name
            break
    return name


@lru_cache(maxsize=2)
def get_audn_name_and_code(session, audn_id):
    name = None
    code = None
    if audn_id is not None:
        stmn = text("""
            SELECT name, code FROM audn
            WHERE did=:audn_id
            """)
        stmn = stmn.bindparams(audn_id=audn_id)
        instances = session.execute(stmn)
        for i in instances:
            code = i.code
            name = i.name
            break
    return name, code


@lru_cache(maxsize=2)
def get_mattype_name(session, mattype_id):
    name = None
    if mattype_id is not None:
        stmn = text("""
            SELECT name FROM mattype
            WHERE did=:mattype_id
            """)
        stmn = stmn.bindparams(mattype_id=mattype_id)
        instances = session.execute(stmn)
        for i in instances:
            name = i.name
            break
    return name


@lru_cache(maxsize=4)
def get_status_name(session, status_id):
    stmn = text("""
        SELECT name FROM status
        WHERE did=:status_id
        """)
    stmn = stmn.bindparams(status_id=status_id)
    instances = session.execute(stmn)
    for i in instances:
        name = i.name
        break
    return name


@lru_cache(maxsize=2)
def get_library_name(session, library_id):
    stmn = text("""
        SELECT name FROM library
        WHERE did=:library_id
        """)
    stmn = stmn.bindparams(library_id=library_id)
    instances = session.execute(stmn)
    for i in instances:
        name = i.name
        break
    return name


@lru_cache(maxsize=2)
def get_system_name(session, system_id):
    name = None
    stmn = text("""
        SELECT name FROM system
        WHERE did=:system_id
        """)
    stmn = stmn.bindparams(system_id=system_id)
    instances = session.execute(stmn)
    for i in instances:
        name = i.name
        break
    return name


@lru_cache(maxsize=4)
def get_owner(session, user_id):
    owner = None
    stmn = text("""
        SELECT name FROM user
        WHERE did=:user_id
        """)
    stmn = stmn.bindparams(user_id=user_id)
    instances = session.execute(stmn)
    for i in instances:
        owner = i.name
        break
    return owner


def get_data_by_identifier(keyword, keyword_type):
    if keyword_type == 'bib #':
        param = Order.bid
    elif keyword_type == 'order #':
        param = Order.oid
    elif keyword_type == 'wlo #':
        param = Order.wlo
    elif keyword_type == 'ISBN':
        param = Resource.isbn
    elif keyword_type == 'UPC':
        param = Resource.upc
    elif keyword_type == 'other #':
        param = Resource.other_no
    elif keyword_type == 'blanketPO':
        param = Cart.blanketPO
    else:
        raise AttributeError('Invalid keyword_type passed')
    mlogger.debug(f'Basic search params: {keyword}, type {param}')

    try:
        with session_scope() as session:
            recs = (
                session.query(
                    Cart,
                    Order,
                    Resource)
                .join(Order, Cart.did == Order.cart_id)
                .join(Resource, Order.did == Resource.order_id)
                .filter(param == keyword)
                .all())

            results = []
            for cart_rec, ord_rec, res_rec in recs:
                # cart
                cart = cart_rec.name
                owner = get_owner(session, cart_rec.user_id)
                system = get_system_name(session, cart_rec.system_id)
                library = get_library_name(session, cart_rec.library_id)
                status = get_status_name(session, cart_rec.status_id)
                created = cart_rec.created
                blanketPO = cart_rec.blanketPO

                # order
                oid = ord_rec.oid
                bid = ord_rec.bid
                wlo = ord_rec.wlo
                po = ord_rec.poPerLine

                lang = get_lang_name(session, ord_rec.lang_id)
                audn_name, audn_code = get_audn_name_and_code(
                    session, ord_rec.audn_id)
                vendor = get_vendor_code(session, ord_rec.vendor_id, system)
                mattype = get_mattype_name(session, ord_rec.matType_id)

                locs = []
                for loc in ord_rec.locations:
                    branch = get_branch_code(session, loc.branch_id)
                    shelfcode = get_shelfcode(
                        session, loc.shelfcode_id, audn_code)
                    qty = loc.qty
                    fund = get_fund_code(session, loc.fund_id)
                    locs.append(
                        f'{branch}{shelfcode}({qty})/{fund}')

                # resouce
                title = res_rec.title
                author = res_rec.author
                isbn = res_rec.isbn
                upc = res_rec.upc
                other_no = res_rec.other_no

                unit = dict(
                    title=title,
                    author=author,
                    isbn=isbn,
                    upc=upc,
                    other_no=other_no,
                    bid=bid,
                    oid=oid,
                    wlo=wlo,
                    owner=owner,
                    cart=cart,
                    created=created,
                    system=system,
                    library=library,
                    status=status,
                    vendor=vendor,
                    lang=lang,
                    audn_name=audn_name,
                    mattype=mattype,
                    po=po,
                    locs=', '.join(locs))
                results.append(unit)
            session.expunge_all()

        return results

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error(
            'Unhandled error during Basic search.'
            f'Traceback: {tb}')
        raise BabelError('Unable to retrieve records.')


def complex_search(conditions):
    """
    args:
        condictions: dict, key=element name, value=tuple(con, value)
    """

    # will tackle in next iteration
    pass
