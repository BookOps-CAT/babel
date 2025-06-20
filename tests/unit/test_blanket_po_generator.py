# -*- coding: utf-8 -*-
from datetime import date

import pytest

from babel.data.blanket_po_generator import create_blanketPO


def test_blanket_po_without_parameters():
    assert create_blanketPO() is None


def test_blanket_po_with_none_vendor_codes():
    assert create_blanketPO(None) is None


def test_blanket_po_type_error_exception():
    with pytest.raises(TypeError) as exc:
        create_blanketPO("foo")
    assert str(exc.value) == "vendor_codes param must be a list"


def test_blanket_po_single_vendor():
    vendor_codes = ["foo"]
    date_today = date.strftime(date.today(), "%Y%m%d")
    assert create_blanketPO(vendor_codes) == f"foo{date_today}0"


def test_blanket_po_multiple_venodrs():
    vendor_codes = ["foo", "bar"]
    date_today = date.strftime(date.today(), "%Y%m%d")
    assert create_blanketPO(vendor_codes) == f"multivendor{date_today}0"


def test_blanket_po_sequence():
    vendor_codes = ["foo"]
    date_today = date.strftime(date.today(), "%Y%m%d")
    assert create_blanketPO(vendor_codes, 3) == f"foo{date_today}3"
