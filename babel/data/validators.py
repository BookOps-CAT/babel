# validates data passed from spreadsheets
from decimal import Decimal
import re

p1 = re.compile(r'[12]\d{3}')
p2 = re.compile(r'97\d{10}[xX]|97\d{11}|^\d{10}(?!\d)|^\d{9}[xX](?!\d)')
p3 = re.compile(r'\d{1,4}\.\d{1,}|\d{1,4}')


def value2string(value):
    if type(value) is str:
        return value
    elif value is None:
        return value
    else:
        return str(value)


def normalize_date(value):
    value = value2string(value)
    if value:
        m = re.search(p1, value)
        if m:
            return m.group(0)


def normalize_isbn(value):
    value = value2string(value)
    if value:
        value = value.replace('-', '').replace(' ', '').replace(
            '\n', ' ').lower().strip()
        m = re.search(p2, value)
        if m:
            return m.group(0)


def normalize_price(value):
    if type(value) is int:
        return Decimal(value)
    elif type(value) is float:
        return Decimal(value)
    elif type(value) is str:
        m = re.search(p3, value)
        if m:
            return Decimal(m.group(0))
        else:
            return Decimal('0.00')
    else:
        return Decimal('0.00')


def normalize_whitespaces(value):
    if type(value) is str:
        value = value.replace('\t', ' ').replace('\n', ' ')
        return value
    else:
        return value
