from collections import namedtuple


VenData = namedtuple(
    'VenData',
    [
        'title',
        'author',
        'series',
        'publisher',
        'pub_date',
        'summary',
        'isbn',
        'upc',
        'other_no',
        'price_list',
        'price_disc',
        'desc_url'
    ],
    defaults=[
        None, None, None, None,
        None, None, None, None,
        None, 0.0, 0.0, None])
