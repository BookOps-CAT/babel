# -*- coding: utf-8 -*-

import unittest


from context import xlsx


class TestOrderDataReader(unittest.TestCase):
    """Test parsing vendor sheet with title/order info"""

    def setUp(self):
        self.fh_eng = './test_sheets/eng.xlsx'

    def test_no_header_provided(self):
        with self.assertRaises(AttributeError):
            xlsx.OrderDataReader(self.fh_eng)

    def test_no_title_col_provided(self):
        with self.assertRaises(AttributeError):
            xlsx.OrderDataReader(self.fh_eng, header_row=1)

    def test_eng_sheet(self):
        data = xlsx.OrderDataReader(
            self.fh_eng,
            header_row=1,
            title_col=2,
            author_col=1,
            series_col=3,
            publisher_col=5,
            pub_date_col=11,
            summary_col=10,
            isbn_col=6,
            upc_col=14,
            other_no_col=0,
            price_list_col=12,
            price_disc_col=13,
            desc_url_col=15)

        self.assertEqual(data.min_row, 3)
        self.assertEqual(
            data.ws.title, 'Attikus')

        c = 0
        for d in data:
            if c == 0:
                self.assertEqual(d.title, 'Zendegi')
                self.assertEqual(d.author, 'Egan, Greg')
                self.assertIsNone(d.series)
                self.assertEqual(d.publisher, 'Orion')
                self.assertEqual(d.pub_date, '2016')
                self.assertIsNone(d.pub_place)
                self.assertEqual(d.isbn, '9785389109476')
                self.assertEqual(d.summary, 'Summary 1 here')
                self.assertEqual(d.price_list, 29.00)
                self.assertEqual(d.price_disc, 25.00)
                self.assertEqual(d.upc, '5060099503825')
                self.assertEqual(d.other_no, 'A12')
                self.assertEqual(
                    d.desc_url, 'https://en.wikipedia.org/wiki/Zendegi')
                self.assertIsNone(d.misc)
            if c == 1:
                self.assertEqual(d.title, 'Reamde :  a novel')
                self.assertEqual(d.author, 'Stephenson, Neal')
                self.assertIsNone(d.series)
                self.assertEqual(d.publisher, 'Harper')
                self.assertEqual(d.pub_date, '2019')
                self.assertIsNone(d.pub_place)
                self.assertEqual(d.isbn, '9785389109452')
                self.assertEqual(d.summary, 'Summary 2 here')
                self.assertEqual(d.price_list, 13.00)
                self.assertEqual(d.price_disc, 11.99)
                self.assertEqual(d.upc, '5060099503826')
                self.assertEqual(d.other_no, 'A13')
                self.assertEqual(
                    d.desc_url, 'https://en.wikipedia.org/wiki/Reamde')
                self.assertIsNone(d.misc)
            if c == 2:
                self.assertEqual(d.title, 'The Best Science fiction of 2019')
                self.assertIsNone(d.author)
                self.assertEqual(d.series, 'Asimov Magazine Selection')
                self.assertIsNone(d.publisher)
                self.assertIsNone(d.pub_date)
                self.assertIsNone(d.pub_place)
                self.assertEqual(d.isbn, '9785389112308')
                self.assertIsNone(d.summary)
                self.assertEqual(d.price_list, 15.99)
                self.assertEqual(d.price_disc, 0.0)
                self.assertEqual(d.upc, '5060099503827')
                self.assertEqual(d.other_no, 'A14')
                self.assertIsNone(d.desc_url)
                self.assertIsNone(d.misc)
            c += 1


if __name__ == '__main__':
    unittest.main()
