import pathclass
import unittest

class Tests(unittest.TestCase):
    def test_something(self):
        self.assertEqual('C:\\Users', pathclass.get_path_casing('C:\\users'))
        self.assertEqual('C:\\Users\\Nonexist', pathclass.get_path_casing('C:\\users\\Nonexist'))

if __name__ == '__main__':
    unittest.main()
