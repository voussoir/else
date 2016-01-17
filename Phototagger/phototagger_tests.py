import os
import phototagger
import unittest

DB_NAME = ':memory:'

#try:
#    os.remove(DB_NAME)
#    print('Deleted old database.')
#except FileNotFound:
#    pass

class PhotoDBTest(unittest.TestCase):
    def setUp(self):
        self.p = phototagger.PhotoDB(DB_NAME)

    def tearDown(self):
        pass

    def test_add_and_remove_tag(self):
        tag = self.p.new_tag('trains')
        self.assertEqual(tag.name, 'trains')
        self.assertEqual(len(tag.id), phototagger.UID_CHARACTERS)

        tag2 = self.p.get_tag_by_id(tag.id)
        self.assertEqual(tag, tag2)

        tag3 = self.p.get_tag_by_name(tag.name)
        self.assertEqual(tag, tag3)

        self.assertEqual(tag2, tag3)

        self.p.remove_tag(tagid=tag.id)

        tag4 = self.p.get_tag_by_id(tag.id)
        self.assertIsNone(tag4)

    def test_new_tag_invalid_name(self):
        print('NOT IMPLEMENTED')

    def test_new_tag_too_long(self):
        print('NOT IMPLEMENTED')

if __name__ == '__main__':
    unittest.main()