# supports searches in Babel search widget
import logging


from data.datastore import (session_scope, Order, Cart, Resource, System,
                            Library, User, Lang, Audn, MatType, Vendor,
                            OrderLocation, Fund, Branch, ShelfCode)


mlogger = logging.getLogger('babel_logger')


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

    with session_scope() as session:
        recs = (session.query(
            Cart,
            Order,
            Resource,
            Vendor,
            System)
            .join(Order, Cart.did == Order.cart_id)
            .join(Resource, Order.did == Resource.order_id)
            .join(Vendor, Order.vendor_id == Vendor.did)
            .join(System, Cart.system_id == System.did)
            .filter(param == keyword)
            .all())

            # System,
            # Library,
            # Lang,
            # MatType,
            # User,
            # Fund,
            # Branch,
            # ShelfCode,
            # Audn,
            # OrderLocation)
            # .join(System, System.did == Cart.system_id)
            # .join(Library, Library.did == Cart.library_id)
            # .join(User, User.did == Cart.user_id)
            # .join(Lang, Order.lang_id == Lang.did)
            # .join(Audn, Order.audn_id == Audn.did)
            # .join(MatType, Order.matType_id == MatType.did)
            # .join(OrderLocation, OrderLocation.order_id == Order.did)
            # .join(Fund, OrderLocation.fund_id == Fund.did)
            # .join(Branch, OrderLocation.branch_id == Branch.did)
            # .join(ShelfCode, OrderLocation.shelfcode_id == ShelfCode.did)

        c = 0
        for rec in recs:
            c += 1

        print(f'retrieved {c} records')
