# methods for generating order details reports

import pandas as pd


def pull_table_to_dataframe(stmn, session):
    """
    turns SQLAlchemy results into Pandas dataframe
    args:
        stmn: string, SQL statement
        session: sqlalchemy.orm.session.Session
    returns:
        dataframe: pandas.core.frame.DataFrame
    """

    df = pd.read_sql_query(stmn, session.bind)
    return df


def find_total_titles(df):
    """
    finds total number of titles in order
    args:
        df: pandas.core.frame.DataFrame
    returns:
        title_count, int
    """

    return df['os_id'].nunique()


def find_total_copies(df):
    """
    finds total number of copies in order
    args:
        df: pandas.core.frame.DataFrame
    returns:
        copies_count, int
    """

    return df['qty'].sum()


def find_total_cost(df):
    """
    finds total cost of order
    args:
        df: pandas.code.frame.DataFrame
    returns:
        total_cost, int (in cents)
    """

    cdf = df[['qty', 'price']].copy()
    cdf['cost'] = df['qty'] * df['price']
    return cdf['cost'].sum()


def find_linked(df):
    """
    finds linked records in order
    args:
    df: pandas.core.frame.DataFrame
    returns:
        linked_recs: tuple, first value Boolean,
            second int missing bibs, third int missing orders
    """

    ldf = df[['os_id', 'bNumber', 'oNumber']].copy()
    ubdf = ldf[ldf['bNumber'].isnull()]
    unlinked_bibs = ubdf['os_id'].nunique()
    uodf = ldf[ldf['oNumber'].isnull()]
    unlinked_orders = uodf['os_id'].nunique()

    if unlinked_bibs == 0 and unlinked_orders == 0:
        linked = True
    else:
        linked = False

    return (linked, unlinked_bibs, unlinked_orders)


def title_per_fund_breakdown(df):
    """
    creates a list funds with title and audience data for each fund
    args:
        df: pandas.code.frame.DataFrame
    returns:
        titles_per_fund: list of tuples, sorted by fund code,
            tuple values: fund code, audn code, number of titles
    """
    tdf = df.groupby(['fcode', 'acode'])  # groupby sorts by default
    return [(g[0], g[1], data['os_id'].nunique()) for g, data in tdf]


def copies_per_fund_breakdown(df):
    """
    creates a list of funds with number of copies per audience
    args:
        df: pandas.code.frame.DataFrame
    returns:
        copies_per_fund: list of tuples, sorted by fund code,
            tuple values:  funds, audn codes and number of copies for each
    """
    cdf = df.groupby(['fcode', 'acode'])
    return [(g[0], g[1], data['qty'].sum()) for g, data in cdf]


def cost_per_fund_breakdown(df):
    """
    creates a list of funds with cost per audience
    args:
        df: pandas.code.frame.DataFrame
    returns:
        cost_per_fund: list of tuples, sorted by fund code,
            tuple values: fund code, audn code, cost in cents
    """
    results = []
    cdf = df[['fcode', 'qty', 'acode', 'price']].copy().groupby(['fcode', 'acode'])
    for g, d in cdf:
        p = d.copy()
        p['cost'] = p['qty'] * p['price']
        results.append((g[0], g[1], p['cost'].sum()))
    return results
