import os
import phototagger
import unittest

DB_NAME = ':memory:'

class PhotoDBTest(unittest.TestCase):
    def setUp(self):
        self.p = phototagger.PhotoDB(DB_NAME)

    def tearDown(self):
        pass

    def test_add_and_remove_photo(self):
        photo1 = self.p.new_photo('samples\\train.jpg')
        self.assertEqual(len(photo1.id), self.p.id_length)

        photo2 = self.p.get_photo_by_id(photo1.id)
        self.assertEqual(photo1, photo2)

        self.p.remove_photo(photo1.id)

        photo3 = self.p.get_photo_by_id(photo1.id)
        self.assertIsNone(photo3)

    def test_add_and_remove_tag(self):
        tag1 = self.p.new_tag('trains')
        self.assertEqual(tag1.name, 'trains')
        self.assertEqual(len(tag1.id), self.p.id_length)

        tag2 = self.p.get_tag_by_id(tag1.id)
        self.assertEqual(tag1, tag2)

        self.p.remove_tag(tagid=tag1.id)

        tag3 = self.p.get_tag_by_id(tag1.id)
        self.assertIsNone(tag3)

        # Normalization
        tag = self.p.new_tag('one two!')
        self.assertEqual(tag.name, 'one_two')

    def test_add_and_remove_synonym(self):
        # Add synonym
        giraffe = self.p.new_tag('giraffe')
        horse = self.p.new_tag_synonym('long horse', 'giraffe')
        tag = self.p.get_tag_by_name('long horse', resolve_synonyms=True)
        self.assertEqual(tag, giraffe)

        # Synonym of synonym should resolve to master
        snake = self.p.new_tag_synonym('snake with legs', 'long horse')
        tag = self.p.get_tag_by_name('snake with legs')
        self.assertEqual(tag, giraffe)

        # Remove Tag
        self.p.remove_tag_synonym('long horse')
        horse = self.p.get_tag_by_name('long horse')
        self.assertIsNone(horse)

        # Exceptions
        self.assertRaises(phototagger.NoSuchTag, self.p.new_tag_synonym, 'blanc', 'white')
        self.assertRaises(phototagger.NoSuchSynonym, self.p.remove_tag_synonym, 'blanc')

    def test_apply_photo_tag(self):
        photo = self.p.new_photo('samples\\train.jpg')
        self.p.new_tag('vehicles')

        # Should only return True if it is a new tag.
        status = self.p.apply_photo_tag(photo.id, tagname='vehicles')
        self.assertTrue(status)

        status = self.p.apply_photo_tag(photo.id, tagname='vehicles')
        self.assertFalse(status)

    def test_convert_tag_synonym(self):
        # Install tags and a synonym
        photo = self.p.new_photo('samples\\train.jpg')
        trains = self.p.new_tag('trains')
        locomotives = self.p.new_tag('locomotives')
        choochoos = self.p.new_tag_synonym('choochoos', 'locomotives')

        # The first two, as independents, return True.
        self.assertTrue(self.p.apply_photo_tag(photo.id, trains.id))
        self.assertTrue(self.p.apply_photo_tag(photo.id, locomotives.id))
        self.assertFalse(self.p.apply_photo_tag(photo.id, tagname='choochoos'))

        # Pre-conversion, they should be independent.
        trains = self.p.get_tag_by_name('trains', resolve_synonyms=False)
        locomotives = self.p.get_tag_by_name('locomotives', resolve_synonyms=False)
        self.assertNotEqual(trains, locomotives)
        trains_id = trains.id

        # Convert and make sure the second is no longer independent.
        self.p.convert_tag_to_synonym(oldtagname='locomotives', mastertagname='trains')
        trains = self.p.get_tag_by_name('trains', resolve_synonyms=False)
        locomotives = self.p.get_tag_by_name('locomotives', resolve_synonyms=False)
        self.assertIsNone(locomotives)
        self.assertEqual(trains.id, trains_id)

        # The old tag should still pass has_tag as a synonym.
        # The synonym of the old tag should have been remapped to the master.
        self.assertTrue(self.p.photo_has_tag(photo.id, tagname='trains'))
        self.assertTrue(self.p.photo_has_tag(photo.id, tagname='locomotives'))
        self.assertTrue(self.p.photo_has_tag(photo.id, tagname='choochoos'))

        # Synonym should not be included in the photo's tag list.
        tags = list(self.p.get_tags_by_photo(photo.id))
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].id, trains_id)

    def test_generate_id(self):
        i_photo = self.p.generate_id('photos')
        i_tag = self.p.generate_id('tags')
        self.assertRaises(ValueError, self.p.generate_id, 'other')

        self.assertEqual(len(i_photo), self.p.id_length)
        self.assertEqual(len(i_tag), self.p.id_length)

        self.assertEqual(int(i_photo), int(i_tag))
        self.assertLess(int(i_photo), int(self.p.generate_id('photos')))

    def test_get_photo_by_id(self):
        photo = self.p.new_photo('samples\\train.jpg')

        photo2 = self.p.get_photo_by_id(photo.id)
        self.assertEqual(photo, photo2)

    def test_get_photo_by_path(self):
        photo = self.p.new_photo('samples\\train.jpg')

        photo2 = self.p.get_photo_by_path(photo.filepath)
        self.assertEqual(photo, photo2)

    def test_get_photos_by_recent(self):
        paths = ['train.jpg', 'bolts.jpg', 'reddit.png']
        paths = ['samples\\' + path for path in paths]
        paths = [os.path.abspath(path) for path in paths]
        for path in paths:
            self.p.new_photo(path)

        photos = list(self.p.get_photos_by_recent())
        paths.reverse()
        for (index, photo) in enumerate(photos):
            self.assertEqual(photo.filepath, paths[index])

        photos = list(self.p.get_photos_by_recent(count=2))
        self.assertEqual(len(photos), 2)

    def test_get_photos_by_search(self):
        print('NOT IMPLEMENTED')

    def test_get_tag_by_id(self):
        tag1 = self.p.new_tag('test by id')
        tag2 = self.p.get_tag_by_id(tag1.id)
        self.assertEqual(tag1, tag2)

        tag2 = self.p.get_tag(tagid=tag1.id)
        self.assertEqual(tag1, tag2)

    def test_get_tag_by_name(self):
        tag1 = self.p.new_tag('test by name')
        tag2 = self.p.get_tag_by_name(tag1.name)
        self.assertEqual(tag1, tag2)

        tag2 = self.p.get_tag(tagname=tag1.name)
        self.assertEqual(tag1, tag2)

    def test_get_tags_by_photo(self):
        photo = self.p.new_photo('samples\\train.jpg')
        tag = self.p.new_tag('vehicles')
        stat = self.p.apply_photo_tag(photo.id, tagname='vehicles')

        tags = self.p.get_tags_by_photo(photo.id)
        self.assertEqual(tags[0].name, 'vehicles')

    def test_new_tag_lengths(self):
        t = 'x' * (phototagger.MAX_TAG_NAME_LENGTH)
        self.p.new_tag(t)
        self.assertRaises(phototagger.TagTooLong, self.p.new_tag, t+'x')
        self.assertRaises(phototagger.TagTooShort, self.p.new_tag, '')
        self.assertRaises(phototagger.TagTooShort, self.p.new_tag, '!!??&&*')

    def test_photo_has_tag(self):
        photo = self.p.new_photo('samples\\train.jpg')
        tag = self.p.new_tag('vehicles')
        self.p.apply_photo_tag(photo.id, tag.id)

        self.p.photo_has_tag(photo.id, tag.id)

    def test_rename_tag(self):
        print('NOT IMPLEMENTED')

if __name__ == '__main__':
    unittest.main()