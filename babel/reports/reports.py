from pandas import DataFrame, Series


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
            amount=f'${amount:.2f}')))
    data['funds'] = DataFrame(funds)

    # languages
    langs = []
    for k, d in fdf.groupby('lang_name'):
        amount = (d['qty'] * d['price']).sum()
        langs.append(Series(dict(
            lang=k,
            amount=f'${amount:.2f}')))
    data['langs'] = DataFrame(langs)

    # audiences
    audns = []
    for k, d in fdf.groupby('audn'):
        amount = (d['qty'] * d['price']).sum()
        audns.append(Series(dict(
            audn=k,
            amount=f'${amount:.2f}')))
    data['audns'] = DataFrame(audns)

    # material types
    mats = []
    for k, d in fdf.groupby('mattype'):
        amount = (d['qty'] * d['price']).sum()
        mats.append(Series(dict(
            type=k,
            amount=f'${amount:.2f}')))
    data['mats'] = DataFrame(mats)

    # vendors
    vendors = []
    for k, d in fdf.groupby('vendor'):
        amount = (d['qty'] * d['price']).sum()
        vendors.append(Series(dict(
            vendor=k,
            amount=f'${amount:.2f}')))

    data['vendors'] = DataFrame(vendors)

    return data
