# -*- coding: utf-8 -*-

import unittest


from context import data_objs


class TestVenData(unittest.TestCase):
    """Tests the structure of vendor data extracted from vendor sheet"""

    def test_data_attributes(self):
        data = data_objs.VenData()
        self.assertEqual(
            data._fields,
            ('title', 'author', 'series', 'publisher',
             'pub_date', 'summary', 'isbn', 'upc',
             'other_no', 'price_list', 'price_disc',
             'desc_url'))

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
        self.assertEqual(data.price_list, 0.0)
        self.assertEqual(data.price_disc, 0.0)
        self.assertIsNone(data.desc_url)

    def test_data_population(self):
        data = data_objs.VenData(
            title='Test title',
            author='Smith, John',
            publisher='TestPub',
            pub_date='2019',
            isbn='978178349005x',
            price_list=12.00,
            price_disc=9.99)
        self.assertEqual(data.title, 'Test title')
        self.assertEqual(data.author, 'Smith, John')
        self.assertIsNone(data.series)
        self.assertEqual(data.publisher, 'TestPub')
        self.assertEqual(data.pub_date, '2019')
        self.assertIsNone(data.summary)
        self.assertEqual(data.isbn, '978178349005x')
        self.assertIsNone(data.upc)
        self.assertIsNone(data.other_no)
        self.assertEqual(data.price_list, 12.00)
        self.assertEqual(data.price_disc, 9.99)
        self.assertIsNone(data.desc_url)


if __name__ == '__main__':
    unittest.main()
