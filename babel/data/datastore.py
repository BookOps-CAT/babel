"""
Defines and initiates local DB that stores Babel data
"""

from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

# from sqlalchemy.sql import text
import shelve


try:
    from credentials import get_from_vault
    from data.datastore_values import *
    from data.datastore_worker import insert_or_ignore
    from paths import USER_DATA
except ImportError:
    from babel.credentials import get_from_vault
    from babel.data.datastore_values import *
    from babel.data.datastore_worker import insert_or_ignore
    from babel.paths import USER_DATA

DB_DIALECT = "mysql"
DB_DRIVER = "pymysql"
DB_CHARSET = "utf8"


Base = declarative_base()


class System(Base):
    __tablename__ = "system"
    did = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(3), nullable=False, unique=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<System({attrs})>"


class Library(Base):
    __tablename__ = "library"
    did = Column(Integer, primary_key=True, autoincrement=False)
    code = Column(String(1), unique=True, nullable=False)
    name = Column(String(8), unique=True, nullable=False)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Library({attrs})>"


class User(Base):
    __tablename__ = "user"
    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)
    nyp_code = Column(String(1), nullable=False, default="-")
    bpl_code = Column(String(1), nullable=False, default="-")

    distsets = relationship("DistSet", cascade="all, delete-orphan")
    carts = relationship("Cart", cascade="all, delete-orphan")
    sheets = relationship("Sheet", cascade="all, delete-orphan")

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<User({attrs})>"


class Lang(Base):
    __tablename__ = "lang"

    did = Column(Integer, primary_key=True)
    code = Column(String(3), unique=True, nullable=False)
    name = Column(String(50), nullable=False)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Lang({attrs})>"


class Audn(Base):
    __tablename__ = "audn"

    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False)
    code = Column(String(1), nullable=False, unique=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Audn({attrs})>"


class MatType(Base):
    __tablename__ = "mattype"

    did = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)
    bpl_bib_code = Column(String(1))
    bpl_ord_code = Column(String(1))
    nyp_bib_code = Column(String(1))
    nyp_ord_code = Column(String(1))

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<MatType({attrs})>"


class Branch(Base):
    __tablename__ = "branch"
    __table_args__ = (UniqueConstraint("code", "system_id", name="uix_branch"),)

    did = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey("system.did"), nullable=False)
    name = Column(String(50))
    code = Column(String(2), nullable=False)
    is_research = Column(Boolean, default=None)
    temp_closed = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Branch({attrs})>"


class Vendor(Base):
    __tablename__ = "vendor"

    did = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    note = Column(String(250))
    bpl_code = Column(String(5))
    nyp_code = Column(String(5))

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Vendor({attrs})>"


class GridLocation(Base):
    __tablename__ = "gridlocation"

    did = Column(Integer, primary_key=True)
    distgrid_id = Column(Integer, ForeignKey("distgrid.did"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch.did"), nullable=False)
    shelfcode_id = Column(Integer, ForeignKey("shelfcode.did"), nullable=False)
    qty = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<GridLocation({attrs})>"


class DistGrid(Base):
    __tablename__ = "distgrid"
    __table_args__ = (UniqueConstraint("name", "distset_id", name="uix_distgrid"),)

    did = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    distset_id = Column(Integer, ForeignKey("distset.did"), nullable=False)

    gridlocations = relationship(
        "GridLocation",
        lazy="joined",
        order_by="GridLocation.did",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<DistGrid({attrs})>"


class DistSet(Base):
    __tablename__ = "distset"
    __table_args__ = (
        UniqueConstraint("name", "system_id", "user_id", name="uix_distset"),
    )

    did = Column(Integer, primary_key=True)
    name = Column(String(80, collation="utf8_bin"), nullable=False)
    system_id = Column(Integer, ForeignKey("system.did"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.did"), nullable=False)

    distgrids = relationship("DistGrid", lazy="joined", cascade="all, delete-orphan")

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<DistSet({attrs})>"


class ShelfCode(Base):
    __tablename__ = "shelfcode"
    __table_args__ = (UniqueConstraint("code", "system_id", name="uix_shelfcode"),)

    did = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey("system.did"), nullable=False)
    code = Column(String(3))
    name = Column(String(50), nullable=False)
    includes_audn = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<ShelfCode({attrs})>"


class FundLibraryJoiner(Base):
    __tablename__ = "fundlibraryjoiner"

    fund_id = Column(Integer, ForeignKey("fund.did"), primary_key=True)
    library_id = Column(Integer, ForeignKey("library.did"), primary_key=True)


class FundAudnJoiner(Base):
    __tablename__ = "fundaudnjoiner"

    fund_id = Column(Integer, ForeignKey("fund.did"), primary_key=True)
    audn_id = Column(Integer, ForeignKey("audn.did"), primary_key=True)


class FundMatTypeJoiner(Base):
    __tablename__ = "fundmattypejoiner"

    fund_id = Column(Integer, ForeignKey("fund.did"), primary_key=True)
    matType_id = Column(Integer, ForeignKey("mattype.did"), primary_key=True)


class FundBranchJoiner(Base):
    __tablename__ = "fundbranchjoiner"

    fund_id = Column(Integer, ForeignKey("fund.did"), primary_key=True)
    branch_id = Column(Integer, ForeignKey("branch.did"), primary_key=True)


class Fund(Base):
    __tablename__ = "fund"
    __table_args__ = (UniqueConstraint("code", "system_id", name="uix_fund"),)

    did = Column(Integer, primary_key=True)
    code = Column(String(15))
    system_id = Column(Integer, ForeignKey("system.did"), nullable=False)
    describ = Column(String(100))

    audns = relationship("FundAudnJoiner", cascade="all, delete-orphan", lazy="joined")

    branches = relationship(
        "FundBranchJoiner", cascade="all, delete-orphan", lazy="joined"
    )

    matTypes = relationship(
        "FundMatTypeJoiner", cascade="all, delete-orphan", lazy="joined"
    )

    libraries = relationship(
        "FundLibraryJoiner", cascade="all, delete-orphan", lazy="joined"
    )

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<ShelfCode({attrs})>"


class Resource(Base):
    __tablename__ = "resource"

    did = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.did"), nullable=False)
    title = Column(String(length=250, collation="utf8_bin"), nullable=False)
    add_title = Column(String(length=250, collation="utf8_bin"))
    author = Column(String(length=150, collation="utf8_bin"))
    series = Column(String(length=250, collation="utf8_bin"))
    publisher = Column(String(length=150, collation="utf8_bin"))
    pub_date = Column(String(25))
    pub_place = Column(String(length=50, collation="utf8_bin"))
    summary = Column(String(length=500, collation="utf8_bin"))
    isbn = Column(String(13))
    upc = Column(String(20))
    other_no = Column(String(25))
    price_list = Column(Float(asdecimal=True))
    price_disc = Column(Float(asdecimal=True), default=0.0, nullable=False)
    desc_url = Column(String(length=500, collation="utf8_bin"))
    misc = Column(String(250))
    dup_babel = Column(Boolean)
    dup_catalog = Column(Boolean)
    dup_bibs = Column(String(length=200, collation="utf8_bin"))
    dup_timestamp = Column(DateTime)

    order = relationship("Order", back_populates="resource", lazy="joined")

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Resource({attrs})>"


class Cart(Base):
    __tablename__ = "cart"
    __table_args__ = (
        UniqueConstraint("name", "system_id", "user_id", name="uix_cart"),
    )

    did = Column(Integer, primary_key=True)
    name = Column(String(75), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.now())
    updated = Column(DateTime, nullable=False, default=datetime.now())
    status_id = Column(Integer, ForeignKey("status.did"), nullable=False, default=1)
    linked = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey("user.did"), nullable=False)
    system_id = Column(Integer, ForeignKey("system.did"), nullable=False)
    library_id = Column(Integer, ForeignKey("library.did"))
    blanketPO = Column(String(25), unique=True, nullable=True)

    orders = relationship("Order", cascade="all, delete-orphan")

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Cart({attrs})>"


class Order(Base):
    __tablename__ = "order"

    did = Column(Integer, primary_key=True)
    oid = Column(String(9))
    bid = Column(String(10))
    wlo = Column(String(13))
    cart_id = Column(Integer, ForeignKey("cart.did"), nullable=False)
    lang_id = Column(Integer, ForeignKey("lang.did"))
    audn_id = Column(Integer, ForeignKey("audn.did"))
    vendor_id = Column(Integer, ForeignKey("vendor.did"))
    matType_id = Column(Integer, ForeignKey("mattype.did"))
    poPerLine = Column(String(50))
    note = Column(String(50))
    comment = Column(String(150))

    resource = relationship(
        "Resource",
        uselist=False,
        cascade="all, delete-orphan",
        back_populates="order",
        lazy="joined",
    )

    locations = relationship(
        "OrderLocation",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="OrderLocation.did",
    )

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Order({attrs})>"


class OrderLocation(Base):
    __tablename__ = "orderlocation"

    did = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.did"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch.did"))
    shelfcode_id = Column(Integer, ForeignKey("shelfcode.did"))
    qty = Column(Integer)
    fund_id = Column(Integer, ForeignKey("fund.did"))

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<OrderLocation({attrs})>"


class Status(Base):
    __tablename__ = "status"

    did = Column(Integer, primary_key=True)
    name = Column(String(15))

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Status({attrs})>"


class Sheet(Base):
    __tablename__ = "sheet"
    __table_args__ = (UniqueConstraint("name", "user_id", name="uix_sheet"),)

    did = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("user.did"), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.now())
    updated = Column(DateTime, nullable=False, default=datetime.now())
    header_row = Column(Integer, nullable=False)
    title_col = Column(Integer, nullable=False)
    add_title_col = Column(Integer)
    author_col = Column(Integer)
    series_col = Column(Integer)
    publisher_col = Column(Integer)
    pub_date_col = Column(Integer)
    pub_place_col = Column(Integer)
    summary_col = Column(Integer)
    isbn_col = Column(Integer)
    upc_col = Column(Integer)
    other_no_col = Column(Integer)
    price_list_col = Column(Integer)
    price_disc_col = Column(Integer)
    desc_url_col = Column(Integer)
    comment_col = Column(Integer)
    misc_col = Column(Integer)

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Sheet({attrs})>"


class Wlos(Base):
    """
    stores unique wlo numbers that can be used for retrieval of bibs
    and orders from Sierra and for matching them to Babel records
    """

    __tablename__ = "wlo"

    did = Column(String(13), primary_key=True, autoincrement=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now())

    def __repr__(self):
        state = inspect(self)
        attrs = ", ".join([f"{attr.key}={attr.loaded_value!r}" for attr in state.attrs])
        return f"<Wlo({attrs})>"


def datastore_url():
    user_data = shelve.open(USER_DATA)
    if "db_config" in user_data:
        db_details = user_data["db_config"]
        passw = get_from_vault("babel_db", db_details["DB_USER"])
        db_url = URL(
            drivername=DB_DIALECT + "+" + DB_DRIVER,
            username=db_details["DB_USER"],
            password=passw,
            host=db_details["DB_HOST"],
            port=db_details["DB_PORT"],
            database=db_details["DB_NAME"],
            query={"charset": DB_CHARSET},
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
        self.Session = sessionmaker(bind=self.engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    dal = DataAccessLayer()
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


def create_datastore(db_name=None, user=None, password=None, host=None, port=None):
    """
    Creates new Babel datastore
    """

    if not db_name:
        raise ValueError("Missing db_name parameter.")
    if not user:
        raise ValueError("Missing user parameter.")
    if not password and user != "dev":
        raise ValueError("Missing password parameter.")
    if not host:
        raise ValueError("Missing host parameter.")
    if not port:
        raise ValueError("Missing port parameter.")

    # create engine
    database_url = URL(
        drivername=DB_DIALECT + "+" + DB_DRIVER,
        username=user,
        password=password,
        host=host,
        port=port,
        database=db_name,
        query={"charset": DB_CHARSET},
    )
    print(database_url)
    engine = create_engine(database_url)

    # check if datastore exists and delete it
    # use only initially for development!
    try:
        engine.execute("DROP DATABASE %s;" % db_name)
    except:
        print("Unable to drop database.")
        pass

    engine.execute("CREATE DATABASE IF NOT EXISTS %s" % db_name)

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    # populate table with pre-defined values
    print("Populating pre-defined tables...")
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    for item in SYSTEM:
        insert_or_ignore(session, System, did=item[0], name=item[1])

    for item in LIBRARY:
        insert_or_ignore(session, Library, did=item[0], code=item[1], name=item[2])

    for item in AUDN:
        insert_or_ignore(session, Audn, code=item[0], name=item[1])

    for item in LANG:
        insert_or_ignore(session, Lang, code=item[0], name=item[1])

    for item in BRANCH:
        insert_or_ignore(
            session,
            Branch,
            system_id=item[0],
            code=item[1],
            name=item[2],
            is_research=item[3],
        )

    for item in MATERIAL:
        insert_or_ignore(
            session,
            MatType,
            name=item[0],
            bpl_bib_code=item[1][1],
            bpl_ord_code=item[1][2],
            nyp_bib_code=item[2][1],
            nyp_ord_code=item[2][2],
        )

    for item in USERS:
        insert_or_ignore(
            session, User, name=item[0], bpl_code=item[1][1], nyp_code=item[2][1]
        )

    for item in STATUS:
        insert_or_ignore(session, Status, did=item[0], name=item[1])

    session.commit()

    print("creating carts data view...")
    stmn = """
    CREATE VIEW carts_meta AS
        SELECT cart.did AS cart_id, cart.name AS cart_name,
               cart.created AS cart_date, cart.system_id AS system_id,
               status.name AS cart_status, user.name AS cart_owner,
               cart.linked AS linked
        FROM cart
            JOIN status ON status.did = cart.status_id
            JOIN user ON user.did = cart.user_id
    """
    session.execute(stmn)

    print("creating cart_fund view...")
    stmn = """
    CREATE VIEW cart_details AS
        SELECT cart.did AS cart_id, cart.blanketPO as blanketPO,
               `order`.did AS order_id, `order`.oid as order_oid, `order`.wlo as wlo,
               resource.price_disc as price,
               orderlocation.qty as qty, fund.code as fund,
               lang.name as lang, audn.name as audn,
               vendor.name as vendor, mattype.name as mattype,
               branch.code as branch
        FROM cart
            JOIN `order` ON cart.did = `order`.cart_id
            JOIN resource ON `order`.did = resource.order_id
            JOIN vendor ON `order`.vendor_id = vendor.did
            JOIN lang ON `order`.lang_id = lang.did
            JOIN audn ON `order`.audn_id = audn.did
            JOIN orderlocation ON `order`.did = orderlocation.order_id
            JOIN mattype ON `order`.matType_Id = mattype.did
            JOIN fund ON orderlocation.fund_id = fund.did
            JOIN branch ON orderlocation.branch_id = branch.did
        """
    session.execute(stmn)

    # enter last wlo number

    print("inserting first wlo number")
    wlos = insert_or_ignore(
        session, Wlos, did="wlo0000059510", timestamp=datetime.now()
    )
    print(f"{wlos} inserted")
    session.commit()

    session.close()

    print("DB set-up complete.")
