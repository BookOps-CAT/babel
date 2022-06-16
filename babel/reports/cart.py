"""
This module includes methods used to tabulate and format data to be displayed
in CartView.
"""

from collections import OrderedDict

from data.transactions_carts import get_cart_details_as_dataframe


def tabulate_cart_data(cart_id):
    df = get_cart_details_as_dataframe(cart_id)

    data = OrderedDict()
    for branch, value in df.groupby("branch"):
        titles = value["order_id"].nunique()
        copies = value["qty"].sum()
        dollars = (value["qty"] * value["price"]).sum()
        dollars = f"${dollars:.2f}"
        data[branch] = dict(titles=titles, copies=copies, dollars=dollars)

    return data


def format_nypl_sierra_data_for_display(bib_response: dict, item_resposne: dict) -> str:
    """
    Parses and formats bibliographic and item data received from
    NYPL Platform middleware.

    Args:
        bib_response:                   `requests.Response.json()` instance
        item_response:                  `requests.Response.json()` instance

    Returns:
        str for display
    """
    pass


def format_bpl_sierra_data_for_display(bib_response: dict) -> str:
    """
    Parses and fomrat bibliographic and item data received from
    BPL Solr middleware

    Args:
        bib_response:                   `requests.Resposne.json()` instance

    Returns:
        str for display
    """
    pass
