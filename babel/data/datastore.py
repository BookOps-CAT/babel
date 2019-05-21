"""
Defines and initiates local DB that stores Babel data
"""

from contextlib import contextmanager

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, load_only, subqueryload
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import shelve

from data.datastore_values import *
from data.datastore_worker import insert_or_ignore

DB_DIALECT = 'mysql'
DB_DRIVER = 'pymysql'
DB_CHARSET = 'utf8'


Base = declarative_base()


class System(Base):
    __tablename__ = 'system'
    did = Column(Integer, primary_key=True, autoincrement=False)
    code = Column(String(3), nullable=False, unique=True)

    def __repr__(self):
        return "<System(did='%s', code='%s')>" % (
            self.did, self.code)


class Library(Base):
    __tablename__ = 'library'
    did = Column(Integer, primary_key=True, autoincrement=False)
    code = Column(String(1), nullable=False, unique=True)
    name = Column(String(8), nullable=False, unique=True)

    def __repr__(self):
        return "<Library(did='%s', code='%s', " \
            "name='%s')>" % (
                self.did, self.code, self.name)


class Users(Base):
    __tablename__ = 'users'
    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)
    nyp_code = Column(String(1), nullable=False, default='-')
    bpl_code = Column(String(1), nullable=False, default='-')

    def __repr__(self):
        return "<User(did='%s', name='%s', nyp_code='%s', " \
            "bpl_code='%s')>" % (
                self.did, self.name, self.nyp_code,
                self.bpl_code)


class Lang(Base):
    __tablename__ = 'lang'

    did = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True)
    name = Column(String(50), nullable=False)

    def __repr__(self):
        return "<Lang(did='%s', code='%s', name='%s')>" % (
            self.did, self.code, self.name)


class Audn(Base):
    __tablename__ = 'audn'

    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    code = Column(String(1), nullable=False, unique=True)

    def __repr__(self):
        return "<Audn(did='%s', name='%s', code='%s')>" % (
            self.id, self.name, self.code)


class MatType(Base):
    __tablename__ = 'mattype'

    did = Column(Integer, primary_key=True, )
    name = Column(String(25), nullable=False)

    def __repr__(self):
        return "<MatType(did='%s', name='%s')>" % (
            self.did, self.name)


class Branch(Base):
    __tablename__ = 'branch'

    bid = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey('system.did'), nullable=False)
    name = Column(String(50))
    code = Column(String(2), nullable=False, unique=True)

    def __repr__(self):
        return "<Branch(did='%s', system_id='%s', name='%s', code='%s')>" \
            % (self.did, self.system_id, self.name, self.code)


def datastore_url():
    """Windows Cred Vault mod needed below"""
    user_data = shelve.open('user_data')
    if 'db_config' in user_data:
        db_details = user_data['db_config']
        db_url = URL(
            drivername=db_details['dialect'] + '+' + db_details['driver'],
            username=db_details['user'],
            password=db_details['password'],
            host=db_details['host'],
            port=db_details['port'],
            database=db_details['db_name'],
            query={'charset': db_details['charset']}
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
            session, System, did=item[0], code=item[1])

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
