# datastore transations and methods

from sqlalchemy.orm import load_only


def insert_or_ignore(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    return instance


def get_column_values(session, model, column, **kwargs):
    instances = session.query(model).filter_by(**kwargs).options(
        load_only(column)).order_by(column)
    return instances


def retrieve_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    return instance


def update_record(session, model, did, **kwargs):
    instance = session.query(model).filter_by(id=id).one()
    for key, value in kwargs.iteritems():
        setattr(instance, key, value)


def delete_record(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).one()
    session.delete(instance)


