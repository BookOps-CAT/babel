# -*- coding: utf-8 -*-

import pytest

# from babel import errors
from babel.ingest import xlsx


def test_ResourceDataReader_no_header():
    with pytest.raises(AttributeError) as exc:
        xlsx.ResourceDataReader("tests/test_sheets/eng.xlsx")
    assert str(exc.value) == "Header row number is a required argument"


def test_ResourceDataReader_no_title_col():
    with pytest.raises(AttributeError) as exc:
        xlsx.ResourceDataReader("tests/test_sheets/eng.xlsx", header_row=1)
    assert str(exc.value) == "Title column number is a required argument"


def test_ResourceDataReader_success():
    fh = "tests/test_sheets/eng.xlsx"
    data = xlsx.ResourceDataReader(
        fh,
        header_row=2,
        title_col=2,
        author_col=1,
        series_col=3,
        publisher_col=5,
        pub_place_col=8,
        pub_date_col=11,
        summary_col=10,
        isbn_col=6,
        upc_col=14,
        other_no_col=0,
        price_list_col=12,
        price_disc_col=13,
        desc_url_col=15,
        comment_col=16,
        misc_col=17,
    )

    assert data.min_row == 3
    assert data.ws.title == "Attikus"
    c = 0
    for d in data:
        if c == 0:
            assert d.title == "Zendegi"
            assert d.author == "Egan, Greg"
            assert d.series is None
            assert d.publisher == "Orion"
            assert d.pub_date == "2016"
            assert d.pub_place == "New York"
            assert d.isbn == "9785389109476"
            assert d.summary == "Summary 1 here"
            assert d.price_list == 29.00
            assert d.price_disc == 25.00
            assert d.upc == "5060099503825"
            assert d.other_no == "A12"
            assert d.desc_url == "https://en.wikipedia.org/wiki/Zendegi"
            assert d.comment == "order 3"
            assert d.misc == "rush"
        if c == 1:
            assert d.title == "Reamde :  a novel"
            assert d.author == "Stephenson, Neal"
            assert d.series is None
            assert d.publisher == "Harper"
            assert d.pub_date == "2019"
            assert d.pub_place == "Boston"
            assert d.isbn == "9785389109452"
            assert d.summary == "Summary 2 here"
            assert d.price_list == 13.00
            assert d.price_disc == 11.99
            assert d.upc == "5060099503826"
            assert d.other_no == "A13"
            assert d.desc_url == "https://en.wikipedia.org/wiki/Reamde"
            assert d.comment == "order 4"
            assert d.misc is None
        if c == 2:
            assert d.title == "The Best Science fiction of 2019"
            assert d.author is None
            assert d.series == "Asimov Magazine Selection"
            assert d.publisher is None
            assert d.pub_date is None
            assert d.pub_place is None
            assert d.isbn == "9785389112308"
            assert d.summary is None
            assert d.price_list == 15.99
            assert d.price_disc == 0.0
            assert d.upc == "5060099503827"
            assert d.other_no == "A14"
            assert d.desc_url is None
            assert d.comment == "juv"
            assert d.misc is None
        if c == 3:
            assert d.title == "1984"
            assert d.author == "Orwell, George"
            assert d.series is None
            assert d.publisher == "Harper"
            assert d.pub_date == "2018"
            assert d.pub_place == "New York"
            assert d.summary is None
            assert d.price_list == 9.99
            assert d.price_disc == 7.99
            assert d.upc == "5060099503828"
            assert d.desc_url is None
        c += 1
