# datastore transations and methods

from sqlalchemy.orm import load_only
from sqlalchemy.sql import text


def insert_or_ignore(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    return instance


def insert(session, model, **kwargs):
    instance = model(**kwargs)
    session.add(instance)
    session.flush()
    return instance


def get_column_values(session, model, column, **kwargs):
    instances = session.query(model).filter_by(**kwargs).options(
        load_only(column)).order_by(column)
    return instances


def retrieve_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    return instance


def retrieve_first_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).order_by(model.did).first()
    return instance


def retrieve_first_n(session, model, n, **kwargs):
    instances = session.query(model).filter_by(**kwargs).limit(n).all()
    return instances


def retrieve_last_record_filtered(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).order_by(
        model.did.desc()).first()
    return instance


def retrieve_last_record(session, model):
    instance = session.query(model).order_by(model.did.desc()).first()
    return instance


def retrieve_records(session, model, **kwargs):
    instances = session.query(model).filter_by(**kwargs).order_by(
        model.did).all()
    return instances


def count_records(session, model, **kwargs):
    row_count = session.query(model).filter_by(**kwargs).count()
    return row_count


def update_record(session, model, did, **kwargs):
    instance = session.query(model).filter_by(did=did).one()
    for key, value in kwargs.items():
        setattr(instance, key, value)


def delete_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    session.delete(instance)


def retrieve_cart_order_ids(session, cart_id):
    stmn = text("""
        SELECT `order`.did
        FROM `order`
        WHERE cart_id=:cart_id
        ORDER BY `order`.did
        """)
    stmn = stmn.bindparams(cart_id=cart_id)
    instances = session.execute(stmn)
    return instances


def get_cart_data_view_records(
        session, system_id, user='All users', status=''):
    if user == 'All users' and status:
        stmn = text("""
            SELECT cart_id, cart_name, cart_date,
                   system_id, cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id AND cart_status=:status
        """)
        stmn = stmn.bindparams(system_id=system_id, status=status)

    elif user == 'All users' and not status:
        stmn = text("""
            SELECT cart_id, cart_name, cart_date, system_id,
                   cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id
        """)
        stmn = stmn.bindparams(system_id=system_id)
    elif user != 'All users' and not status:
        stmn = text("""
            SELECT cart_id, cart_name, cart_date, system_id,
                   cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id AND cart_owner=:user
        """)
        stmn = stmn.bindparams(system_id=system_id, user=user)
    else:
        stmn = text("""
            SELECT cart_id, cart_name, cart_date, system_id,
                   cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id AND cart_owner=:user AND cart_status=:status
        """)
        stmn = stmn.bindparams(system_id=system_id, user=user, status=status)
    instances = session.execute(stmn)
    return instances


def retrieve_cart_details_view_stmn(cart_id):
    stmn = text("""
        SELECT * FROM cart_details
        WHERE cart_id=:cart_id
        """)
    stmn = stmn.bindparams(cart_id=cart_id)
    return stmn


def retrieve_unique_vendors_from_cart(session, cart_id):
    stmn = text("""
    SELECT DISTINCT name
        FROM vendor
        JOIN `order` ON `order`.vendor_id = vendor.did
        WHERE `order`.cart_id=:cart_id
        ;
    """)
    stmn = stmn.bindparams(cart_id=cart_id)
    instances = session.execute(stmn)
    return instances
