# -*- coding: utf-8 -*-
import unittest


from context import validators

class TestValue2String(unittest.TestCase):

    def test_int_to_unicode(self):
        value = 2016
        value_as_uni = validators.value2string(value)
        print(type(value_as_uni))


class TestNormalizeDate(unittest.TestCase):
    """Test date parsing"""

    def test_int2string(self):
        # date = validators.normalize_date(2016)
        pass


if __name__ == '__main__':
    unittest.main()
