# price in babel is converted to cents for storing
# in local db (stored as integers) &
# converted back to dollars when retrieved and displayed

from decimal import *


def dollars2cents(price):
    """converts price from dollars to cents"""
    # print price * 100
    if price is None:
        price = 0.0
    price_in_cents = Decimal(price).quantize(
        Decimal('.01')) * 100
    price_in_cents = int(price_in_cents)
    return price_in_cents


def cents2dollars(price):
    """converts price from cents to dollars"""
    if price is None:
        price = 0.0
    price_in_dollars = float(price) / 100.0
    price_in_dollars = Decimal(price_in_dollars).quantize(Decimal('.01'))
    return price_in_dollars
