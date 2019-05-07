# validates data passed from spreadsheets
import re


def value2string(value):
    return str(value)


def normalize_date(value):
    m = re.search(
        re.compile('\\d{4}', value))
    if m:
        return m.group(0)
