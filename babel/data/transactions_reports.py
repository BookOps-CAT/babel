# Datastore transctions invoked through ReportWizView interface

from datetime import date
import logging

from pandas import read_sql
# from sqlalchemy.exc import IntegrityError

from data.datastore import session_scope
from data.datastore_worker import construct_report_query_stmn
from reports.reports import (generate_fy_summary_for_display,
                             generate_detailed_breakdown,
                             generate_branch_breakdown)
from logging_settings import LogglyAdapter
# from errors import BabelError


mlogger = LogglyAdapter(logging.getLogger('babel'), None)


def query2dataframe(system_id, library_id, user_ids,
                    start_date, end_date):
    """
    Queries datastore for relevant records and outputs the results
    as Pandas dataframe

    args:
        system_id: int, datastore system.did
        library_id: int, datastore library.did
        user_ids: list, datastore user.did list

    returns:
        df: Pandas dataframe with following columns:
            cart_id, cart_date, user, system, library, order_id,
            lang_name, lang_code, audn, vendor, mattype, price
            branch_code, branch_name, qty, fund, total
    """
    mlogger.debug(
        'Report query criteria: '
        f'system_id={system_id}, library_id={library_id}, '
        f'user_ids={user_ids}, start_date={start_date}, '
        f'end_date={end_date}')

    with session_scope() as session:
        stmn = construct_report_query_stmn(
            system_id, library_id, user_ids, start_date, end_date)

        mlogger.debug(f'Report query stmn: {stmn}')

        df = read_sql(stmn, session.bind, parse_dates=['cart_date'])

        return df


def get_fy_summary(system_id, library_id, user_ids):
    """
    Queries datastore and creates Pandas dataframe to be displayed as a report
    args:
        system_id: int, datastore system.did
        library_id: int, datastore library.did
        user_ids: list, datastore user.did list
    returns:
        data: dict, data to be displayed broke down to different categories
    """
    date_today = date.today()
    if date_today.month < 6:
        start_date = date.fromisoformat(f'{date_today.year - 1}-07-01')
    else:
        start_date = date.fromisoformat(f'{date_today.year}-07-01')
    end_date = date_today

    df = query2dataframe(system_id, library_id, user_ids,
                         start_date, end_date)
    data = generate_fy_summary_for_display(df)

    return data


def get_categories_breakdown(system_id, library_id, user_ids,
                             start_date, end_date):
    """
    Queries datastore and creates categories dictionary with report
    data categories
    args:
        system_id: int, datastore system.did
        library_id: int, datastore library.did
        user_ids: list, list of datastore user.did
        start_date: str, starting date (inclusive) in format YYYY-MM-DD
        end_date: str, end date (inclusive) in format YYYY-MM-DD
    returns:
        data: dict, data to be displayed broke down to different categories
    """
    df = query2dataframe(system_id, library_id, user_ids,
                         start_date, end_date)
    data = generate_detailed_breakdown(df, start_date, end_date)

    return data


def get_branch_breakdown(system_id, library_id, user_ids,
                         start_date, end_date):
    """
    Queries datastore and breaks down data by individual branch
    args:
        system_id: int, datastore system.did
        library_id: int, datastore library.did
        user_ids: list, list of datastore user.did
        start_date: str, starting date (inclusive) in format YYYY-MM-DD
        end_date: str, end date (inclusive) in format YYYY-MM-DD
    returns:
        data: dict, data to be displayed broke down by branch
    """
    df = query2dataframe(system_id, library_id, user_ids,
                         start_date, end_date)
    data = generate_branch_breakdown(df, start_date, end_date)

    return data
