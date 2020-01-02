from pandas import DataFrame, Series, Grouper
from matplotlib.figure import Figure


def generate_fy_summary_by_user_chart(user_data, language_data):
    # try refactoring it with one figure and two subplots
    f1 = Figure(
        figsize=(8.65, 4), dpi=100, tight_layout=True,
        frameon=False)
    f2 = Figure(
        figsize=(8.65, 4), dpi=100, tight_layout=True,
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
