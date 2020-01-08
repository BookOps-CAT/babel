from collections import OrderedDict

from pandas import DataFrame, Series, Grouper
from matplotlib.figure import Figure


def generate_fy_summary_by_user_chart(user_data, language_data):
    # try refactoring it with one figure and two subplots
    f1 = Figure(
        figsize=(6.3, 4), dpi=100, tight_layout=True,
        frameon=False)
    f2 = Figure(
        figsize=(6.3, 4), dpi=100, tight_layout=True,
        frameon=False)
    a = f1.add_subplot(111)
    b = f2.add_subplot(111)

    users = user_data.keys()
    langs = language_data.keys()
    month_lbl = [
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    for user, y in user_data.items():
        a.plot(month_lbl, y)

    for lang, y in language_data.items():
        b.plot(month_lbl, y)

    a.set_xlabel('months')
    b.set_xlabel('months')
    a.set_ylabel('dollars allocated')
    b.set_ylabel('dollars allocated')
    a.spines['top'].set_visible(False)
    a.spines['right'].set_visible(False)
    b.spines['top'].set_visible(False)
    b.spines['right'].set_visible(False)
    a.legend(users)
    b.legend(langs)
    a.set_title('funds allocation in current FY by user')
    b.set_title('funds allocation in current FY by language')

    return f1, f2


def generate_fy_summary_for_display(df):
    data = dict()
    data['start_date'] = None
    data['end_date'] = None

    # unique carts by status
    status = dict()
    for k, d in df.groupby('cart_status'):
        cart_count = d['cart_id'].nunique()
        status[k] = cart_count
    data['status'] = status

    fdf = df[df['cart_status'] != 'in-works']
    # number of orders/titles
    data['orders'] = fdf['order_id'].nunique()

    # number of copies
    data['copies'] = fdf['qty'].sum()

    # funds
    funds = []
    for k, d in fdf.groupby('fund'):
        amount = (d['qty'] * d['price']).sum()
        funds.append(Series(dict(
            fund=k,
            amount=f'${amount:,.2f}')))
    data['funds'] = DataFrame(funds)

    # languages
    langs = []
    lang_time = dict()
    for k, d in fdf.groupby('lang_name'):
        amount = (d['qty'] * d['price']).sum()
        langs.append(Series(dict(
            lang=k,
            amount=f'${amount:,.2f}')))

        # languages in time chart data
        y = [0] * 12
        for m, md in d.groupby(Grouper(key='cart_date', freq='M')):
            m_amount = (md['price'] * md['qty']).sum()
            pos = m.month
            if pos <= 6:
                y[pos + 7] = m_amount
            else:
                y[pos - 7] = m_amount
        lang_time[k] = y

    data['langs'] = DataFrame(langs)
    data['langs_time'] = lang_time

    # audiences
    audns = []
    for k, d in fdf.groupby('audn'):
        amount = (d['qty'] * d['price']).sum()
        audns.append(Series(dict(
            audn=k,
            amount=f'${amount:,.2f}')))
    data['audns'] = DataFrame(audns)

    # material types
    mats = []
    for k, d in fdf.groupby('mattype'):
        amount = (d['qty'] * d['price']).sum()
        mats.append(Series(dict(
            type=k,
            amount=f'${amount:,.2f}')))
    data['mats'] = DataFrame(mats)

    # vendors
    vendors = []
    for k, d in fdf.groupby('vendor'):
        amount = (d['qty'] * d['price']).sum()
        vendors.append(Series(dict(
            vendor=k,
            amount=f'${amount:,.2f}')))

    data['vendors'] = DataFrame(vendors)

    # users in time
    users = dict()
    for k, d in fdf.groupby('user'):
        y = [0] * 12
        for m, md in d.groupby(Grouper(key='cart_date', freq='M')):
            amount = (md['price'] * md['qty']).sum()
            pos = m.month
            if pos <= 6:
                y[pos + 7] = amount
            else:
                y[pos - 7] = amount
        users[k] = y

    data['users_time'] = users

    return data


def generate_detailed_breakdown(df, start_date, end_date):
    """
    Creates report data in form of a dictionary
    based on Pandas dataframe

    args:
        df: Pandas dataframe
        start_date: str, report starting date (inclusive)
        end_date: str, report ending date (inclusive)

    returns:
        data: dict, data in form of dictionary
    """
    data = dict()
    data['start_date'] = start_date
    data['end_date'] = end_date

    # filter out carts that are not finilized
    fdf = df[df['cart_status'] != 'in-works']

    # breakdown by audience
    audns = []
    for k, d in fdf.groupby('audn'):
        orders_qty = d['order_id'].nunique()
        copies_qty = d['qty'].sum()
        amount = (d['price'] * d['qty']).sum()
        audns.append(Series(dict(
            audience=k,
            orders=orders_qty,
            copies=copies_qty,
            amount=f'${amount:,.2f}')))

    data['audns'] = DataFrame(audns)

    # breakdown by language
    langs = []
    langs_audns = []
    for k, d in fdf.groupby('lang_name'):
        orders_qty = d['order_id'].nunique()
        copies_qty = d['qty'].sum()
        amount = (d['price'] * d['qty']).sum()
        langs.append(Series(dict(
            language=k,
            orders=orders_qty,
            copies=copies_qty,
            amount=f'${amount:,.2f}')))

        for kk, dd in d.groupby('audn'):
            la_orders_qty = dd['order_id'].nunique()
            la_copies_qty = dd['qty'].sum()
            la_amount = (dd['price'] * dd['qty']).sum()
            langs_audns.append(Series(dict(
                language=k,
                audience=kk,
                orders=la_orders_qty,
                copies=la_copies_qty,
                amount=f'${la_amount:,.2f}')))

    data['langs'] = DataFrame(langs)
    data['langs_audns'] = DataFrame(langs_audns)

    # vendors
    vendors = []
    for k, d in fdf.groupby('vendor'):
        orders_qty = d['order_id'].nunique()
        copies_qty = d['qty'].sum()
        amount = (d['price'] * d['qty']).sum()
        vendors.append(Series(dict(
            vendor=k,
            orders=orders_qty,
            copies=copies_qty,
            amount=f'${amount:,.2f}')))

    data['vendors'] = DataFrame(vendors)

    # funds
    funds = []
    for k, d in fdf.groupby('fund'):
        orders_qty = d['order_id'].nunique()
        copies_qty = d['qty'].sum()
        amount = (d['price'] * d['qty']).sum()
        funds.append(Series(dict(
            fund=k,
            orders=orders_qty,
            copies=copies_qty,
            amount=f'${amount:,.2f}')))

    data['funds'] = DataFrame(funds)

    # material types
    mattypes = []
    mattypes_langs = []
    for k, d in fdf.groupby('mattype'):
        orders_qty = d['order_id'].nunique()
        copies_qty = d['qty'].sum()
        amount = (d['price'] * d['qty']).sum()
        mattypes.append(Series(dict(
            type=k,
            orders=orders_qty,
            copies=copies_qty,
            amount=f'${amount:,.2f}')))

        for kk, dd in d.groupby('lang_name'):
            l_orders_qty = dd['order_id'].nunique()
            l_copies_qty = dd['qty'].sum()
            l_amount = (dd['price'] * dd['qty']).sum()
            mattypes_langs.append(Series(dict(
                type=k,
                language=kk,
                orders=l_orders_qty,
                copies=l_copies_qty,
                amount=f'${l_amount:,.2f}')))

    data['mattypes'] = DataFrame(mattypes)
    data['mattypes_langs'] = DataFrame(mattypes_langs)

    return data


def generate_branch_breakdown(df, start_date, end_date):
    """
    Creates individual branches report data in form of a dictionary
    based on Pandas dataframe

    args:
        df: Pandas dataframe
        start_date: str, report starting date (inclusive)
        end_date: str, report ending date (inclusive)

    returns:
        data: dict, data in form of dictionary
    """
    data = dict()
    data['start_date'] = start_date
    data['end_date'] = end_date

    # filter out carts that are not finilized
    fdf = df[df['cart_status'] != 'in-works']

    # group by branch
    branches = OrderedDict()
    for k, d in fdf.groupby('branch_name'):
        branch = []
        total_copies = d['qty'].sum()
        ad = d[d['audn'] == 'adult']
        adult_copies = ad['qty'].sum()
        yd = d[d['audn'] == 'young adult']
        ya_copies = yd['qty'].sum()
        jd = d[d['audn'] == 'juvenile']
        juv_copies = jd['qty'].sum()
        for kk, dd in d.groupby('lang_name'):
            total_lang_copies = dd['qty'].sum()
            add = dd[dd['audn'] == 'adult']
            adult_lang_copies = add['qty'].sum()
            ydd = dd[dd['audn'] == 'juvenile']
            juv_lang_copies = ydd['qty'].sum()
            ydd = dd[dd['audn'] == 'young adult']
            ya_lang_copies = ydd['qty'].sum()

            branch.append(Series(
                {
                    '': kk,
                    'total': total_lang_copies,
                    'adult': adult_lang_copies,
                    'ya': ya_lang_copies,
                    'juv': juv_lang_copies
                }))
        branch.append(Series(
            {
                '': 'combined',
                'total': total_copies,
                'adult': adult_copies,
                'ya': ya_copies,
                'juv': juv_copies
            }))

        bdf = DataFrame(branch)
        if not bdf.empty:
            branches[k] = bdf

    data['branches'] = branches

    return data
