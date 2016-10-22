import bytestring
import unittest

bytestring_pairs = {
    100: '100.000 b',
    2 ** 10: '1.000 KiB',
    2 ** 20: '1.000 MiB',
    2 ** 30: '1.000 GiB',
    -(2 ** 30): '-1.000 GiB',
    (2 ** 30) + (512 * (2 ** 20)): '1.500 GiB',
}

parsebytes_pairs = {
    '100k': 102400,
    '100 k': 102400,
    '100 kb': 102400,
    '100  kib': 102400,
    '100.00KB': 102400,
    '1.5 mb': 1572864,
    '-1.5 mb': -1572864,
}

unit_string_cases = [
'B', 'b',
'KiB', 'kib', 'KB', 'K', 'k',
'MiB', 'mib', 'MB', 'M', 'm',
'GiB', 'gib', 'GB', 'G', 'g',
'TiB', 'tib', 'TB', 'T', 't',
'PiB', 'pib', 'PB', 'P', 'p',
'EiB', 'eib', 'EB', 'E', 'e',
'ZiB', 'zib', 'ZB', 'Z', 'z',
'YiB', 'yib', 'YB', 'Y', 'y',
]

class BytestringTest(unittest.TestCase):
    def test_bytestring(self):
        for (number, text) in bytestring_pairs.items():
            self.assertEqual(bytestring.bytestring(number), text)
        self.assertEqual(bytestring.bytestring(1024, force_unit=1), '1024.000 b')
        self.assertEqual(bytestring.bytestring(1024, force_unit='b'), '1024.000 b')

    def test_parsebytes(self):
        for (number, text) in bytestring_pairs.items():
            self.assertEqual(bytestring.parsebytes(text), number)
        for (text, number) in parsebytes_pairs.items():
            self.assertEqual(bytestring.parsebytes(text), number)
        self.assertRaises(ValueError, bytestring.parsebytes, 'no numbers')
        self.assertRaises(ValueError, bytestring.parsebytes, '100 and 300')
        self.assertRaises(ValueError, bytestring.parsebytes, 'something300')
        self.assertRaises(ValueError, bytestring.parsebytes, '100 wrongunit')

    def test_normalize_unit_string(self):
        for case in unit_string_cases:
            normalized = bytestring.normalize_unit_string(case)
            self.assertTrue(normalized in bytestring.REVERSED_UNIT_STRINGS)
        self.assertRaises(ValueError, bytestring.normalize_unit_string, 'incorrect')
        self.assertRaises(ValueError, bytestring.normalize_unit_string, 'x')

if __name__ == '__main__':
    unittest.main()
