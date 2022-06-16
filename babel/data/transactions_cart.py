from collections import OrderedDict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import logging
import sys

from sqlalchemy import and_

# from sqlalchemy.dialects import mysql

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text


from errors import BabelError
from data.blanket_po_generator import create_blanketPO
from data.datastore import (
    session_scope,
    Audn,
    Branch,
    Cart,
    DistSet,
    DistGrid,
    Fund,
    GridLocation,
    Lang,
    MatType,
    Order,
    OrderLocation,
    Resource,
    ShelfCode,
    Vendor,
    Wlos,
)
from data.datastore_worker import (
    count_records,
    delete_record,
    insert_or_ignore,
    insert,
    retrieve_last_record,
    retrieve_record,
    retrieve_records,
    update_record,
)
from data.transactions_carts import get_cart_details_as_dataframe
from data.wlo_generator import wlo_pool
from gui.utils import get_id_from_index
from logging_settings import format_traceback, LogglyAdapter
from sierra_adapters.middleware import catalog_match, NypPlatform, BplSolr


mlogger = LogglyAdapter(logging.getLogger("babel"), None)


def add_resource(cart_id, **kwargs):
    try:
        with session_scope() as session:
            orec = insert(session, Order, cart_id=cart_id)
            kwargs["order_id"] = orec.did
            insert(session, Resource, **kwargs)
    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on updating resource." f"Traceback: {tb}")
        raise BabelError(exc)


def apply_fund_to_cart(system_id, cart_id, fund_codes):

    try:
        with session_scope() as session:
            cart_rec = retrieve_record(session, Cart, did=cart_id)
            ord_recs = retrieve_records(session, Order, cart_id=cart_id)

            for code in fund_codes:
                fund_rec = retrieve_record(
                    session, Fund, code=code, system_id=system_id
                )

                fund_audn, fund_mat, fund_branch, fund_lib = valid_fund_ids(fund_rec)

                for orec in ord_recs:
                    audn_match = False
                    mat_match = False
                    library_match = False

                    if orec.audn_id in fund_audn:
                        audn_match = True

                    if orec.matType_id in fund_mat:
                        mat_match = True

                    if cart_rec.library_id in fund_lib:
                        library_match = True

                    for oloc in orec.locations:
                        if oloc.branch_id in fund_branch:
                            mlogger.debug(
                                "OrdRec-Fund branch {} match".format(oloc.branch_id)
                            )
                            if audn_match and library_match and mat_match:
                                # update
                                mlogger.debug("Complete match. Updating OrderLocation.")
                                update_record(
                                    session,
                                    OrderLocation,
                                    oloc.did,
                                    fund_id=fund_rec.did,
                                )
                            else:
                                mlogger.debug(
                                    "Incomplete match: lib={}, audn={}, "
                                    "mat={}.".format(
                                        library_match, audn_match, mat_match
                                    )
                                )

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on applying funds to cart." f"Traceback: {tb}")
        raise BabelError(exc)


def apply_globals_to_cart(cart_id, widgets):
    try:

        with session_scope() as session:
            # order data
            okwargs = get_ids_for_order_boxes_values(widgets)
            # locations
            dist_id, grid_name = widgets["globgrid"]
            grid_rec = retrieve_record(
                session, DistGrid, distset_id=dist_id, name=grid_name
            )
            mlogger.debug(f"Applying globally grid {grid_rec}")

            # resource data
            rkwargs = {}

            discount = None
            if "discEnt" in widgets:
                if widgets["discEnt"].get() != "":
                    discount = Decimal(widgets["discEnt"].get())

            if "priceEnt" in widgets:
                if widgets["priceEnt"].get() != "":
                    list_price = Decimal(widgets["priceEnt"].get())
                    rkwargs["price_list"] = list_price
                    if discount:
                        rkwargs["price_disc"] = list_price - (
                            (list_price * discount) / Decimal(100)
                        )
                    else:
                        rkwargs["price_disc"] = list_price
            mlogger.debug(
                "Global update to prices: {}, discount: {}".format(rkwargs, discount)
            )

            ord_recs = retrieve_records(session, Order, cart_id=cart_id)

            for rec in ord_recs:
                if grid_rec:
                    olocs = []
                    for l in grid_rec.gridlocations:
                        olocs.append(
                            OrderLocation(
                                order_id=rec.did,
                                branch_id=l.branch_id,
                                shelfcode_id=l.shelfcode_id,
                                qty=l.qty,
                            )
                        )
                    okwargs["locations"] = olocs
                update_record(session, Order, rec.did, **okwargs)

                if rkwargs:
                    update_record(session, Resource, rec.resource.did, **rkwargs)

                session.flush()

                if discount is not None:
                    rkwargs["price_disc"] = rec.resource.price_list - (
                        (rec.resource.price_list * discount) / Decimal(100)
                    )
                    update_record(session, Resource, rec.resource.did, **rkwargs)
                    rkwargs = {}

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on applying globals to cart." f"Traceback: {tb}")
        raise BabelError(exc)


def apply_grid_to_selected_orders(order_ids, grid_id, append=False):
    """
    Datastore transaction that appends or replaces current
    OrderLocation records
    args:
        order_ids: list, list of datastore order dids
        grid_id: int, datastore DistGrid.did
        append: boolean, True appends to existing locations,
                         False replaces existing locations
    """
    with session_scope() as session:
        # retrieve grid location data
        grid_rec = retrieve_record(session, DistGrid, did=grid_id)

        if append:
            # add to existing locations
            for oid in order_ids:
                ord_rec = retrieve_record(session, Order, did=oid)

                for gloc in grid_rec.gridlocations:
                    # find duplicates and merge
                    dup = False
                    for oloc in ord_rec.locations:
                        if (
                            oloc.branch_id == gloc.branch_id
                            and oloc.shelfcode_id == gloc.shelfcode_id
                        ):
                            # add quantity to existing oloc
                            dup = True
                            mlogger.debug(
                                "Updating existing "
                                f"OrderLocation.did={oloc.did} "
                                f"with new qty={oloc.qty + gloc.qty}"
                            )
                            update_record(
                                session,
                                OrderLocation,
                                oloc.did,
                                order_id=oid,
                                branch_id=oloc.branch_id,
                                shelfcode_id=oloc.shelfcode_id,
                                qty=oloc.qty + gloc.qty,
                                fund_id=oloc.fund_id,
                            )
                    if not dup:
                        mlogger.debug(
                            f"Inserting new OrderLocation for Order.did={oid} "
                            f"based on DistGrid.did={gloc.did}"
                        )
                        insert_or_ignore(
                            session,
                            OrderLocation,
                            order_id=oid,
                            branch_id=gloc.branch_id,
                            shelfcode_id=gloc.shelfcode_id,
                            qty=gloc.qty,
                        )
        else:
            # replace existing locations
            for oid in order_ids:
                # delete exiting locaations
                loc_recs = retrieve_records(session, OrderLocation, order_id=oid)
                for oloc in loc_recs:
                    mlogger.debug(
                        f"Deleting OrderLocation.did={oloc.did} " f"of order.did={oid}"
                    )
                    delete_record(session, OrderLocation, did=oloc.did)

                for gloc in grid_rec.gridlocations:
                    mlogger.debug(
                        f"Inserting new OrderLocation based on "
                        f"DistGrid.did={gloc.did}"
                    )
                    insert_or_ignore(
                        session,
                        OrderLocation,
                        order_id=oid,
                        branch_id=gloc.branch_id,
                        shelfcode_id=gloc.shelfcode_id,
                        qty=gloc.qty,
                    )


def assign_blanketPO_to_cart(cart_id):
    try:

        with session_scope() as session:
            cart_rec = retrieve_record(session, Cart, did=cart_id)
            if cart_rec.blanketPO is None:
                res = retrieve_unique_vendor_codes_from_cart(
                    session, cart_id, cart_rec.system_id
                )
                vendor_codes = [code[0] for code in res]
                blanketPO = create_blanketPO(vendor_codes)
                unique = True
                n = 0
                while unique:
                    try:
                        update_record(session, Cart, cart_id, blanketPO=blanketPO)
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
            "Unhandled error on assigning blanketPo to cart." f"Traceback: {tb}"
        )
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
                if o.wlo is None:
                    wlo = wlo_numbers.__next__()
                    update_record(session, Order, o.did, wlo=wlo)
                    insert(session, Wlos, did=wlo)

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on assigning wlo to cart." f"Traceback: {tb}")
        raise BabelError(exc)


def babel_resource_match(session, system_id, library_id, isbn=None, upc=None):
    """Finds ordered previously resources"""
    isbn_matches = 0
    if isbn is not None:
        isbn_matches = (
            session.query(Cart, Order, Resource)
            .join(Order, Cart.did == Order.cart_id)
            .join(Resource, Order.did == Resource.order_id)
            .filter(Cart.system_id == system_id)
            .filter(Cart.library_id == library_id)
            .filter(Resource.isbn == isbn)
            .count()
        )

    upc_matches = 0
    if upc is not None:
        upc_matches = (
            session.query(Cart, Order, Resource)
            .join(Order, Cart.did == Order.cart_id)
            .join(Resource, Order.did == Resource.order_id)
            .filter(Cart.system_id == system_id)
            .filter(Cart.library_id == library_id)
            .filter(Resource.upc == upc)
            .count()
        )

    if isbn_matches > 1:
        return True
    elif upc_matches > 1:
        return True
    else:
        return False


def convert_price2datastore(price_str):
    try:
        price = Decimal(price_str)
    except InvalidOperation:
        price = Decimal(0)

    return price


def create_grids_snapshot(grid_trackers):
    snapshot = hashlib.md5()
    for grid in grid_trackers:
        # did = grid['loc_id']
        for key, widget in grid.items():
            if key in ("branchCbx", "shelfCbx", "qtyEnt", "fundCbx"):
                snapshot.update(widget.get().encode("utf-8"))
    return snapshot.digest()


def create_order_snapshot(order_tracker):
    snapshot = hashlib.md5()
    # did = order_tracker['order_id']
    for key, widget in order_tracker.items():
        if key != "order_id":
            snapshot.update(widget.get().encode("utf-8"))
    sh = snapshot.digest()
    # mlogger.debug(
    #     f'Generated hash ({sh} for order no {did}.)')
    return sh


def delete_locations_from_selected_orders(order_ids):
    with session_scope() as session:
        for oid in order_ids:
            loc_recs = retrieve_records(session, OrderLocation, order_id=oid)
            for oloc in loc_recs:
                mlogger.debug(
                    f"Deleting OrderLocation.did={oloc.did} " f"of Order.did={oid}"
                )
                delete_record(session, OrderLocation, did=oloc.did)


def determine_needs_validation(cart_id):
    with session_scope() as session:
        cart_rec = retrieve_record(session, Cart, did=cart_id)
        # ignore status 'finlized' and 'archived'
        if cart_rec.status_id in (2, 4):
            return False
        else:
            return True


def find_matches(cart_id, creds_fh, progbar=None):
    with session_scope() as session:

        if progbar:
            count = count_records(session, Order, cart_id=cart_id)
            progbar["value"] = 0
            progbar["maximum"] = count

        cart_rec = retrieve_record(session, Cart, did=cart_id)
        ord_recs = retrieve_records(session, Order, cart_id=cart_id)

        # determine appropriate middleware to query for dups in the catalog
        if cart_rec.system_id == 1:
            # BPL Solr
            middleware = BplSolr(creds_fh)
        elif cart_rec.system_id == 2:
            # NYPL Platform
            if cart_rec.library_id == 1:
                library = "branches"
            elif cart_rec.library_id == 2:
                library = "research"
            else:
                library = None
            middleware = NypPlatform(library, creds_fh)
        else:
            middleware = None

        for rec in ord_recs:

            # check for internal duplicates
            keywords = []
            if rec.resource.isbn:
                keywords.append(rec.resource.isbn)
                babel_dup = babel_resource_match(
                    session,
                    cart_rec.system_id,
                    cart_rec.library_id,
                    isbn=rec.resource.isbn,
                )
            elif rec.resource.upc:
                keywords.append(rec.resource.upc)
                babel_dup = babel_resource_match(upc=rec.resource.upc)
            else:
                babel_dup = False

            # check for duplicates in the catalog
            mlogger.debug(
                f"Identified following keywords for middleware query: {keywords}"
            )
            if middleware is not None and keywords:
                catalog_dup, dup_bibs = catalog_match(middleware, keywords)
            else:
                catalog_dup = None
                dup_bibs = None

            mlogger.debug(
                f"Found following order matches for {keywords}: babel={babel_dup}, "
                f"catalog={catalog_dup}, dub_bibs={dup_bibs}."
            )

            update_record(
                session,
                Resource,
                rec.resource.did,
                dup_babel=babel_dup,
                dup_catalog=catalog_dup,
                dup_bibs=dup_bibs,
                dup_timestamp=datetime.now(),
            )

            if progbar:
                progbar["value"] += 1
                progbar.update()

        # close session with middleware
        if middleware is not None:
            try:
                middleware.close()
            except:
                pass


@lru_cache(maxsize=24)
def get_branch_code(session, branch_id):
    rec = retrieve_record(session, Branch, did=branch_id)
    return rec.code


@lru_cache(maxsize=24)
def get_branch_rec_id(session, branch_code):
    rec = retrieve_record(session, Branch, code=branch_code)
    return rec.did


def get_cart_resources(cart_id):
    """creates a list of resources to be displayed in ApplyGridsWidget"""

    resources = []
    with session_scope() as session:
        records = retrieve_records(session, Order, cart_id=cart_id)
        n = 0
        for rec in records:
            n += 1
            price = f"{rec.resource.price_disc:,.2f}"
            qty = 0
            loc_ids = []
            for loc in rec.locations:
                qty += loc.qty
                loc_ids.append(loc.branch_id)
            locations = []
            for loc_id in loc_ids:
                branch_code = get_branch_code(session, loc_id)
                locations.append(branch_code)
            locations = ",".join(sorted(locations))

            resources.append(
                (
                    rec.did,
                    n,
                    rec.resource.title,
                    rec.resource.author,
                    rec.resource.isbn,
                    price,
                    rec.comment,
                    qty,
                    locations,
                )
            )

    return resources


@lru_cache(maxsize=2)
def get_fund_rec_id(session, fund_code):
    rec = retrieve_record(session, Fund, code=fund_code)
    return rec.did


def get_ids_for_order_boxes_values(values_dict):
    try:

        kwargs = {}
        with session_scope() as session:
            if values_dict["langCbx"].get() not in ("", "keep current"):
                rec = retrieve_record(session, Lang, name=values_dict["langCbx"].get())
                kwargs["lang_id"] = rec.did

            if values_dict["vendorCbx"].get() not in ("", "keep current"):
                rec = retrieve_record(
                    session, Vendor, name=values_dict["vendorCbx"].get()
                )
                kwargs["vendor_id"] = rec.did

            if values_dict["mattypeCbx"].get() not in ("", "keep current"):
                rec = retrieve_record(
                    session, MatType, name=values_dict["mattypeCbx"].get()
                )
                kwargs["matType_id"] = rec.did

            if values_dict["audnCbx"].get() not in ("", "keep current"):
                rec = retrieve_record(session, Audn, name=values_dict["audnCbx"].get())
                kwargs["audn_id"] = rec.did

            if "poEnt" in values_dict:
                if values_dict["poEnt"].get().strip() != "":
                    kwargs["poPerLine"] = values_dict["poEnt"].get().strip()

            if "noteEnt" in values_dict:
                if values_dict["noteEnt"].get().strip() != "":
                    kwargs["note"] = values_dict["noteEnt"].get().strip()

            if "commentEnt" in values_dict:
                if "commentEnt" in values_dict:
                    if values_dict["commentEnt"].get().strip() != "":
                        kwargs["comment"] = values_dict["commentEnt"].get().strip()

            return kwargs

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on getting ids in cart." f"Traceback: {tb}")
        raise BabelError(exc)


def get_last_cart():
    """
    retrieves the most recent cart
    """
    with session_scope() as session:
        cart_rec = retrieve_last_record(session, Cart)
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


@lru_cache(maxsize=2)
def get_shelf_rec_id(session, shelf_code):
    rec = retrieve_record(session, ShelfCode, code=shelf_code)
    return rec.did


def has_library_assigned(cart_id):
    """
    args:
        cart_id: int, datastore Cart.did
    returns:
        boolean: True is library assigned, False if not
    """
    with session_scope() as session:
        rec = retrieve_record(session, Cart, did=cart_id)
        if rec.library_id:
            return True
        else:
            return False


def retrieve_unique_vendor_codes_from_cart(session, cart_id, system_id):
    if system_id == 1:
        stmn = text(
            """
        SELECT DISTINCT bpl_code
            FROM vendor
            JOIN `order` ON `order`.vendor_id = vendor.did
            WHERE `order`.cart_id=:cart_id
            ;
        """
        )
    elif system_id == 2:
        stmn = text(
            """
        SELECT DISTINCT nyp_code
            FROM vendor
            JOIN `order` ON `order`.vendor_id = vendor.did
            WHERE `order`.cart_id=:cart_id
            ;
        """
        )
    stmn = stmn.bindparams(cart_id=cart_id)
    instances = session.execute(stmn)
    return instances


def save_displayed_order_data(tracker_values):
    try:
        with session_scope() as session:
            for v in tracker_values:
                order = v["order"]
                locs = v["grid"]["locs"]

                okwargs = {}
                locations = []
                for l in locs:
                    mlogger.debug(
                        "Saving orderLoc data: order_id:{}, "
                        "loc_id:{}, frm_id:{}".format(
                            order["order_id"], l["loc_id"], l["unitFrm"].winfo_id()
                        )
                    )
                    lkwargs = {}
                    if l["loc_id"] is not None:
                        lkwargs["did"] = l["loc_id"]
                    if l["branchCbx"].get() != "":
                        rec_id = get_branch_rec_id(session, l["branchCbx"].get())
                        lkwargs["branch_id"] = rec_id
                    if l["shelfCbx"].get() != "":
                        rec_id = get_shelf_rec_id(session, l["shelfCbx"].get())
                        lkwargs["shelfcode_id"] = rec_id
                    if l["qtyEnt"].get() != "":
                        lkwargs["qty"] = int(l["qtyEnt"].get())
                    if l["fundCbx"].get() != "":
                        rec_id = get_fund_rec_id(session, l["fundCbx"].get())
                        lkwargs["fund_id"] = rec_id
                        # validate here
                    if lkwargs:
                        locations.append(OrderLocation(**lkwargs))
                        mlogger.debug(
                            "Saving orderLoc data, params: {}".format(lkwargs)
                        )

                okwargs = get_ids_for_order_boxes_values(order)
                okwargs["locations"] = locations
                mlogger.debug(
                    "Saving order data (id:{}), params: {}".format(
                        order["order_id"], okwargs
                    )
                )

                update_record(session, Order, order["order_id"], **okwargs)

    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on saving cart data." f"Traceback: {tb}")
        raise BabelError(exc)


def save_new_dist_and_grid(
    system_id, profile_id, grids, branch_idx, shelf_idx, dist=None, grid=None
):
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
            "Creating new dist/grid from CartView. "
            f"system: {system_id}, profile: {profile_id}, "
            f"dist: {dist}, grid: {grid}"
        )

        if profile_id is not None:
            with session_scope() as session:
                dist_rec = insert_or_ignore(
                    session, DistSet, system_id=system_id, user_id=profile_id, name=dist
                )
                mlogger.debug(f"Dist_rec: {dist_rec}")

                # check if given grid already exists
                grid_rec = retrieve_record(
                    session, DistGrid, name=grid, distset_id=dist_rec.did
                )
                mlogger.debug(f"Grid_rec: {grid_rec}")

                # determine new gridLocations
                locations = []
                locs = grids["locs"]
                for l in locs:
                    if grid_rec:
                        locations.append(
                            GridLocation(
                                distgrid_id=grid_rec.did,
                                branch_id=get_id_from_index(
                                    l["branchCbx"].get(), branch_idx
                                ),
                                shelfcode_id=get_id_from_index(
                                    l["shelfCbx"].get(), shelf_idx
                                ),
                                qty=int(l["qtyEnt"].get()),
                            )
                        )
                    else:
                        locations.append(
                            GridLocation(
                                branch_id=get_id_from_index(
                                    l["branchCbx"].get(), branch_idx
                                ),
                                shelfcode_id=get_id_from_index(
                                    l["shelfCbx"].get(), shelf_idx
                                ),
                                qty=int(l["qtyEnt"].get()),
                            )
                        )
                mlogger.debug(f"New locations: {locations}")

                if grid_rec:
                    mlogger.debug("Updating existing grid_rec.")
                    update_record(
                        session,
                        DistGrid,
                        grid_rec.did,
                        name=grid,
                        distset_id=dist_rec.did,
                        gridlocations=locations,
                    )
                else:
                    mlogger.debug("Inserting new grid_rec.")
                    insert(
                        session,
                        DistGrid,
                        name=grid,
                        distset_id=dist_rec.did,
                        gridlocations=locations,
                    )

    except ValueError as e:
        mlogger.error(
            "User attempted to save new grid with incorrect values." f"Error: {e}"
        )
        raise BabelError(
            "Your new grid includes invalid values.\n"
            "Please make sure branch, shelf, and qty are valid."
        )


def search_cart(cart_id, keywords, keyword_type, search_type):
    """Searches given cart for resources matching user criteria
    args:
        cart_id: int, Cart.did
        keywords: str, words to search
        keyword_type: str, various columns to search
        search_type: str, 'phrase' or 'keyword'
    returns:
        results: list of tuples, (oid, #, title, author, isbn)
    """

    with session_scope() as session:
        recs = []

        query = (
            session.query(Order.did, Resource.title, Resource.author, Resource.isbn)
            .join(Order, Order.did == Resource.order_id)
            .filter(Order.cart_id == cart_id)
            .order_by(Order.did)
        )

        if keyword_type == "isbn":
            recs = query.filter(Resource.isbn.ilike(f"%{keywords}%")).all()
        if keyword_type == "upc":
            recs = query.filter(Resource.upc.ilike(f"%{keywords}%")).all()
        if keyword_type == "other #":
            recs = query.filter(Resource.other_no.ilike(f"%{keywords}")).all()
        if keyword_type == "wlo #":
            recs = query.filter(Order.wlo.ilike(f"%{keywords}%")).all()
        if keyword_type == "order #":
            recs = query.filter(Order.oid.ilike(f"%{keywords}%")).all()
        if keyword_type == "bib #":
            recs = query.filter(Order.bid.ilike(f"%{keywords}%")).all()
        if keyword_type == "title":
            if search_type == "phrase":
                query = query.filter(Resource.title.ilike(f"%{keywords}%"))
                recs = query.all()
            elif search_type == "keyword":
                keywords = keywords.split(" ")
                for word in keywords:
                    query = query.filter(Resource.title.ilike(f"%{word}%"))
                recs = query.all()
        if keyword_type == "author":
            if search_type == "phrase":
                recs = query.filter(Resource.author.ilike(f"%{keywords}%")).all()
            elif search_type == "keyword":
                keywords = keywords.split(" ")
                for word in keywords:
                    query = query.filter(Resource.author.ilike(f"%{word}%"))
                recs = query.all()

        results = []
        n = 0
        for rec in recs:
            n += 1
            results.append((rec[0], n, rec[1], rec[2], rec[3]))

        return results


def tabulate_funds(cart_id):
    """
    Calculates amount alocated per fund in the cart
    args:
        cart_id: int, datastore cart did
    returns:
        tally: list of tuples(code, amount)
    """
    tally = []
    df = get_cart_details_as_dataframe(cart_id)
    for fund, value in df.groupby("fund"):
        amount = (value["price"] * value["qty"]).sum()
        amount = f"{amount:.2f}"
        tally.append(f"{fund}:${amount}")

    with session_scope() as session:
        update_record(session, Cart, did=cart_id, updated=datetime.now())

    return tally


def update_resource(resource_id, **kwargs):
    try:
        with session_scope() as session:
            update_record(session, Resource, resource_id, **kwargs)
    except Exception as exc:
        _, _, exc_traceback = sys.exc_info()
        tb = format_traceback(exc, exc_traceback)
        mlogger.error("Unhandled error on updating resource." f"Traceback: {tb}")
        raise BabelError(exc)


def validate_cart_data(cart_id):
    issues = OrderedDict()
    iss_count = 0
    with session_scope() as session:
        cart_rec = retrieve_record(session, Cart, did=cart_id)
        if cart_rec.system_id == 1 and cart_rec.library_id != 1:
            iss_count += 1
            issues[0] = "BPL cart library parameter must be set to 'branches'"
        elif cart_rec.system_id == 2:
            if not cart_rec.library_id or cart_rec.library_id == 3:
                iss_count += 1
                issues[0] = "NYPL carts must specify library"

        n = 0
        order_records = retrieve_records(session, Order, cart_id=cart_id)
        for o in order_records:
            ord_issues = []
            n += 1
            if not o.lang_id:
                iss_count += 1
                ord_issues.append("language")
            if not o.audn_id:
                iss_count += 1
                ord_issues.append("audience")
            if not o.vendor_id:
                iss_count += 1
                ord_issues.append("vendor")
            if not o.matType_id:
                iss_count += 1
                ord_issues.append("material type")
            if not o.resource.title:
                iss_count += 1
                ord_issues.append("title")
            if not o.resource.price_disc:
                iss_count += 1
                ord_issues.append("discount price")

            grid_issues = OrderedDict()
            m = 0
            if o.locations:
                for l in o.locations:
                    m += 1
                    loc_issues = []
                    if not l.branch_id:
                        iss_count += 1
                        loc_issues.append("branch")
                    if not l.shelfcode_id:
                        iss_count += 1
                        loc_issues.append("shelf code")
                    if not l.qty:
                        iss_count += 1
                        loc_issues.append("quantity")
                    if not l.fund_id:
                        iss_count += 1
                        loc_issues.append("fund")
                    else:
                        # verify fund here
                        valid_fund = validate_fund(
                            session,
                            l.fund_id,
                            cart_rec.system_id,
                            cart_rec.library_id,
                            o.audn_id,
                            o.matType_id,
                            l.branch_id,
                        )
                        if not valid_fund:
                            loc_issues.append("(incorrect) fund")

                    if loc_issues:
                        grid_issues[m] = loc_issues
            else:
                iss_count += 1
                ord_issues.append("locations")

            if ord_issues or grid_issues:
                issues[n] = (ord_issues, grid_issues)

    return iss_count, issues


@lru_cache(maxsize=24)
def validate_fund(
    session, fund_id, system_id, library_id, audn_id, mattype_id, branch_id
):
    valid = True
    params = [library_id, audn_id, mattype_id, branch_id]
    for p in params:
        if p is None:
            return True

    fund_rec = retrieve_record(session, Fund, did=fund_id)

    fund_audn, fund_mat, fund_branch, fund_lib = valid_fund_ids(fund_rec)
    if library_id not in fund_lib:
        valid = False
    if audn_id not in fund_audn:
        valid = False
    if mattype_id not in fund_mat:
        valid = False
    if branch_id not in fund_branch:
        valid = False

    return valid


def valid_fund_ids(fund_rec):
    fund_audn_ids = [a.audn_id for a in fund_rec.audns]
    mlogger.debug(f"Fund {fund_rec.code} permitted audns: {fund_audn_ids}")

    fund_mat_ids = [m.matType_id for m in fund_rec.matTypes]
    mlogger.debug(f"Fund {fund_rec.code} permitted mats: {fund_mat_ids}")

    fund_branch_ids = [b.branch_id for b in fund_rec.branches]
    mlogger.debug(f"Fund {fund_rec.code} permitted branches: {fund_branch_ids}")

    fund_library_ids = [l.library_id for l in fund_rec.libraries]
    mlogger.debug(f"Fund {fund_rec.code} permitted libraries: {fund_library_ids}")

    return (fund_audn_ids, fund_mat_ids, fund_branch_ids, fund_library_ids)
