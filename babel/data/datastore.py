"""
Defines and initiates local DB that stores Babel data
"""

from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import (DateTime, Column, ForeignKey, Integer,
                        String, UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship, sessionmaker, load_only, subqueryload
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import shelve


from credentials import get_from_vault
from data.datastore_values import *
from data.datastore_worker import insert_or_ignore
from paths import USER_DATA

DB_DIALECT = 'mysql'
DB_DRIVER = 'pymysql'
DB_CHARSET = 'utf8'


Base = declarative_base()


class System(Base):
    __tablename__ = 'system'
    did = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(3), nullable=False, unique=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<System({attrs})>"


class Library(Base):
    __tablename__ = 'library'
    did = Column(Integer, primary_key=True, autoincrement=False)
    code = Column(String(1), nullable=False, unique=True)
    name = Column(String(8), nullable=False, unique=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<Library({attrs})>"


class User(Base):
    __tablename__ = 'user'
    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)
    nyp_code = Column(String(1), nullable=False, default='-')
    bpl_code = Column(String(1), nullable=False, default='-')

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<User({attrs})>"


class Lang(Base):
    __tablename__ = 'lang'

    did = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True, nullable=False)
    name = Column(String(50), nullable=False)

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<Lang({attrs})>"


class Audn(Base):
    __tablename__ = 'audn'

    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    code = Column(String(1), nullable=False, unique=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<Audn({attrs})>"


class MatType(Base):
    __tablename__ = 'mattype'

    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<MatType({attrs})>"


class Branch(Base):
    __tablename__ = 'branch'

    did = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey('system.did'), nullable=False)
    name = Column(String(50))
    code = Column(String(2), nullable=False, unique=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<Branch({attrs})>"


class VendorCode(Base):
    __tablename__ = 'vencode'
    vendor_id = Column(Integer, ForeignKey('vendor.did'), primary_key=True)
    system_id = Column(Integer, ForeignKey('system.did'), primary_key=True)
    code = Column(String(5))

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<VenCode({attrs})>"


class Vendor(Base):
    __tablename__ = 'vendor'

    did = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    note = Column(String(250))

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<Vendor({attrs})>"


class DistGrid(Base):
    __tablename__ = 'distgrid'

    did = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    distgridset_id = Column(Integer, ForeignKey('distgridset.did'),
                            nullable=False)

    UniqueConstraint('name', 'distgridset_id')

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<DistGrid({attrs})>"


class DistGridSet(Base):
    __tablename__ = 'distgridset'

    did = Column(Integer, primary_key=True)
    name = Column(String(80, collation='utf8_bin'),
                  nullable=False, unique=True)
    system_id = Column(Integer, ForeignKey('system.did'), nullable=False)

    distgrids = relationship(
        'DistGrid', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<DistGridSet({attrs})>"


class ShelfCode(Base):
    __tablename__ = 'shelfcode'

    did = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey('system.did'), nullable=False)
    code = Column(String(3), unique=True, nullable=False)
    name = Column(String(50))

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<ShelfCode({attrs})>"


class Wlos(Base):
    """
    stores unique wlo numbers that can be used for retrieval of bibs
    and orders from Sierra and for matching them to Babel records
    """

    __tablename__ = 'wlo'

    did = Column(String(13), primary_key=True, autoincrement=False)
    date = Column(DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        state = inspect(self)
        attrs = ', '.join([
            f'{attr.key}={attr.loaded_value!r}' for attr in state.attrs])
        return f"<Wlo({attrs})>"


def datastore_url():
    """Windows Cred Vault mod needed below"""
    user_data = shelve.open(USER_DATA)
    if 'db_config' in user_data:
        db_details = user_data['db_config']
        passw = get_from_vault(
            db_details['db_name'], db_details['user'])
        db_url = URL(
            drivername=DB_DIALECT + '+' + DB_DRIVER,
            username=db_details['user'],
            password=passw,
            host=db_details['host'],
            port=db_details['port'],
            database=db_details['db_name'],
            query={'charset': DB_CHARSET}
        )
    else:
        db_url = None
    user_data.close()
    return db_url


class DataAccessLayer:

    def __init__(self):
        self.db_url = datastore_url()
        self.engine = None
        self.Session = None

    def connect(self):
        self.engine = create_engine(self.db_url)
        # Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)


dal = DataAccessLayer()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    dal.connect()
    session = dal.Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def create_datastore(
        db_name=None, user=None, password=None, host=None, port=None):
    """
    Creates new Babel datastore
    """

    if not db_name:
        raise ValueError('Missing db_name parameter.')
    if not user:
        raise ValueError('Missing user parameter.')
    if not password and user != 'dev':
        raise ValueError('Missing password parameter.')
    if not host:
        raise ValueError('Missing host parameter.')
    if not port:
        raise ValueError('Missing port parameter.')

    # create engine
    database_url = URL(
        drivername=DB_DIALECT + '+' + DB_DRIVER,
        username=user,
        password=password,
        host=host,
        port=port,
        database=db_name,
        query={'charset': DB_CHARSET})
    print(database_url)
    engine = create_engine(database_url)

    # check if datastore exists and delete it
    # use only initially for development!
    try:
        engine.execute("DROP DATABASE %s;" % db_name)
    except:
        pass

    engine.execute("CREATE DATABASE IF NOT EXISTS %s" % db_name)

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    # populate table with pre-defined values
    print('Populating pre-defined tables...')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    for item in SYSTEM:
        insert_or_ignore(
            session, System, did=item[0], name=item[1])

    for item in LIBRARY:
        insert_or_ignore(
            session, Library, did=item[0], code=item[1], name=item[2])

    for item in AUDN:
        insert_or_ignore(session, Audn, code=item[0], name=item[1])

    for item in LANG:
        insert_or_ignore(session, Lang, code=item[0], name=item[1])

    for item in BRANCH:
        insert_or_ignore(
            session, Branch, system_id=item[0],
            code=item[1], name=item[2])

    for item in MATERIAL:
        insert_or_ignore(session, MatType, name=item[0])

    session.commit()
    session.close()
    print('DB set-up complete.')
