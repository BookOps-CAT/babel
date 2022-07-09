# datastore transations and methods

from sqlalchemy.orm import load_only
from sqlalchemy.sql import text


def count_records(session, model, **kwargs):
    row_count = session.query(model).filter_by(**kwargs).count()
    return row_count


def delete_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    session.delete(instance)


def get_column_values(session, model, column, **kwargs):
    instances = (
        session.query(model)
        .filter_by(**kwargs)
        .options(load_only(column))
        .order_by(column)
    )
    return instances


def insert(session, model, **kwargs):
    instance = model(**kwargs)
    session.add(instance)
    session.flush()
    return instance


def insert_or_ignore(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    return instance


def retrieve_first_n(session, model, n, **kwargs):
    instances = session.query(model).filter_by(**kwargs).limit(n).all()
    return instances


def retrieve_first_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).order_by(model.did).first()
    return instance


def retrieve_last_record(session, model):
    instance = session.query(model).order_by(model.did.desc()).first()
    return instance


def retrieve_last_record_filtered(session, model, **kwargs):
    instance = (
        session.query(model).filter_by(**kwargs).order_by(model.did.desc()).first()
    )
    return instance


def retrieve_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    return instance


def retrieve_records(session, model, **kwargs):
    instances = session.query(model).filter_by(**kwargs).order_by(model.did).all()
    return instances


def retrieve_cart_order_ids(session, cart_id):
    stmn = text(
        """
        SELECT `order`.did
        FROM `order`
        WHERE cart_id=:cart_id
        ORDER BY `order`.did
        """
    )
    stmn = stmn.bindparams(cart_id=cart_id)
    instances = session.execute(stmn)
    return instances


def get_cart_data_view_records(session, system_id, user="All users", status=""):
    if user == "All users" and status:
        stmn = text(
            """
            SELECT cart_id, cart_name, cart_date,
                   system_id, cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id AND cart_status=:status
            ORDER BY cart_date DESC
        """
        )
        stmn = stmn.bindparams(system_id=system_id, status=status)

    elif user == "All users" and not status:
        stmn = text(
            """
            SELECT cart_id, cart_name, cart_date, system_id,
                   cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id
            ORDER BY cart_date DESC
        """
        )
        stmn = stmn.bindparams(system_id=system_id)
    elif user != "All users" and not status:
        stmn = text(
            """
            SELECT cart_id, cart_name, cart_date, system_id,
                   cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id AND cart_owner=:user
            ORDER BY cart_date DESC
        """
        )
        stmn = stmn.bindparams(system_id=system_id, user=user)
    else:
        stmn = text(
            """
            SELECT cart_id, cart_name, cart_date, system_id,
                   cart_status, cart_owner, linked
            FROM carts_meta
            WHERE system_id=:system_id AND cart_owner=:user AND cart_status=:status
            ORDER BY cart_date DESC
        """
        )
        stmn = stmn.bindparams(system_id=system_id, user=user, status=status)
    instances = session.execute(stmn)
    return instances


def retrieve_cart_details_view_stmn(cart_id):
    stmn = text(
        """
        SELECT * FROM cart_details
        WHERE cart_id=:cart_id
        """
    )
    stmn = stmn.bindparams(cart_id=cart_id)
    return stmn


def retrieve_unique_vendors_from_cart(session, cart_id):
    stmn = text(
        """
    SELECT DISTINCT name
        FROM vendor
        JOIN `order` ON `order`.vendor_id = vendor.did
        WHERE `order`.cart_id=:cart_id
        ;
    """
    )
    stmn = stmn.bindparams(cart_id=cart_id)
    instances = session.execute(stmn)
    return instances


def update_record(session, model, did, **kwargs):
    instance = session.query(model).filter_by(did=did).one()
    for key, value in kwargs.items():
        setattr(instance, key, value)


def construct_report_query_stmn(
    system_id: int, library_id: int, user_ids: list[int], start_date: str, end_date: str
):
    """
    Creates SQL query statemanet to select datastore records matching
    report criteria

    args:
        system_id:                      int, datastore system.did
        library_id:                     int, datastore library.did
        user_ids:                       list, list of datastore user.did
        start_date:                     str, starting date (inclusive) in format YYYY-MM-DD
        end_date:                       str, ending date (inclusive) in format YYYY-MM-DD

    returns:
        stmn: instance of sqlalchemy.sql.expression.TextClause
    """
    sql_str = """
        SELECT cart.did as cart_id,
               cart.created as cart_date,
               status.name as cart_status,
               user.name as user,
               system.name as system,
               library.name as library,
               `order`.did as order_id,
               lang.name as lang_name,
               lang.code as lang_code,
               audn.name as audn,
               vendor.name as vendor,
               mattype.name as mattype,
               resource.price_disc as price,
               branch.code as branch_code,
               branch.name as branch_name,
               orderlocation.qty as qty,
               fund.code as fund
        FROM cart
        JOIN status ON cart.status_id = status.did
        JOIN user ON cart.user_id = user.did
        JOIN system ON cart.system_id = system.did
        JOIN library ON cart.library_id = library.did
        JOIN `order` ON cart.did = `order`.cart_id
        JOIN lang ON `order`.lang_id = lang.did
        JOIN audn ON `order`.audn_id = audn.did
        JOIN vendor ON `order`.vendor_id = vendor.did
        JOIN mattype ON `order`.matType_id = mattype.did
        JOIN resource ON `order`.did = resource.order_id
        JOIN orderlocation ON `order`.did = orderlocation.order_id
        JOIN branch ON orderlocation.branch_id = branch.did
        JOIN fund ON orderlocation.fund_id = fund.did
        WHERE cart.created BETWEEN CAST(:start_date AS DATE) AND CAST(:end_date AS DATE)
    """
    params = dict(start_date=f"'{start_date}'", end_date=f"'{end_date}'")

    if system_id is not None:
        params["system_id"] = system_id
        sql_str += " AND cart.system_id=:system_id"

    if user_ids:
        s = []
        sql_str += " AND ("
        for user in list(enumerate(user_ids)):
            arg = f"user_{user[0]}"
            params[arg] = user[1]
            s.append(f"cart.user_id=:{arg}")
        sql_str += " OR ".join(s)
        sql_str += " )"

    if library_id is not None:
        params["library_id"] = library_id
        sql_str += " AND cart.library_id=:library_id"

    stmn = text(sql_str)
    stmn = stmn.bindparams(**params)

    return stmn
