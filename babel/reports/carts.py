# import pandas as pd


from data.transactions_carts import get_cart_details_as_dataframe


def summarize_cart(cart_id):
    details = {}
    df = get_cart_details_as_dataframe(cart_id)
    fdf = df.groupby('fund')

    # amount of money spend by fund
    funds = {}
    for fund, d in fdf:
        # damage = df['price'] * df['qty']
        fd = d.loc[:, ('price', 'qty')]
        fd['damage'] = fd['price'] * fd['qty']
        funds[fund] = {
            'damage': fd['damage'].sum(),
            'copies': fd['qty'].sum(),
            'titles': fd.shape[0]}

    details['funds'] = funds
    details['langs'] = ','.join(df['lang'].unique().tolist())
    details['vendors'] = ','.join(df['vendor'].unique().tolist())
    details['mattypes'] = ','.join(df['mattype'].unique().tolist())
    details['audns'] = ','.join(df['audn'].unique().tolist())

    return details
