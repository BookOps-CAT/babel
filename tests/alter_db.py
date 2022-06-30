"""
Run this script after migration to the new server and before shipping updated
Babel 4.0.0
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

from babel.data.datastore import DB_DIALECT, DB_DRIVER, DB_CHARSET, Base, Branch
from babel.data.datastore_values import BRANCH
from babel.data.datastore_worker import retrieve_record, insert


def alter_datastore(db_name=None, user=None, password=None, host=None, port=None):
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

    # add extra columns to modified tables
    engine.excute(
        "ALTER TABLE resource ADD dup_bibs VARCHAR(200) CHARACTER SET UTF8 COLLATE utf8_bin AFTER dup_catalog;"
    )
    print("Added dup_bibs column to resource table.")

    engine.execute("ALTER TABLE branch ADD is_research BOOLEAN AFTER code;")
    print("Added is_research column to branch table.")

    engine.execute(
        "ALTER TABLE cart MODIFY `name` VARCHAR(100) CHARACTER SET UTF8 COLLATE utf8_bin;"
    )
    print("Modified cart name column to allow longer names.")

    # update branch table
    DbSession = sessionmaker(bind=engine)
    session = DbSession()

    nyp_branches = dict()
    for d in BRANCH:
        if d[0] == 2:
            nyp_branches[d[1]] = {"name": d[2], "is_research": d[3]}

    for code, values in nyp_branches.items():
        rec = retrieve_record(session, Branch, code=code, system_id=2)
        if rec:
            rec.is_research = values["is_research"]
            print(f"Updated {rec}.")
        else:
            new_rec = insert(
                session,
                Branch,
                system_id=2,
                code=code,
                name=values["name"],
                is_research=values["is_research"],
            )
            print(f"Inserted {new_rec}.")

    session.commit()
    session.close()


if __name__ == "__main__":
    import os
    import json

    creds_fh = os.path.join(os.getenv("USERPROFILE"), ".babel/new-babel-prod-db.json")
    with open(creds_fh, "r") as f:
        creds = json.load(f)

    alter_datastore(
        db_name=creds["db"],
        user=creds["user"],
        password=creds["password"],
        host=creds["host"],
        port=creds["port"],
    )
