# translates objects from one format to another
import re


def parse_year(date_str):
    try:
        date_str.encode(encoding='UTF-8', errors='ignore')
    except:
        return None
    pattern = re.compile(r'[12]\d\d\d')
    match = re.search(pattern, date_str)
    if match:
        return match.group(0)
    else:
        return None


def parse_isbn(isbn):
    if type(isbn) is unicode or type(isbn) is str:
        # print 'parsing ISBN as unicode'
        isbn = isbn.strip()
        isbn_str = str(isbn)
        isbn_str = isbn_str.replace('-', '')
        isbn_str = isbn_str.replace(' ', '')
        pattern = re.compile(r'\d{12}[xX]|\d{13}|\d{10}|\d{9}[xX]')
        match = re.search(pattern, isbn_str)
        if match:
            # print 'pattern found, isbn:', match.group(0)
            return match.group(0)
        else:
            return None
    elif isbn is None:
        return None
    else:
        # print 'parsing ISBN as a integer'
        isbn_str = str(int(isbn))
        if len(isbn_str) == 13 or len(isbn_str) == 10:
            # print isbn_str
            return isbn_str
        else:
            return None


if __name__ == '__main__':
    year_test = parse_year('2016-19-12')
    print year_test
    isbn_test = parse_isbn(unicode('  9780973879826'))
    print isbn_test
