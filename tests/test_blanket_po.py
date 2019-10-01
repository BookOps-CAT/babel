# -*- coding: utf-8 -*-
from datetime import date
import unittest


from context import create_blanketPO


class TestBlanketPO(unittest.TestCase):
    """Tests creation of new unique wlo numbers"""

    def test_without_parameters(self):
        self.assertIsNone(create_blanketPO())

    def test_vendor_codes_is_None(self):
        self.assertIsNone(create_blanketPO(None, 0))

    def test_vendor_code_is_str(self):
        with self.assertRaises(TypeError):
            create_blanketPO('jamal', 0)

    def test_vendor_codes_are_empty_list(self):
        self.assertIsNone(create_blanketPO([], 0))

    def test_correct_vendor_codes(self):
        vendor_codes = ['jamal']
        date_today = date.strftime(date.today(), '%Y%m%d')
        self.assertEqual(
            create_blanketPO(vendor_codes), f'jamal{date_today}0')

    def test_correct_multi_vendor_codes(self):
        vendor_codes = ['jamal', 'chbks']
        date_today = date.strftime(date.today(), '%Y%m%d')
        self.assertEqual(
            create_blanketPO(vendor_codes), f'multivendor{date_today}0')

    def test_sequence(self):
        vendor_codes = ['jamal']
        date_today = date.strftime(date.today(), '%Y%m%d')
        self.assertEqual(
            create_blanketPO(vendor_codes, 3), f'jamal{date_today}3')


if __name__ == '__main__':
    unittest.main()
