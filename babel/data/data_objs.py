from collections import namedtuple
from decimal import Decimal


VenData = namedtuple(
    'VenData',
    [
        'title',
        'add_title',
        'author',
        'series',
        'publisher',
        'pub_date',
        'pub_place',
        'summary',
        'isbn',
        'upc',
        'other_no',
        'price_list',
        'price_disc',
        'desc_url',
        'misc'
    ],
    defaults=[
        None, None, None, None,
        None, None, None, None,
        None, None, None, None,
        Decimal('0.00'), None, None])
