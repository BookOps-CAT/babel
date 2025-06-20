# -*- coding: utf-8 -*-
from decimal import Decimal

import pytest


from babel.data import validators


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (2016, "2016"),
        ("07/12/2016", "2016"),
        ("2016年1月", "2016"),
        ("Jul=16", None),
        ("2016-07-12", "2016"),
    ],
)
def test_normalize_date(arg, expectation):
    assert validators.normalize_date(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (None, None),
        ("", None),
        ("23980433", None),
        ("5060099503825", None),
        ("8376723979", "8376723979"),
        ("9788376723976", "9788376723976"),
        ("978-8-37-672397-6", "9788376723976"),
        (" 9788 37672397 6 ", "9788376723976"),
        ("978-8-37-672397-6  \n 8376723979", "9788376723976"),
        ("9788376723976 (pbk.)", "9788376723976"),
    ],
)
def test_normalize_isbn(arg, expectation):
    assert validators.normalize_isbn(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (None, Decimal("0.00")),
        ("", Decimal("0.00")),
        ("0", Decimal("0.00")),
        (0, Decimal("0.00")),
        ("$0", Decimal("0.00")),
        ("$0.00", Decimal("0.00")),
        (25, Decimal("25.00")),
        ("25.00", Decimal("25.00")),
        ("$9.99", Decimal("9.99")),
        ("$123.45", Decimal("123.45")),
        ("$0.99", Decimal("0.99")),
        ("$100", Decimal("100.00")),
        ("$100.00", Decimal("100.00")),
        ("$100.123", Decimal("100.123")),
        ("$100.1234", Decimal("100.1234")),
        ("$100.12345", Decimal("100.12345")),
    ],
)
def test_normalize_price(arg, expectation):
    assert validators.normalize_price(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo\tbar", "foo bar"),
        ("foo\nbar", "foo bar"),
        ("foobar", "foobar"),
        (" foo bar ", "foo bar"),
        ("", None),
    ],
)
def test_normalize_whitespaces(arg, expectation):
    assert validators.normalize_whitespaces(arg) == expectation


@pytest.mark.parametrize(
    "arg1,arg2,expectation",
    [
        (None, 5, None),
        ("foo", 1, "f"),
        ("shrubbery", 5, "shrub"),
        ("shrubbery", 9, "shrubbery"),
        ("foo" * 200, 250, ("foo" * 200)[:250]),
        ("", 5, ""),
        (" ", 5, " "),
    ],
)
def test_shorten4datastore(arg1, arg2, expectation):
    assert validators.shorten4datastore(arg1, arg2) == expectation


def test_shorten4datastore_invalid_chr_allowed_type():
    with pytest.raises(TypeError) as exc:
        validators.shorten4datastore("foo", "bar")
    assert str(exc.value) == "chr_allowed must be an integer"


def test_shorten4datastore_invalid_value_type():
    with pytest.raises(TypeError) as exc:
        validators.shorten4datastore(12345, 3)
    assert str(exc.value) == "shorten4datastore accepts only strings, got <class 'int'>"


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("foo", "foo"),
        ("", ""),
        (None, None),
        (5, "5"),
        (2016, "2016"),
        (2.05, "2.05"),
        (5060099503825, "5060099503825"),
        ([1, 2, 3], "[1, 2, 3]"),
        ("Маэстра", "Маэстра"),
    ],
)
def test_value2string(arg, expectation):
    assert validators.value2string(arg) == expectation
