# -*- coding: utf-8 -*-
from decimal import Decimal
import unittest


from .context import validators


class TestValue2String(unittest.TestCase):
    def test_int_to_unicode(self):
        value = 2016
        value_as_uni = validators.value2string(value)
        self.assertIsInstance(value_as_uni, str)
        self.assertEqual(value_as_uni, "2016")

    def test_float_to_unicode(self):
        value = 12.99
        value_as_uni = validators.value2string(value)
        self.assertIsInstance(value_as_uni, str)
        self.assertEqual(value_as_uni, "12.99")

    def test_str_to_unicode(self):
        value = "Маэстра"
        value_as_uni = validators.value2string(value)
        self.assertIsInstance(value_as_uni, str)
        self.assertEqual(value_as_uni, value)

    def test_none_returns_none(self):
        value = None
        value_as_uni = validators.value2string(value)
        self.assertIsNone(value_as_uni)

    def test_long_number_to_unicode(self):
        value = 5060099503825
        value_as_uni = validators.value2string(value)
        self.assertEqual(value_as_uni, "5060099503825")


class TestNormalizeDate(unittest.TestCase):
    """Test date parsing"""

    def test_int_to_string(self):
        date = validators.normalize_date(2016)
        self.assertEqual(date, "2016")

    def test_buried_date(self):
        date = validators.normalize_date("07/12/2016")
        self.assertEqual(date, "2016")

    def test_buried_date_with_diacritics(self):
        date = validators.normalize_date("2016年1月")
        self.assertEqual(date, "2016")

    def test_incorect_returns_none(self):
        date = validators.normalize_date("Jul=16")
        self.assertIsNone(date)


class TestNormalizeISBN(unittest.TestCase):
    """Test parsing and normalizing ISBNs"""

    def test_None_returns_none(self):
        isbn = validators.normalize_isbn(None)
        self.assertIsNone(isbn)

    def test_white_space_returns_none(self):
        isbn = validators.normalize_isbn("")
        self.assertIsNone(isbn)

    def test_incorrect_isbn_returns_none(self):
        isbn = validators.normalize_isbn("23980433")
        self.assertIsNone(isbn)

    def test_13_digits_upc_returns_none(self):
        isbn = validators.normalize_isbn("5060099503825")
        self.assertIsNone(isbn)

    def test_10_digits_valid_isbn(self):
        isbn = validators.normalize_isbn("8376723979")
        self.assertEqual(isbn, "8376723979")

    def test_13_digits_valid_isbn(self):
        isbn = validators.normalize_isbn("9788376723976")
        self.assertEqual(isbn, "9788376723976")

    def test_stripping_dashes(self):
        isbn = validators.normalize_isbn("978-8-37-672397-6")
        self.assertEqual(isbn, "9788376723976")

    def test_stripping_white_space(self):
        isbn = validators.normalize_isbn(" 9788 37672397 6 ")
        self.assertEqual(isbn, "9788376723976")

    def test_value_with_line_breaks(self):
        isbn = validators.normalize_isbn("978-8-37-672397-6  \n 8376723979")
        self.assertEqual(isbn, "9788376723976")

    def test_isbn_with_extra_data(self):
        isbn = validators.normalize_isbn("9788376723976 (pbk.)")
        self.assertEqual(isbn, "9788376723976")


class TestNormalizePrice(unittest.TestCase):
    """Tests parsing of prices from spreasheets"""

    def test_none_returns_none(self):
        price = validators.normalize_price(None)
        self.assertEqual(price, Decimal(0.00))

    def test_empty_string_returns_none(self):
        price = validators.normalize_price("")
        self.assertEqual(price, Decimal(0.00))

    def test_zero_returns_zero(self):
        price = validators.normalize_price(0)
        self.assertEqual(price, Decimal(0))

    def test_int_converted_to_float(self):
        price = validators.normalize_price(25)
        self.assertEqual(price, Decimal(25))

    def test_float_stays_as_float(self):
        price = validators.normalize_price(9.99)
        self.assertEqual(price, Decimal(9.99))

    def test_price_as_str_converted_to_decimal(self):
        price = validators.normalize_price("9.99")
        self.assertEqual(price, Decimal("9.99"))

    def test_price_as_str_with_dollars_converted_to_decimal(self):
        price = validators.normalize_price("$123.99")
        self.assertEqual(price, Decimal("123.99"))

    def test_price_as_str_without_decimals(self):
        price = validators.normalize_price("$9")
        self.assertEqual(price, Decimal("9.0"))

    def test_price_with_long_decimal(self):
        price = validators.normalize_price(5.9234)
        self.assertEqual(price, Decimal(5.9234))

    def test_price_with_long_decimal_as_string(self):
        price = validators.normalize_price("$15.9234")
        self.assertEqual(price, Decimal("15.9234"))

    def test_price_with_extra_spaces(self):
        price = validators.normalize_price(" $12.99\n")
        self.assertEqual(price, Decimal("12.99"))


class TestCharactersLimit4Datastore(unittest.TestCase):
    """Test shortening of string for datastore storage"""

    def test_None(self):
        value = validators.shorten4datastore(None, 5)
        self.assertIsNone(value)

    def test_chr_allowed_not_integer(self):
        with self.assertRaises(AttributeError):
            validators.shorten4datastore("foo", "bar")

    def test_correct_shortening(self):
        value = validators.shorten4datastore("foo", 1)
        self.assertEqual(value, "f")

    def test_dots_trigger_not_firing(self):
        value = validators.shorten4datastore("shrubbery", 5)
        self.assertEqual(value, "shrub")

    def test_dots_trigger_activated(self):
        value = validators.shorten4datastore("shrubbery", 9)
        self.assertEqual(value, "shrubbery")

    def test_long_value(self):
        value = validators.shorten4datastore("foo" * 200, 250)
        self.assertEqual(len(value), 250)
        self.assertEqual(value, ("foo" * 200)[:250])

    def test_long_value_without_skip_dots(self):
        value = validators.shorten4datastore("foo" * 50, 250)
        self.assertEqual(len(value), 150)
        self.assertNotEqual(value[-4:], " ...")


class TestNormalizeWhiteSpaces(unittest.TestCase):
    """Tests removal of white spaces from values"""

    def test_value_is_none(self):
        self.assertIsNone(validators.normalize_whitespaces(None))

    def test_value_is_empty_string(self):
        self.assertIsNone(validators.normalize_whitespaces(""))

    def test_value_is_integer(self):
        self.assertEqual(validators.normalize_whitespaces(5), "5")

    def test_value_with_tabs(self):
        self.assertEqual(validators.normalize_whitespaces("foo\tbar"), "foo bar")

    def test_value_with_new_line(self):
        self.assertEqual(
            validators.normalize_whitespaces("foo bar\nshrubbery"), "foo bar shrubbery"
        )

    def test_starting_and_trailing_whitespace(self):
        self.assertEqual(validators.normalize_whitespaces("  foo bar   "), "foo bar")


if __name__ == "__main__":
    unittest.main()
