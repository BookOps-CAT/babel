# -*- coding: utf-8 -*-
import unittest


from context import validators


class TestValue2String(unittest.TestCase):

    def test_int_to_unicode(self):
        value = 2016
        value_as_uni = validators.value2string(value)
        self.assertIsInstance(value_as_uni, str)

    def test_float_to_unicode(self):
        value = 12.99
        value_as_uni = validators.value2string(value)
        self.assertIsInstance(value_as_uni, str)

    def test_str_to_unicode(self):
        value = 'Маэстра'
        value_as_uni = validators.value2string(value)
        self.assertIsInstance(value_as_uni, str)

    def test_none_returns_none(self):
        value = None
        value_as_uni = validators.value2string(value)
        self.assertIsNone(value_as_uni)


class TestNormalizeDate(unittest.TestCase):
    """Test date parsing"""

    def test_int_to_string(self):
        date = validators.normalize_date(2016)
        self.assertEqual(date, '2016')

    def test_buried_date(self):
        date = validators.normalize_date('07/12/2016')
        self.assertEqual(date, '2016')

    def test_buried_date_with_diacritics(self):
        date = validators.normalize_date('2016年1月')
        self.assertEqual(date, '2016')

    def test_incorect_returns_none(self):
        date = validators.normalize_date('Jul=16')
        self.assertIsNone(date)


class TestNormalizeISBN(unittest.TestCase):
    """Test parsing and normalizing ISBNs"""

    def test_None_returns_none(self):
        isbn = validators.normalize_isbn(None)
        self.assertIsNone(isbn)

    def test_white_space_returns_none(self):
        isbn = validators.normalize_isbn('')
        self.assertIsNone(isbn)

    def test_incorrect_isbn_returns_none(self):
        isbn = validators.normalize_isbn('23980433')
        self.assertIsNone(isbn)

    def test_13_digits_upc_returns_none(self):
        isbn = validators.normalize_isbn('5060099503825')
        self.assertIsNone(isbn)

    def test_10_digits_valid_isbn(self):
        isbn = validators.normalize_isbn('8376723979')
        self.assertEqual(isbn, '8376723979')

    def test_13_digits_valid_isbn(self):
        isbn = validators.normalize_isbn('9788376723976')
        self.assertEqual(isbn, '9788376723976')

    def test_stripping_dashes(self):
        isbn = validators.normalize_isbn('978-8-37-672397-6')
        self.assertEqual(isbn, '9788376723976')

    def test_stripping_white_space(self):
        isbn = validators.normalize_isbn(' 9788 37672397 6 ')
        self.assertEqual(isbn, '9788376723976')

    def test_value_with_line_breaks(self):
        isbn = validators.normalize_isbn('978-8-37-672397-6  \n 8376723979')
        self.assertEqual(isbn, '9788376723976')


if __name__ == '__main__':
    unittest.main()
