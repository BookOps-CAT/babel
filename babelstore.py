# defines and initiates local DB that stores Babel data

from contextlib import contextmanager
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, load_only, subqueryload
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import func, text
import shelve
# from collections import defaultdict
# from sqlalchemy.inspection import inspect

from prepopulated_tables import *
from convert_price import cents2dollars


DB_DIALECTS = ('mysql', )
DB_DRIVERS = ('pymysql', )
DB_CHARSET = ('utf8', )


Base = declarative_base()


class Library(Base):
    __tablename__ = 'library'
    id = Column(Integer, primary_key=True, autoincrement=False)
    code = Column(String(4), nullable=False, unique=True)

    locations = relationship('Location', cascade='all, delete-orphan')
    branches = relationship('Branch', cascade='all, delete-orphan')
    matTypes = relationship('MatTypeLibraryJoiner',
                            cascade='all, delete-orphan')
    funds = relationship('Fund', cascade='all, delete-orphan')

    def __repr__(self):
        return "<Library(id='%s', code='%s')>" % (
            self.id, self.code)


class Vendor(Base):
    __tablename__ = 'vendor'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)
    nameFormal = Column(String(50), nullable=False)
    note = Column(String(250))
    bplCode = Column(String(5), nullable=False)
    nyplCode = Column(String(5), nullable=False)

    sheets = relationship('VendorSheetTemplate', cascade='all, delete-orphan')

    def __repr__(self):
        return "<Vendor(id='%s', name='%s', nameFormal='%s', note='%s'," \
               " bplCode='%s',nyplCode='%s')>" % (self.id, self.name,
                                                  self.nameFormal, self.note,
                                                  self.bplCode, self.nyplCode)


class Lang(Base):
    __tablename__ = 'lang'

    id = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True)
    name = Column(String(50), nullable=False)

    collaborators = relationship("Collaborator", cascade='all, delete-orphan')
    sheets = relationship("VendorSheetTemplate", cascade='all, delete-orphan')

    def __repr__(self):
        return "<Lang(id='%s', code='%s', name='%s')>" % (self.id,
                                                          self.code,
                                                          self.name)


class Collaborator(Base):
    __tablename__ = 'collaborator'

    id = Column(Integer, primary_key=True)
    templateName = Column(String(25), nullable=False, )
    lang_id = Column(Integer, ForeignKey('lang.id'), nullable=False)
    collab1 = Column(String(25), nullable=False)
    collab2 = Column(String(25))
    collab3 = Column(String(25))
    collab4 = Column(String(25))
    collab5 = Column(String(25))

    def __repr__(self):
        return "<Collaborator(id='%s', templateName='%s', lang_id'%s', " \
               "colab1='%s', colab2='%s', colab3='%s', colab4='%s', " \
               "colab5='%s')>" % (self.id, self.templateName, self.lang_id,
                                  self.colab1, self.colab2, self.colab3,
                                  self.colab4, self.colab5)


class Audn(Base):
    __tablename__ = 'audn'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    code = Column(String(1), nullable=False, unique=True)

    def __repr__(self):
        return "<Audn(id='%s', name='%s', code='%s')>" % (self.id, self.name,
                                                          self.code)


class MatTypeLibraryJoiner(Base):
    __tablename__ = 'mattypelibraryjoiner'

    matType_id = Column(Integer, ForeignKey('mattype.id'), primary_key=True)
    library_id = Column(Integer, ForeignKey('library.id'), primary_key=True)
    codeO = Column(String(1), nullable=False)
    codeB = Column(String(1), nullable=False)


class MatType(Base):
    __tablename__ = 'mattype'

    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)

    locations = relationship("Location", cascade='all, delete-orphan')
    sheets = relationship("VendorSheetTemplate", cascade='all, delete-orphan')
    lib_joins = relationship("MatTypeLibraryJoiner",
                             lazy='joined',
                             cascade='all, delete-orphan')

    def __repr__(self):
        return "<MatType(id='%s', name='%s')>" % (self.id,
                                                  self.name)


class Branch(Base):
    __tablename__ = 'branch'

    id = Column(Integer, primary_key=True)
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    name = Column(String(50))
    code = Column(String(2), nullable=False, unique=True)

    locations = relationship("Location", cascade='all, delete-orphan')
    funds = relationship("FundBranchJoiner", cascade='all, delete-orphan')

    def __repr__(self):
        return "<Branch(id='%s', library_id='%s', name='%s', code='%s')>" \
            % (self.id, self.library_id, self.name, self.code)


class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True)
    name = Column(String(length=10, collation='utf8_bin'),
                  nullable=False, unique=True)
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    matType_id = Column(Integer, ForeignKey('mattype.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branch.id'), nullable=False)
    shelf = Column(String(3))
    audnPresent = Column(String(1), nullable=False)

    def __repr__(self):
        return "<Location(id='%s', name='%s', library_id='%s', " \
               "matType_id='%s, branch_id='%s', shelf='%s', " \
               "audnPresent='%s')>" % (
                   self.id, self.name, self.library_id,
                   self.matType_id, self.branch_id, self.shelf,
                   self.audnPresent)


class ShelfCode(Base):
    __tablename__ = 'shelfcode'

    # eventually shelfCode should be a child of Location
    # requires too much code review but should be fixed later
    id = Column(Integer, primary_key=True)
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    code = Column(String(3), unique=True, nullable=False)

    def __repr__(self):
        return "<ShelfCode(id='%s', library_id='%s', code='%s')>" % (
            self.id, self.library_id, self.code)


class DistrTemplate(Base):
    __tablename__ = 'distrtemplate'

    id = Column(Integer, primary_key=True)
    name = Column(String(length=50, collation='utf8_bin'),
                  nullable=False, unique=True)
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    lang_id = Column(Integer, ForeignKey('lang.id'), nullable=False)

    distrCodes = relationship("DistrCode",
                              lazy='joined',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return "<DistrTemplate(id='%s', name='%s', library_id='%s', " \
               "lang_id='%s')>" % (self.id, self.name, self.library_id,
                                   self.lang_id)


class DistrCode(Base):
    __tablename__ = 'distrcode'

    id = Column(Integer, primary_key=True)
    code = Column(String(2), nullable=False)
    distrTemplate_id = Column(Integer, ForeignKey('distrtemplate.id'),
                              nullable=False)

    distrLocQtys = relationship("DistrLocQuantity",
                                lazy='joined',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return "<DistrCode(id='%s', code='%s', distrTemplate_id='%s')>" % (
            self.id, self.code, self.distrTemplate_id)


class DistrLocQuantity(Base):
    __tablename__ = 'distrlocquantity'

    id = Column(Integer, primary_key=True)
    distrCode_id = Column(Integer, ForeignKey('distrcode.id'))
    location_id = Column(Integer, ForeignKey('location.id'))
    quantity = Column(Integer, nullable=False)

    def __repr__(self):
        return "<DistrLocQuantity(id='%s', distrCode_id='%s', " \
               "location_id='%s', quantity='%s)>" % (
                   self.id, self.distrCode_id, self.location_id, self.quantity)


class FundAudnJoiner(Base):
    __tablename__ = 'fundaudnjoiner'

    fund_id = Column(Integer, ForeignKey('fund.id'), primary_key=True)
    audn_id = Column(Integer, ForeignKey('audn.id'), primary_key=True)


class FundMatTypeJoiner(Base):
    __tablename__ = 'fundmattypejoiner'

    fund_id = Column(Integer, ForeignKey('fund.id'), primary_key=True)
    matType_id = Column(Integer, ForeignKey('mattype.id'), primary_key=True)


class FundBranchJoiner(Base):
    __tablename__ = 'fundbranchjoiner'

    fund_id = Column(Integer, ForeignKey('fund.id'), primary_key=True)
    branch_id = Column(Integer, ForeignKey('branch.id'), primary_key=True)


class Fund(Base):
    __tablename__ = 'fund'

    id = Column(Integer, primary_key=True)
    code = Column(String(25), nullable=False, unique=True)
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    desc = Column(String(100))

    audns = relationship('FundAudnJoiner',
                         cascade='all, delete-orphan',
                         lazy='joined')
    matTypes = relationship('FundMatTypeJoiner',
                            cascade='all, delete-orphan',
                            lazy='joined')
    branches = relationship('FundBranchJoiner',
                            cascade='all, delete-orphan',
                            lazy='joined')

    def __repr__(self):
        return "<Funds(id='%s', code='%s', library_id='%s', desc='%s')>" % (
            self.id, self.code, self.library_id, self.desc)


class VendorSheetTemplate(Base):
    __tablename__ = 'vendorsheettemplate'

    id = Column(Integer, primary_key=True)
    name = Column(String(length=25, collation='utf8_bin'),
                  nullable=False, unique=True)
    desc = Column(String(length=250, collation='utf8_bin'))
    lastMod = Column(DateTime, nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendor.id'), nullable=False)
    lang_id = Column(Integer, ForeignKey('lang.id'), nullable=False)
    matType_id = Column(Integer, ForeignKey('mattype.id'), nullable=False)
    headRow = Column(Integer, nullable=False)
    titleCol = Column(String(2), nullable=False)
    isbnCol = Column(String(2))
    venNoCol = Column(String(2))
    authorCol = Column(String(2))
    publisherCol = Column(String(2))
    pubDateCol = Column(String(2))
    pubPlaceCol = Column(String(2))
    priceDiscCol = Column(String(2))
    priceRegCol = Column(String(2))

    def __repr__(self):
        return "<VendorSheetTemplate(id='%s', name='%s', desc='%s', " \
               "lastMod='%s', vendor_id='%s', lang_id='%s', " \
               "matType_id='%s', " \
               "headRow='%s', titleCol='%s', isbnCol='%s', venNoCol='%s', " \
               "authorCol='%s', publisherCol='%s', pubDateCol='%s', " \
               "pubPlace='%s', priceDiscCol='%s', priceRegCol='%s'" % (
                   self.id, self.name, self.desc, self.lastMod,
                   self.vendor_id, self.lang_id, self.matType_id,
                   self.headRow, self.titleCol, self.isbnCol, self.venNoCol,
                   self.authorCol, self.publisherCol, self.pubDateCol,
                   self.pubPlaceCol, self.priceDiscCol, self.priceRegCol
               )


class Selector(Base):
    __tablename__ = 'selector'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    selector_codes = relationship('SelectorCode',
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return "<Selector(id='%s', name='%s')>" % (
            self.id, self.name)


class SelectorCode(Base):
    __tablename__ = 'selectorcode'

    selector_id = Column(Integer, ForeignKey('selector.id'), primary_key=True)
    library_id = Column(Integer, ForeignKey('library.id'), primary_key=True)
    code = Column(String(1), nullable=False)

    def __repr__(self):
        return "<SelectorCode(selector_id='%s', library_id='%s', " \
               "code='%s')>" % (
                   self.selector_id, self.library_id, self.code)


class Order(Base):
    __tablename__ = 'order'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    date = Column(DateTime, nullable=False)
    library_id = Column(Integer, ForeignKey('library.id'), nullable=False)
    lang_id = Column(Integer, ForeignKey('lang.id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendor.id'), nullable=False)
    selector_id = Column(Integer, ForeignKey('selector.id'), nullable=False)
    matType_id = Column(Integer, ForeignKey('mattype.id'), nullable=False)
    wlo_range = Column(String(27))
    blanketPO = Column(String(50))

    orderSingles = relationship('OrderSingle',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return "<Order(id='%s', name='%s', date='%s', library_id='%s', " \
               "lang_id='%s', vendor_id='%s', selector_id='%s', " \
               "matType_id='%s', " \
               "wlo_range='%s', blanketPO='%s')>" % (
                   self.id, self.name, self.date, self.library_id,
                   self.lang_id, self.vendor_id, self.selector_id,
                   self.matType_id, self.wlo_range, self.blanketPO)


class OrderSingle(Base):
    __tablename__ = 'ordersingle'

    id = Column(Integer, primary_key=True)
    wlo_id = Column(String(13), nullable=False, unique=True)
    bibRec_id = Column(Integer, ForeignKey('bibrec.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('order.id'), nullable=False)
    audn_id = Column(Integer, ForeignKey('audn.id'), nullable=False)
    po_per_line = Column(String(50))
    priceDisc = Column(Integer, nullable=False)
    priceReg = Column(Integer)
    oNumber = Column(String(9))  # add exact length of Sierra order number
    bNumber = Column(String(10))  # add exact length of Sierra bib number

    orderSingleLocations = relationship('OrderSingleLoc',
                                        lazy='joined',
                                        cascade='all, delete-orphan')

    def __repr__(self):
        return "<OrderSingle(id='%s', wlo_id='%s', bibRec_id='%s', " \
               "order_id='%s', " \
               "audn_id='%s', priceDisc='%s', oNumber='%s', " \
               "bNumber='%s'" % (
                   self.id, self.wlo_id, self.bibRec_id,
                   self.order_id,
                   self.audn_id, self.priceDisc, self.oNumber,
                   self.bNumber)


class OrderSingleLoc(Base):
    __tablename__ = 'ordersingleloc'

    id = Column(Integer, primary_key=True)
    orderSingle_id = Column(Integer, ForeignKey('ordersingle.id'),
                            nullable=False)
    location_id = Column(Integer, ForeignKey('location.id'), nullable=False)
    fund_id = Column(Integer, ForeignKey('fund.id'))
    qty = Column(Integer, nullable=False)

    def __repr__(self):
        return "<OrderSingleLoc(id='%s', orderSingle_id='%s', " \
               "location_id='%s', fund_id='%s', qty='%s'" % (
                   self.id, self.orderSingle_id, self.location_id,
                   self.fund_id, self.qty)


class BibRec(Base):
    __tablename__ = 'bibrec'

    id = Column(Integer, primary_key=True)
    title = Column(String(length=250, collation='utf8_bin'), nullable=False)
    title_trans = Column(String(250))
    author = Column(String(length=250, collation='utf8_bin'))
    author_trans = Column(String(250))
    publisher = Column(String(length=250, collation='utf8_bin'))
    publisher_trans = Column(String(250))
    pubDate = Column(String(7))
    pubPlace = Column(String(length=250, collation='utf8_bin'))
    pubPlace_trans = Column(String(250))
    audn_id = Column(Integer, ForeignKey('audn.id'), nullable=False)
    isbn = Column(String(13))
    venNo = Column(String(length=50, collation='utf8_bin'))

    def __repr__(self):
        return "<BibRec(id='%s, title_trans='%s'" \
               "author_trans='%s', publisher_trans='%s', pubDate='%s', " \
               "pubPlace_trans='%s', audn_id='%s', isbn='%s'," \
               "venNo='%s'" % (
                   self.id, self.title_trans,
                   self.author_trans, self.publisher_trans,
                   self.pubDate, self.pubPlace_trans,
                   self.audn_id, self.isbn, self.venNo)


class UsedWlo(Base):
    """
    stores unique wlo numbers that can be used for retrieval of bibs
    and orders from Sierra and for matching them to Babel records
    """
    __tablename__ = 'usedwlo'

    id = Column(String(13), primary_key=True, autoincrement=False)
    date = Column(DateTime, nullable=False)

    def __repr__(self):
        return "<UsedWlo(id='%s', date='%s')>" % (
            self.id, self.date)


class Z3950params(Base):
    """
    stores parameters of different Z3950 targets
    """
    __tablename__ = 'z3950params'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    host = Column(String(250), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(250), nullable=False)
    user = Column(String(250))
    password = Column(String(250))
    syntax = Column(String(100), nullable=False)
    isbn_url = Column(String(250))

    def __repr__(self):
        return "<z3950params(id='%s', name='%s', host='%s', port='%s', " \
               "database='%s', user='%s', syntax='%s', isbn_url='%s')>" % (
                   self.id, self.name, self.host,
                   self.port, self.database, self.user, self.syntax,
                   self.isbn_url)


def database_url():
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


def db_connection():
    # retrieve database url from shelve
    # open connection with localstore as a session
    engine = create_engine(database_url())
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session


def update_record(model, id, **kwargs):
    session = db_connection()
    instance = session.query(model).filter_by(id=id).one()
    for key, value in kwargs.iteritems():
        setattr(instance, key, value)
        session.commit()
    session.close()


def update_record_in_session(session, model, id, **kwargs):
    instance = session.query(model).filter_by(id=id).one()
    for key, value in kwargs.iteritems():
        setattr(instance, key, value)


def update_selector_code(model, selector_id, library_id, **kwargs):
    session = db_connection()
    instance = session.query(model).filter_by(
        selector_id=selector_id).filter_by(
        library_id=library_id).one()
    for key, value in kwargs.iteritems():
        setattr(instance, key, value)
        session.commit()
    session.close()


def merge_object(instance):
    session = db_connection()
    session.merge(instance)
    session.commit()
    session.close()


def create_db_object(model, **kwargs):
    instance = model(**kwargs)
    return instance


def ignore_or_insert(model, **kwargs):
    session = db_connection()
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        try:
            session.add(instance)
            session.commit()
        except IntegrityError as IE:
            session.close()
            return "Database integrity error: {0}".format(IE)
    session.close()
    return True


def ignore_or_insert_in_session(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    return instance


def retrieve_record_in_session(session, model, **kwargs):
    try:
        instance = session.query(model).filter_by(**kwargs).one()
        return instance
    except NoResultFound:
        return None


def insert_record(model, **kwargs):
    session = db_connection()
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        try:
            session.add(instance)
            session.commit()
            session.close()
            return (True, None)
        except IntegrityError as IE:
            session.close()
            e = "Database integrity error: {0}".format(IE)
            return (None, e)
    else:
        session.close()
        return (False, instance)


# method for populating joiner table
def add_to_joiner(association_table, new_values):
    session = db_connection()
    # may need to add condition to skip if already present
    for item in new_values:
        session.execute(association_table.insert().values(item))
        session.commit()
    session.close()


def retrieve_from_joiner(association_table, **kwargs):
    session = db_connection()
    instances = session.query(association_table).filter_by(**kwargs).all()
    session.close()
    return instances


def retrieve_record(model, **kwargs):
    session = db_connection()
    try:
        instance = session.query(model).filter_by(**kwargs).one()
        session.close()
        return instance
    except NoResultFound:
        session.close()
        return None


def retrieve_last(model):
    session = db_connection()
    instance = session.query(model).order_by(model.id.desc()).first()
    session.close()
    return instance


def col_preview(model, *args, **kwargs):
    session = db_connection()
    instances = session.query(model).filter_by(**kwargs).options(
        load_only(*args)).order_by(*args).all()
    session.close()
    return instances


def col_preview_in_session(session, model, *args, **kwargs):
    instances = session.query(model).filter_by(**kwargs).options(
        load_only(*args)).order_by(*args).all()
    return instances


def col_preview_date_desc(model, *args, **kwargs):
    session = db_connection()
    instances = session.query(model).filter_by(**kwargs).options(
        load_only(*args)).order_by(model.date.desc()).all()
    session.close()
    return instances


def retrieve_all(model, related, **kwargs):
    # retrieves a record and related data from other
    # tables based on created relationship
    session = db_connection()
    instances = session.query(model).options(
        subqueryload(related)).filter_by(**kwargs).order_by(model.id).all()
    session.close()
    return instances


def order_search(order_name):
    session = db_connection()
    instances = session.query(
        Order,
        OrderSingle,
        BibRec,
        Audn).\
        filter(Order.id == OrderSingle.order_id).\
        filter(OrderSingle.bibRec_id == BibRec.id).\
        filter(OrderSingle.audn_id == Audn.id).\
        filter(Order.name == order_name).\
        all()

    # find applicable unique location and fund ids
    locs = set()
    funds = set()
    for instance in instances:
        for loc in instance[1].orderSingleLocations:
            locs.add(loc.location_id)
            funds.add(loc.fund_id)

    # compile criteria for Location and Fund tables query
    loc_criteria = [Location.id == l for l in locs]
    fund_criteria = [Fund.id == f for f in funds]

    # query Location and Fund tables
    loc_records = session.query(Location.id, Location.name).\
        filter(or_(*loc_criteria)).all()
    loc_records = dict(loc_records)

    fund_records = session.query(Fund.id, Fund.code).\
        filter(or_(*fund_criteria)).all()
    fund_records = dict(fund_records)

    order_records = []
    for instance in instances:
        distr = []
        for loc in instance[1].orderSingleLocations:
            distr_code = {
                'id': loc.id,
                'location': loc_records[loc.location_id],
                'qty': loc.qty,
                'fund': fund_records[loc.fund_id]}
            distr.append(distr_code)

        entry_data = {
            'bib_id': instance[2].id,
            'ordSingle_id': instance[1].id,
            'title': instance[2].title,
            'title_trans': instance[2].title_trans,
            'author': instance[2].author,
            'author_trans': instance[2].author_trans,
            'isbn': instance[2].isbn,
            'venNo': instance[2].venNo,
            'publisher': instance[2].publisher,
            'date': instance[2].pubDate,
            'place': instance[2].pubPlace,
            'price': instance[1].priceDisc,
            'oNumber': instance[1].oNumber,
            'bNumber': instance[1].bNumber,
            'wloNumber': instance[1].wlo_id,
            'audn': instance[3].code,
            'po_per_line': instance[1].po_per_line,
            'distr': distr}
        order_records.append(entry_data)
    return order_records


def id_search(id_type, id):

    session = db_connection()
    instances = session.query(OrderSingle,
                              BibRec,
                              Order,
                              Vendor,
                              Library,
                              Lang,
                              MatType,
                              Selector).\
        filter(OrderSingle.bibRec_id == BibRec.id).\
        filter(OrderSingle.order_id == Order.id).\
        filter(Order.vendor_id == Vendor.id).\
        filter(Order.library_id == Library.id).\
        filter(Order.lang_id == Lang.id).\
        filter(Order.matType_id == MatType.id).\
        filter(Order.selector_id == Selector.id).\
        filter(id_type == id).\
        all()

    # find applicable unique location and fund ids
    locs = set()
    funds = set()
    for instance in instances:
        for loc in instance[0].orderSingleLocations:
            locs.add(loc.location_id)
            funds.add(loc.fund_id)

    # compile criteria for Location and Fund tables query
    loc_criteria = [Location.id == l for l in locs]
    fund_criteria = [Fund.id == f for f in funds]

    # query Location and Fund tables
    loc_records = session.query(Location.id, Location.name).\
        filter(or_(*loc_criteria)).all()
    loc_records = dict(loc_records)

    fund_records = session.query(Fund.id, Fund.code).\
        filter(or_(*fund_criteria)).all()
    fund_records = dict(fund_records)

    hits = []
    # stich Location & Fund data to retrieved ealier records
    for instance in instances:
        qty = 0
        locations = []
        for loc in instance[0].orderSingleLocations:
            qty += loc.qty
            copy = '{}({})/{}'.format(
                loc_records[loc.location_id],
                str(loc.qty),
                fund_records[loc.fund_id])
            locations.append(copy)

        unit = {'title': instance[1].title,
                'title_trans': instance[1].title_trans,
                'author': instance[1].author,
                'author_trans': instance[1].author_trans,
                'isbn': instance[1].isbn,
                'venNo': instance[1].venNo,
                'pubPlace': instance[1].pubPlace,
                'publisher': instance[1].publisher,
                'pubDate': instance[1].pubDate,
                'library': instance[4].code,
                'oNumber': instance[0].oNumber,
                'bNumber': instance[0].bNumber,
                'wlo_id': instance[0].wlo_id,
                'blanketPO': instance[2].blanketPO,
                'date': instance[2].date,
                'locations': locations,
                'qty': qty,
                'priceDisc': cents2dollars(instance[0].priceDisc),
                'lang': instance[5].name,
                'vendor': instance[3].name,
                'matType': instance[6].name,
                'selector': instance[7].name}
        hits.append(unit)
    session.close()
    return hits


def keyword_search(title_query, title_query_type, author_query,
                   vendor_id, date1, date2, library_id, lang_id,
                   matType_id, selector_id):
    session = db_connection()
    criteria = []
    hits = []

    if title_query_type == 'title keyword':
        if title_query is not None:
            criteria.extend(
                [BibRec.title.ilike(u'%{0}%'.format(q)) for q in title_query])
    else:
        if title_query is not None:
            criteria.append(BibRec.title.ilike(u'%{}%'.format(title_query)))

    if author_query is not None:
        criteria.extend(
            [BibRec.author.ilike(u'%{0}%'.format(q)) for q in author_query])

    if vendor_id is not None:
        criteria.append(Vendor.id == vendor_id)

    if library_id is not None:
        criteria.append(Library.id == library_id)

    if lang_id is not None:
        criteria.append(Lang.id == lang_id)

    if matType_id is not None:
        criteria.append(MatType.id == matType_id)

    if selector_id is not None:
        criteria.append(Selector.id == selector_id)

    instances = session.query(
        OrderSingle,
        BibRec,
        Order,
        Vendor,
        Library,
        Lang,
        MatType,
        Selector).\
        filter(OrderSingle.bibRec_id == BibRec.id).\
        filter(OrderSingle.order_id == Order.id).\
        filter(Order.lang_id == Lang.id).\
        filter(Order.vendor_id == Vendor.id).\
        filter(Order.library_id == Library.id).\
        filter(Order.matType_id == MatType.id).\
        filter(Order.selector_id == Selector.id).\
        filter(and_(*criteria)).\
        filter(func.date(Order.date).between(date1, date2)).\
        all()

    # find applicable unique location and fund ids
    locs = set()
    funds = set()
    for instance in instances:
        for loc in instance[0].orderSingleLocations:
            locs.add(loc.location_id)
            funds.add(loc.fund_id)

    # compile criteria for Location and Fund tables query
    loc_criteria = [Location.id == l for l in locs]
    fund_criteria = [Fund.id == f for f in funds]
    if library_id is not None:
        loc_criteria.append(Location.library_id == library_id)
        fund_criteria.append(Fund.library_id == library_id)
    if matType_id is not None:
        loc_criteria.append(Location.matType_id == matType_id)

    # query Location and Fund tables
    loc_records = session.query(Location.id, Location.name).\
        filter(or_(*loc_criteria)).all()
    loc_records = dict(loc_records)

    fund_records = session.query(Fund.id, Fund.code).\
        filter(or_(*fund_criteria)).all()
    fund_records = dict(fund_records)

    # stich Location & Fund data to retrieved ealier records
    for instance in instances:
        qty = 0
        locations = []
        for loc in instance[0].orderSingleLocations:
            qty += loc.qty
            copy = '{}({})/{}'.format(
                loc_records[loc.location_id],
                str(loc.qty),
                fund_records[loc.fund_id])
            locations.append(copy)

        unit = {'title': instance[1].title,
                'title_trans': instance[1].title_trans,
                'author': instance[1].author,
                'author_trans': instance[1].author_trans,
                'isbn': instance[1].isbn,
                'venNo': instance[1].venNo,
                'pubPlace': instance[1].pubPlace,
                'publisher': instance[1].publisher,
                'pubDate': instance[1].pubDate,
                'library': instance[4].code,
                'oNumber': instance[0].oNumber,
                'bNumber': instance[0].bNumber,
                'wlo_id': instance[0].wlo_id,
                'blanketPO': instance[2].blanketPO,
                'date': instance[2].date,
                'locations': locations,
                'qty': qty,
                'priceDisc': cents2dollars(instance[0].priceDisc),
                'lang': instance[5].name,
                'vendor': instance[3].name,
                'matType': instance[6].name,
                'selector': instance[7].name}
        hits.append(unit)

    session.close()
    return hits


def count_all(model, **kwargs):
    session = db_connection()
    total_count = session.query(model).filter_by(**kwargs).count()
    session.close()
    return total_count


def order_breakdown_sql_stmn(order_id):
    stmn = text("""
        SELECT o_id, osl_id, qty, os_id, price, fcode, acode
        FROM order_fund_audn
        WHERE o_id = :id
        """)
    return stmn.bindparams(id=order_id)


def delete_record(model, **kwargs):
    session = db_connection()
    instance = session.query(model).filter_by(**kwargs).one()
    session.delete(instance)
    session.commit()
    session.close()


def delete_records(model, ids):
    session = db_connection()
    instance = session.query(model).get(ids)
    session.delete(instance)
    session.commit()
    session.close()


def initiateDB():
    # create tables
    print 'creating tables...'
    user_data = shelve.open('user_data')
    if 'db_config' in user_data:
        db = user_data['db_config']
    db_path = db['dialect'] + '+' + db['driver'] + '://' + db['user'] + ':' + db['password'] + '@' + db['host'] + ':' + db['port']
    engine = create_engine(db_path)
    engine.execute("CREATE DATABASE IF NOT EXISTS %s" % db['db_name'])  # create db
    user_data.close()
    engine = create_engine(database_url())
    Base.metadata.create_all(engine)

    # populate table with pre-defined values
    print 'populating pre-defined tables...'
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    for item in LIBRARY:
        ignore_or_insert(Library, id=item[0], code=item[1])

    for item in AUDN:
        ignore_or_insert(Audn, code=item[0], name=item[1])

    for item in LANG:
        ignore_or_insert(Lang, code=item[0], name=item[1])

    for item in BRANCH:
        res = ignore_or_insert(
            Branch, library_id=item[0],
            code=item[1], name=item[2])
    for item in MATERIAL:
        ignore_or_insert(MatType,
                         name=item[0])
        lib_joins = []
        loaded_record = retrieve_record(MatType,
                                        name=item[0])
        lib_joins.append(
            create_db_object(
                MatTypeLibraryJoiner,
                matType_id=loaded_record.id,
                library_id=item[1][0],
                codeB=item[1][1],
                codeO=item[1][2]
            ))
        lib_joins.append(
            create_db_object(
                MatTypeLibraryJoiner,
                matType_id=loaded_record.id,
                library_id=item[2][0],
                codeB=item[2][1],
                codeO=item[2][2]
            ))
        update_record(MatType,
                      id=loaded_record.id,
                      lib_joins=lib_joins)

    for item in SELECTOR:
        ignore_or_insert(Selector,
                         name=item[0])
        codes = []
        loaded_record = retrieve_record(Selector,
                                        name=item[0])
        codes.append(
            create_db_object(
                SelectorCode,
                selector_id=loaded_record.id,
                library_id=item[1][0],
                code=item[1][1]))
        codes.append(
            create_db_object(
                SelectorCode,
                selector_id=loaded_record.id,
                library_id=item[2][0],
                code=item[2][1]))
        update_record(Selector,
                      id=loaded_record.id,
                      selector_codes=codes)

    print('creating order_fund_audn view...')
    stmn = """
        DROP VIEW IF EXISTS order_fund_audn;
        CREATE VIEW order_fund_audn AS
            SELECT ordersingle.order_id AS o_id, ordersingleloc.id AS osl_id, ordersingleloc.qty AS qty, ordersingle.id AS os_id, ordersingle.priceDisc AS price, fund.code AS fcode, audn.code AS acode
            FROM ordersingle
                JOIN ordersingleloc ON ordersingleloc.ordersingle_id = ordersingle.id
                JOIN fund ON ordersingleloc.fund_id = fund.id
                JOIN audn ON ordersingle.audn_id = audn.id
        """
    session.execute(stmn)

    session.close()
    print 'DB set-up complete.'


class DataAccessLayer:
    def __init__(self):
        self.conn_string = database_url()
        self.engine = None
        self.session = None

    def connect(self):
        self.engine = create_engine(self.conn_string)
        self.Session = sessionmaker(bind=self.engine)


dal = DataAccessLayer()


@contextmanager
def session_scope():
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


if __name__ == '__main__':
    initiateDB()
