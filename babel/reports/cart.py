from collections import OrderedDict

from data.transactions_carts import get_cart_details_as_dataframe


def tabulate_cart_data(cart_id):
    df = get_cart_details_as_dataframe(cart_id)

    data = OrderedDict()
    for branch, value in df.groupby('branch'):
        titles = value['order_id'].nunique()
        copies = value['qty'].sum()
        dollars = (value['qty'] * value['price']).sum()
        dollars = f'${dollars:.2f}'
        data[branch] = dict(
            titles=titles,
            copies=copies,
            dollars=dollars)

    return data
