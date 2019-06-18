import pandas as pd


from gui.data_retriever import get_cart_details_as_dataframe


def summarize_cart(cart_id):
    df = get_cart_details_as_dataframe(cart_id)
    print(df.head())

