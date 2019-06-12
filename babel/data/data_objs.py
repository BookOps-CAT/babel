from collections import namedtuple


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
        0.0, None, None])
