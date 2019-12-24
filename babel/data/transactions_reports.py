# Datastore transctions invoked through ReportWizView interface

from datetime import date
import logging

from pandas import read_sql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from data.datastore import session_scope
from data.datastore_worker import construct_fy_summary_stmn
from reports.reports import generate_fy_summary_for_display
from logging_settings import format_traceback, LogglyAdapter
from errors import BabelError


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


def get_fy_summary(system_id, library_id, user_ids):
    """
    Queries datastore and creates pandas dataframe to be displayed as a report
    """
    date_today = date.today()
    if date_today.month < 6:
        start_date = date.fromisoformat(f'{date_today.year - 1}-07-01')
    else:
        start_date = date.fromisoformat(f'{date_today.year}-07-01')
    end_date = date_today

    with session_scope() as session:
        stmn = construct_fy_summary_stmn(
            system_id, library_id, user_ids, start_date, end_date)
        df = read_sql(stmn, session.bind)
        data = generate_fy_summary_for_display(df)

        return data
