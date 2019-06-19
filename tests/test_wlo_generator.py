# -*- coding: utf-8 -*-

import unittest


from context import wlo_pool


class TestWlo(unittest.TestCase):
    """Tests creation of new unique wlo numbers"""

    def test_None(self):
        last_wlo = None
        wlo_numbers = wlo_pool(None, 1)
        self.assertEqual('wlo0000000001', wlo_numbers.__next__())

    def test_next(self):
        last_wlo = 'wlo0000000100'
        wlo_numbers = wlo_pool(last_wlo, 1)
        self.assertEqual('wlo0000000101', wlo_numbers.__next__())

    def test_5_new_wlo_needed(self):
        last_wlo = 'wlo1000000007'
        expected = [
            'wlo1000000008',
            'wlo1000000009',
            'wlo1000000010',
            'wlo1000000011',
            'wlo1000000012']
        wlo_numbers = wlo_pool(last_wlo, 5)
        received = []
        for w in wlo_numbers:
            received.append(w)

        self.assertEqual(expected, received)

    def test_more_than_10_digits(self):
        last_wlo = 'wlo9999999999'
        with self.assertRaises(RuntimeError):
            wlo_pool(last_wlo, 1).__next__()


    def test_illigal_lenght_last_wlo(self):
        last_wlo = 'wlo001'
        wlo_numbers = wlo_pool(last_wlo, 1)
        with self.assertRaises(ValueError):
            wlo_numbers.__next__()

    def test_illigal_value_last_wlo(self):
        last_wlo = 'wloe000000001'
        wlo_numbers = wlo_pool(last_wlo, 1)
        with self.assertRaises(ValueError):
            wlo_numbers.__next__()




if __name__ == '__main__':
    unittest.main()