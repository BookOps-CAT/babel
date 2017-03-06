# defines and initiates local DB that stores Babel data

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, load_only, subqueryload
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.engine.url import URL
import shelve

from prepopulated_tables import *

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
    code = Column(String(1), unique=True, nullable=False)

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
    title = Column(String(250), nullable=False)
    title_trans = Column(String(250))
    author = Column(String(250))
    author_trans = Column(String(250))
    publisher = Column(String(250))
    publisher_trans = Column(String(250))
    pubDate = Column(String(7))
    pubPlace = Column(String(250))
    pubPlace_trans = Column(String(250))
    audn_id = Column(Integer, ForeignKey('audn.id'), nullable=False)
    isbn = Column(String(13))
    venNo = Column(String(50))

    def __repr__(self):
        return "<BibRec(id='%s, title_trans='%s', " \
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


def count_all(model, **kwargs):
    session = db_connection()
    total_count = session.query(model).filter_by(**kwargs).count()
    session.close()
    return total_count


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
        ignore_or_insert(Branch, library_id=item[0],
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

    session.close()
    print 'DB set-up complete.'


if __name__ == '__main__':
    initiateDB()
