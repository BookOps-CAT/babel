from pandas import DataFrame, Series, Grouper
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
from numpy import arange


def generate_fy_summary_by_user_chart(data):
    f = Figure(figsize=(8.8, 4), dpi=100, tight_layout=True)
    a = f.add_subplot(111)
    users = data.keys()
    x = arange(12)
    month_lbl = [
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    for user, y in data.items():
        a.plot(x, y)
        # f.xticks(x, month_lbl)
        # f.ylabel('amount')
        # f.xlabel('months')
    f.legend(users)
    # f.title('fiscal year to date summary')
    # ax = plt.gca()
    # ax.spines['top'].set_visible(False)
    # ax.spines['right'].set_visible(False)
    return f


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
    for k, d in fdf.groupby('lang_name'):
        amount = (d['qty'] * d['price']).sum()
        langs.append(Series(dict(
            lang=k,
            amount=f'${amount:,.2f}')))
    data['langs'] = DataFrame(langs)

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

    data['users'] = users

    return data
