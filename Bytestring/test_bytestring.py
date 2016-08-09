import bytestring
import unittest

pairs = {
    100: '100.000 b',
    2 ** 10: '1.000 KiB',
    2 ** 20: '1.000 MiB',
    2 ** 30: '1.000 GiB',
    -(2 ** 30): '-1.000 GiB',
    (2 ** 30) + (512 * (2 ** 20)): '1.500 GiB',
}

class BytestringTest(unittest.TestCase):
    def test_bytestring(self):
        for (number, text) in pairs.items():
            self.assertEqual(bytestring.bytestring(number), text)

    def test_parsebytes(self):
        for (number, text) in pairs.items():
            self.assertEqual(bytestring.parsebytes(text), number)
        self.assertEqual(bytestring.parsebytes('100k'), 102400)
        self.assertEqual(bytestring.parsebytes('100 k'), 102400)
        self.assertEqual(bytestring.parsebytes('100 kb'), 102400)
        self.assertEqual(bytestring.parsebytes('100  kib'), 102400)
        self.assertEqual(bytestring.parsebytes('100.00KB'), 102400)
        self.assertEqual(bytestring.parsebytes('1.5 mb'), 1572864)
        self.assertEqual(bytestring.parsebytes('-1.5 mb'), -1572864)

if __name__ == '__main__':
    unittest.main()