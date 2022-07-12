# Datastore transctions invoked through ReportWizView interface

from datetime import date
import logging

from pandas import DataFrame, read_sql

try:
    from data.datastore import session_scope
    from data.datastore_worker import construct_report_query_stmn
    from reports.reports import (
        create_branch_to_lang_audn_mat_dataframe,
        create_lang_audn_mat_to_branch_dataframe,
        generate_basic_stats,
        generate_branch_breakdown,
        generate_language_breakdown,
        generate_detailed_breakdown,
        generate_fy_summary_for_display,
    )
    from logging_settings import LogglyAdapter
except ImportError:
    from babel.data.datastore import session_scope
    from babel.data.datastore_worker import construct_report_query_stmn
    from babel.reports.reports import (
        create_branch_to_lang_audn_mat_dataframe,
        create_lang_audn_mat_to_branch_dataframe,
        generate_basic_stats,
        generate_branch_breakdown,
        generate_language_breakdown,
        generate_detailed_breakdown,
        generate_fy_summary_for_display,
    )
    from babel.logging_settings import LogglyAdapter


mlogger = LogglyAdapter(logging.getLogger("babel"), None)


def get_basic_stats(start_date: str, end_date: str) -> dict:
    """
    Queries datastore and compiles basic Babel stats

    Args:
        start_date:             starting date (inclusive) in format YYYY-MM-DD
        end_date:               ending date (inclusive) in format YYYY-MM-DD

    Returns:
        data dictionary
    """
    df = query2dataframe(None, None, [], start_date, end_date)
    data = generate_basic_stats(df, start_date, end_date)

    return data


def get_branch_breakdown(
    system_id: int, library_id: int, user_ids: list[int], start_date: str, end_date: str
) -> dict:
    """
    Queries datastore and breaks down data by individual branch

    Args:
        system_id:              datastore system.did
        library_id:             datastore library.did
        user_ids:               list of datastore user.did
        start_date:             starting date (inclusive) in format YYYY-MM-DD
        end_date:               end date (inclusive) in format YYYY-MM-DD
    Returns:
        data:                   data to be displayed broke down by branch
    """
    df = query2dataframe(system_id, library_id, user_ids, start_date, end_date)
    data = generate_branch_breakdown(df, start_date, end_date)

    return data


def get_branch_lang(
    system_id: int, library_id: int, user_ids: list[int], start_date: str, end_date: str
) -> DataFrame:
    """
    Queries datastore with given criteria and returns dataframe showing branches broken down
    by number of copies for each language, audience and material type

    Args:
        system_id:              int, datastore system.did
        library_id:             int, datastore library.did
        user_ids:               list, list of datastore user.did
        start_date:             str, starting date (inclusive) in format YYYY-MM-DD
        end_date:               str, end date (inclusive) in format YYYY-MM-DD

    Returns:
        dataframe
    """
    df = query2dataframe(system_id, library_id, user_ids, start_date, end_date)
    data = create_branch_to_lang_audn_mat_dataframe(df)
    return data


def get_categories_breakdown(system_id, library_id, user_ids, start_date, end_date):
    """
    Queries datastore and creates categories dictionary with report
    data categories
    args:
        system_id:              int, datastore system.did
        library_id:             int, datastore library.did
        user_ids:               list, list of datastore user.did
        start_date:             str, starting date (inclusive) in format YYYY-MM-DD
        end_date:               str, end date (inclusive) in format YYYY-MM-DD
    returns:
        data:                   dict, data to be displayed broke down to different categories
    """
    df = query2dataframe(system_id, library_id, user_ids, start_date, end_date)
    data = generate_detailed_breakdown(df, start_date, end_date)

    return data


def get_fy_summary(system_id, library_id, user_ids):
    """
    Queries datastore and creates Pandas dataframe to be displayed as a report
    args:
        system_id:              int, datastore system.did
        library_id:             int, datastore library.did
        user_ids:               list, datastore user.did list
    returns:
        data:                   dict, data to be displayed broke down to different categories
    """
    date_today = date.today()
    if date_today.month <= 6:
        start_date = date.fromisoformat(f"{date_today.year - 1}-07-01")
    else:
        start_date = date.fromisoformat(f"{date_today.year}-07-01")
    end_date = date_today

    df = query2dataframe(system_id, library_id, user_ids, start_date, end_date)
    data = generate_fy_summary_for_display(df)

    return data


def get_lang_branch(
    system_id: int, library_id: int, user_ids: list[int], start_date: str, end_date: str
) -> DataFrame:
    """
    Queries datastore with given criteria and returns dataframe showing languages,
    audience, material type broken down by each branch.

    Args:
        system_id:              int, datastore system.did
        library_id:             int, datastore library.did
        user_ids:               list, list of datastore user.did
        start_date:             str, starting date (inclusive) in format YYYY-MM-DD
        end_date:               str, end date (inclusive) in format YYYY-MM-DD

    Returns:
        dataframe
    """
    df = query2dataframe(system_id, library_id, user_ids, start_date, end_date)
    data = create_lang_audn_mat_to_branch_dataframe(df)
    return data


def get_lang_breakdown(
    system_id: str, library_id: str, user_ids: list[int], start_date: str, end_date: str
) -> dict:
    """
    Queries datastore and breaks down data by individual language
    args:
        system_id:              int, datastore system.did
        library_id:             int, datastore library.did
        user_ids:               list, list of datastore user.did
        start_date:             str, starting date (inclusive) in format YYYY-MM-DD
        end_date:               str, end date (inclusive) in format YYYY-MM-DD
    returns:
        data:                   dict, data to be displayed broke down by language
    """
    df = query2dataframe(system_id, library_id, user_ids, start_date, end_date)
    data = generate_language_breakdown(df, start_date, end_date)
    mlogger.debug(f"Created {len(data['languages'])} dataframes for each language.")
    return data


def query2dataframe(
    system_id: int, library_id: int, user_ids: list[int], start_date: str, end_date: str
) -> DataFrame:
    """
    Queries datastore for relevant records and outputs the results
    as Pandas dataframe

    args:
        system_id:              int, datastore system.did
        library_id:             int, datastore library.did
        user_ids:               list, datastore user.did list

    returns:
        df:                     Pandas dataframe with following columns:
                                cart_id, cart_date, user, system, library, order_id,
                                lang_name, lang_code, audn, vendor, mattype, price
                                branch_code, branch_name, qty, fund, total
    """
    mlogger.debug(
        "Report query criteria: "
        f"system_id={system_id}, library_id={library_id}, "
        f"user_ids={user_ids}, start_date={start_date}, "
        f"end_date={end_date}"
    )

    with session_scope() as session:
        stmn = construct_report_query_stmn(
            system_id, library_id, user_ids, start_date, end_date
        )

        mlogger.debug(f"Report query stmn: {stmn}")

        df = read_sql(stmn, session.bind, parse_dates=["cart_date"])

        mlogger.debug(f"query2dataframe func. return dataframe with shape {df.shape}")
        return df
