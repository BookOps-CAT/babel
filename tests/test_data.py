# -*- coding: utf-8 -*-

from decimal import Decimal
import unittest


from .context import data_objs


class TestVenData(unittest.TestCase):
    """Tests the structure of vendor data extracted from vendor sheet"""

    def test_data_attributes(self):
        data = data_objs.VenData()
        self.assertEqual(
            data._fields,
            (
                "title",
                "add_title",
                "author",
                "series",
                "publisher",
                "pub_date",
                "pub_place",
                "summary",
                "isbn",
                "upc",
                "other_no",
                "price_list",
                "price_disc",
                "desc_url",
                "comment",
                "misc",
            ),
        )

    def test_data_defaults(self):
        # afer upgrade to python 3.7.3 use somenamedtuple._field_defaults
        data = data_objs.VenData()
        self.assertIsNone(data.title)
        self.assertIsNone(data.author)
        self.assertIsNone(data.series)
        self.assertIsNone(data.publisher)
        self.assertIsNone(data.pub_date)
        self.assertIsNone(data.summary)
        self.assertIsNone(data.isbn)
        self.assertIsNone(data.upc)
        self.assertIsNone(data.other_no)
        self.assertIsNone(data.price_list)
        self.assertEqual(data.price_disc, Decimal("0.00"))
        self.assertIsNone(data.desc_url)

    def test_data_population(self):
        data = data_objs.VenData(
            title="Test title",
            author="Smith, John",
            publisher="TestPub",
            pub_date="2019",
            isbn="978178349005x",
            price_list=Decimal("12"),
            price_disc=Decimal("9.9"),
        )
        self.assertEqual(data.title, "Test title")
        self.assertEqual(data.author, "Smith, John")
        self.assertIsNone(data.series)
        self.assertEqual(data.publisher, "TestPub")
        self.assertEqual(data.pub_date, "2019")
        self.assertIsNone(data.summary)
        self.assertEqual(data.isbn, "978178349005x")
        self.assertIsNone(data.upc)
        self.assertIsNone(data.other_no)
        self.assertEqual(data.price_list, Decimal("12.00"))
        self.assertEqual(data.price_disc, Decimal("9.90"))
        self.assertIsNone(data.desc_url)
        self.assertIsNone(data.comment)
        self.assertIsNone(data.misc)


if __name__ == "__main__":
    unittest.main()
