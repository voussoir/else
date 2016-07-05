




import datetime
import os
import PIL.Image
import random
import sqlite3
import string
import warnings

ID_LENGTH = 22
VALID_TAG_CHARS = string.ascii_lowercase + string.digits + '_-'
MAX_TAG_NAME_LENGTH = 32

SQL_LASTID_COLUMNS = [
    'table',
    'last_id',
]

SQL_PHOTO_COLUMNS = [
    'id',
    'filepath',
    'extension',
    'width',
    'height',
    'ratio',
    'area',
    'bytes',
    'created',
]

SQL_PHOTOTAG_COLUMNS = [
    'photoid',
    'tagid',
]

SQL_SYN_COLUMNS = [
    'name',
    'master',
]

SQL_TAG_COLUMNS = [
    'id',
    'name',
]

SQL_LASTID = {key:index for (index, key) in enumerate(SQL_LASTID_COLUMNS)}
SQL_PHOTO = {key:index for (index, key) in enumerate(SQL_PHOTO_COLUMNS)}
SQL_PHOTOTAG = {key:index for (index, key) in enumerate(SQL_PHOTOTAG_COLUMNS)}
SQL_SYN = {key:index for (index, key) in enumerate(SQL_SYN_COLUMNS)}
SQL_TAG = {key:index for (index, key) in enumerate(SQL_TAG_COLUMNS)}


DB_INIT = '''
CREATE TABLE IF NOT EXISTS photos(
    id TEXT,
    filepath TEXT,
    extension TEXT,
    width INT,
    height INT,
    ratio REAL,
    area INT,
    bytes INT,
    created INT
    );
CREATE TABLE IF NOT EXISTS tags(
    id TEXT,
    name TEXT
    );
CREATE TABLE IF NOT EXISTS albums(
    albumid TEXT,
    photoid TEXT
    );
CREATE TABLE IF NOT EXISTS photo_tag_rel(
    photoid TEXT,
    tagid TEXT
    );
CREATE TABLE IF NOT EXISTS tag_synonyms(
    name TEXT,
    mastername TEXT
    );
CREATE TABLE IF NOT EXISTS id_numbers(
    tab TEXT,
    last_id TEXT
    );
CREATE INDEX IF NOT EXISTS index_photo_id on photos(id);
CREATE INDEX IF NOT EXISTS index_photo_path on photos(filepath);
CREATE INDEX IF NOT EXISTS index_photo_created on photos(created);

CREATE INDEX IF NOT EXISTS index_tag_id on tags(id);
CREATE INDEX IF NOT EXISTS index_tag_name on tags(name);

CREATE INDEX IF NOT EXISTS index_tagrel_photoid on photo_tag_rel(photoid);
CREATE INDEX IF NOT EXISTS index_tagrel_tagid on photo_tag_rel(tagid);

CREATE INDEX IF NOT EXISTS index_tagsyn_name on tag_synonyms(name);
'''

def basex(number, base, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    '''
    Converts an integer to a different base string.
    Based on http://stackoverflow.com/a/1181922/5430534
    '''
    if base > len(alphabet):
        raise Exception('alphabet %s does not support base %d' % (
                         repr(alphabet), base))
    alphabet = alphabet[:base]
    if not isinstance(number, (int, str)):
        raise TypeError('number must be an integer')
    number = int(number)
    based = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        based = alphabet[i] + based
    return sign + based

def fetch_generator(cursor):
    while True:
        fetch = cursor.fetchone()
        if fetch is None:
            break
        yield fetch

def getnow(timestamp=True):
    '''
    Return the current UTC timestamp or datetime object.
    '''
    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp:
        return now.timestamp()
    return now

def is_xor(*args):
    '''
    Return True if and only if one arg is truthy.
    '''
    return [bool(a) for a in args].count(True) == 1

def min_max_query_builder(name, comparator, value):
    return ' '.join([name, comparator, value])

def normalize_tagname(tagname):
    '''
    Tag names can only consist of lowercase letters, underscores,
    and hyphens. The given tagname is lowercased, gets its spaces
    replaced by underscores, and is stripped of any not-whitelisted
    characters.
    '''
    tagname = tagname.lower()
    tagname = tagname.replace(' ', '_')
    tagname = (c for c in tagname if c in VALID_TAG_CHARS)
    tagname = ''.join(tagname)
    if len(tagname) == 0:
        raise TagTooShort(tagname)
    if len(tagname) > MAX_TAG_NAME_LENGTH:
        raise TagTooLong(tagname)
    return tagname

def not_implemented(function):
    '''
    Decorator for keeping track of which functions still need to be filled out.
    '''
    warnings.warn('%s is not implemented' % function.__name__)
    return function

def raise_nosuchtag(tagid=None, tagname=None, comment=''):
    if tagid is not None:
        message = 'ID: %s. %s' % (tagid, comment)
    elif tagname is not None:
        message = 'Name: %s. %s' % (tagname, comment)
    raise NoSuchTag(message)

class NoSuchPhoto(Exception):
    pass

class NoSuchSynonym(Exception):
    pass

class NoSuchTag(Exception):
    pass

class PhotoExists(Exception):
    pass

class TagExists(Exception):
    pass

class TagTooLong(Exception):
    pass

class TagTooShort(Exception):
    pass

class XORException(Exception):
    pass

class PhotoDB:
    '''
    This class represents an SQLite3 database containing the following tables:

    photos: 
        Rows represent image files on the local disk.
        Entries contain a unique ID, the image's filepath, and metadata
        like dimensions and filesize.

    tags:
        Rows represent labels, which can be applied to an arbitrary number of
        photos. Photos may be selected by which tags they contain.
        Entries contain a unique ID and a name.

    albums:
        Rows represent the inclusion of a photo in an album

    photo_tag_rel:
        Rows represent a Photo's ownership of a particular Tag.

    tag_synonyms:
        Rows represent relationships between two tag names, so that they both
        resolve to the same Tag object when selected. Entries contain the
        subordinate name and master name.
        The master name MUST also exist in the `tags` table.
        If a new synonym is created referring to another synoym, the master name
        will be resolved and used instead, so a synonym is never in the master
        column.
        Tag objects will ALWAYS represent the master tag.

        Note that the entries in this table do not contain ID numbers.
        The rationale here is that "coco" is a synonym for "chocolate" regardless
        of the "chocolate" tag's ID, and that if a tag is renamed, its synonyms
        do not necessarily follow.
        The `rename_tag` method includes a parameter `apply_to_synonyms` if you do
        want them to follow.
    '''
    def __init__(self, databasename='phototagger.db', id_length=None):
        if id_length is None:
            self.id_length = ID_LENGTH
        self.databasename = databasename
        self.sql = sqlite3.connect(databasename)
        self.cur = self.sql.cursor()
        statements = DB_INIT.split(';')
        for statement in statements:
            self.cur.execute(statement)
        self._last_ids = {}

    def __repr__(self):
        return 'PhotoDB(databasename={dbname})'.format(dbname=repr(self.databasename))

    def apply_photo_tag(self, photoid, tagid=None, tagname=None, commit=True):
        '''
        Apply a tag to a photo. `tag` may be the name of the tag or a Tag
        object from the same PhotoDB.

        `tag` may NOT be the tag's ID, since we can't tell if a given string is
        an ID or a name.

        Returns True if the tag was applied, False if the photo already had this tag.
        Raises NoSuchTag and NoSuchPhoto as appropriate.
        '''
        tag = self.get_tag(tagid=tagid, tagname=tagname, resolve_synonyms=True)

        self.cur.execute('SELECT * FROM photo_tag_rel WHERE photoid == ? AND tagid == ?', [photoid, tag.id])
        if self.cur.fetchone() is not None:
            return False

        self.cur.execute('INSERT INTO photo_tag_rel VALUES(?, ?)', [photoid, tag.id])
        if commit:
            self.sql.commit()
        return True

    def convert_tag_to_synonym(self, oldtagname, mastertagname):
        '''
        Convert an independent tag into a synonym for a different independent tag.
        All photos which possess the current tag will have it replaced
        with the master tag. All synonyms of the old tag will point to the new tag.

        Good for when two tags need to be merged under a single name.
        '''
        oldtagname = normalize_tagname(oldtagname)
        mastertagname = normalize_tagname(mastertagname)

        oldtag = self.get_tag_by_name(oldtagname, resolve_synonyms=False)
        if oldtag is None:
            raise NoSuchTag(oldtagname)

        mastertag = self.get_tag_by_name(mastertagname, resolve_synonyms=False)
        if mastertag is None:
            raise NoSuchTag(mastertagname)

        # Migrate the old tag's synonyms to the new one
        # UPDATE is safe for this operation because there is no chance of duplicates.
        self.cur.execute('UPDATE tag_synonyms SET mastername = ? WHERE mastername == ?', [mastertagname, oldtagname])

        # Iterate over all photos with the old tag, and relate them to the new tag
        # if they aren't already.
        temp_cur = self.sql.cursor()
        temp_cur.execute('SELECT * FROM photo_tag_rel WHERE tagid == ?', [oldtag.id])
        for relationship in fetch_generator(temp_cur):
            photoid = relationship[SQL_PHOTOTAG['photoid']]
            self.cur.execute('SELECT * FROM photo_tag_rel WHERE tagid == ?', [mastertag.id])
            if self.cur.fetchone() is not None:
                continue
            self.cur.execute('INSERT INTO photo_tag_rel VALUES(?, ?)', [photoid, mastertag.id])

        # Then delete the relationships with the old tag
        self.cur.execute('DELETE FROM photo_tag_rel WHERE tagid == ?', [oldtag.id])
        self.cur.execute('DELETE FROM tags WHERE id == ?', [oldtag.id])
        
        # Enjoy your new life as a monk.
        self.new_tag_synonym(oldtag.name, mastertag.name, commit=False)
        self.sql.commit()

    def delete_photo(self, photoid):
        '''
        Delete a photo and its relation to any tags and albums.
        '''
        photo = self.get_photo_by_id(photoid)
        if photo is None:
            raise NoSuchPhoto(photoid)
        self.cur.execute('DELETE FROM photos WHERE id == ?', [photoid])
        self.cur.execute('DELETE FROM photo_tag_rel WHERE photoid == ?', [photoid])
        self.sql.commit()

    def delete_tag(self, tagid=None, tagname=None):
        '''
        Delete a tag, its synonyms, and its relation to any photos.
        '''

        tag = self.get_tag(tagid=tagid, tagname=tagname, resolve_synonyms=False)

        if tag is None:
            message = 'Is it a synonym?'
            raise_nosuchtag(tagid=tagid, tagname=tagname, comment=message)

        self.cur.execute('DELETE FROM tags WHERE id == ?', [tag.id])
        self.cur.execute('DELETE FROM photo_tag_rel WHERE tagid == ?', [tag.id])
        self.cur.execute('DELETE FROM tag_synonyms WHERE mastername == ?', [tag.name])
        self.sql.commit()

    def delete_tag_synonym(self, tagname):
        '''
        Delete a tag synonym.
        This will have no effect on photos or other synonyms because
        they always resolve to the master tag before application.
        '''
        tagname = normalize_tagname(tagname)
        self.cur.execute('SELECT * FROM tag_synonyms WHERE name == ?', [tagname])
        fetch = self.cur.fetchone()
        if fetch is None:
            raise NoSuchSynonym(tagname)

        self.cur.execute('DELETE FROM tag_synonyms WHERE name == ?', [tagname])
        self.sql.commit()

    def generate_id(self, table):
        '''
        Create a new ID number that is unique to the given table.
        Note that this method does not commit the database. We'll wait for that
        to happen in whoever is calling us, so we know the ID is actually used.
        '''
        table = table.lower()
        if table not in ['photos', 'tags']:
            raise ValueError('Invalid table requested: %s.', table)

        do_update = False
        if table in self._last_ids:
            # Use cache value
            new_id = self._last_ids[table] + 1
            do_update = True
        else:
            self.cur.execute('SELECT * FROM id_numbers WHERE tab == ?', [table])
            fetch = self.cur.fetchone()
            if fetch is None:
                # Register new value
                new_id = 1
            else:
                # Use database value
                new_id = int(fetch[SQL_LASTID['last_id']]) + 1
                do_update = True
                
        new_id_s = str(new_id).rjust(self.id_length, '0')
        if do_update:
            self.cur.execute('UPDATE id_numbers SET last_id = ? WHERE tab == ?', [new_id_s, table])
        else:
            self.cur.execute('INSERT INTO id_numbers VALUES(?, ?)', [table, new_id_s])
        self._last_ids[table] = new_id
        return new_id_s

    @not_implemented
    def get_album_by_id(self, albumid):
        return

    def get_photo_by_id(self, photoid):
        '''
        Return this Photo object, or None if it does not exist.
        '''
        self.cur.execute('SELECT * FROM photos WHERE id == ?', [photoid])
        photo = self.cur.fetchone()
        if photo is None:
            return None
        photo = self.tuple_to_photo(photo)
        return photo

    def get_photo_by_path(self, filepath):
        '''
        Return this Photo object, or None if it does not exist.
        '''
        filepath = os.path.abspath(filepath)
        self.cur.execute('SELECT * FROM photos WHERE filepath == ?', [filepath])
        photo = self.cur.fetchone()
        if photo is None:
            return None
        photo = self.tuple_to_photo(photo)
        return photo

    def get_photos_by_recent(self, count=None):
        '''
        Yield photo objects in order of creation time.
        '''
        if count is not None and count <= 0:
            return
        # We're going to use a second cursor because the first one may
        # get used for something else, deactivating this query.
        temp_cur = self.sql.cursor()
        temp_cur.execute('SELECT * FROM photos ORDER BY created DESC')
        while True:
            f = temp_cur.fetchone()
            if f is None:
                return
            photo = self.tuple_to_photo(f)

            yield photo

            if count is None:
                continue
            count -= 1
            if count <= 0:
                return

    @not_implemented
    def get_photos_by_search(
        self,
        extension=None,
        maximums={},
        minimums={},
        tag_musts=None,
        tag_mays=None,
        tag_forbids=None,
        tag_forbid_unspecified=False,
        ):
        '''
        Given one or multiple tags, yield photos possessing those tags.

        Parameters:
            extension :
                A string or list of strings of acceptable file extensions.

            maximums : 
                A dictionary, where the key is an attribute of the photo,
                (area, bytes, created, height, id, or width)
                and the value is the maximum desired value for that field.

            minimums :
                A dictionary like `maximums` where the value is the minimum
                desired value for that field.

            tag_musts :
                A list of tag names or Tag objects.
                Photos MUST have ALL tags in this list.

            tag_mays :
                A list of tag names or Tag objects.
                If `forbid_unspecified` is True, then Photos MUST have AT LEAST ONE tag in this list.
                If `forbid_unspecified` is False, then Photos MAY or MAY NOT have ANY tag in this list.

            tag_forbids :
                A list of tag names or Tag objects.
                Photos MUST NOT have ANY tag in the list.

            tag_forbid_unspecified :
                True or False.
                If False, Photos need only comply with the `tag_musts`.
                If True, Photos need to comply with both `tag_musts` and `tag_mays`.
        '''
        maximums = {key:int(val) for (key, val) in maximums.items()}
        minimums = {key:int(val) for (key, val) in minimums.items()}

        # Raise for cases where the minimum > maximum
        for (maxkey, maxval) in maximums.items():
            if maxkey not in minimums:
                continue
            minval = minimums[maxkey]
            if minval > maxval:
                raise ValueError('Impossible min-max for %s' % maxkey)

        conditions = []
        minmaxers = {'<=': maximums, '>=': minimums}

        # Convert the min-max parameters into query strings
        for (comparator, minmaxer) in minmaxers.items():
            for (field, value) in minmaxer.items():
                if field not in Photo.int_properties:
                    raise ValueError('Unknown Photo property: %s' % field)

                value = str(value)
                query = min_max_query_builder(field, comparator, value)
                conditions.append(query)

        if extension is not None:
            if isinstance(extension, str):
                extension = [extension]

            # Normalize to prevent injections
            extension = [normalize_tagname(e) for e in extension]
            extension = ['extension == "%s"' % e for e in extension]
            extension = ' OR '.join(extension)
            extension = '(%s)' % extension
            conditions.append(extension)

        def setify(l):
            return set(self.get_tag_by_name(t) for t in l) if l else set()
        tag_musts = setify(tag_musts)
        tag_mays = setify(tag_mays)
        tag_forbids = setify(tag_forbids)

        base = '%s EXISTS (SELECT 1 FROM photo_tag_rel WHERE photo_tag_rel.photoid == photos.id AND photo_tag_rel.tagid %s %s)'
        for tag in tag_musts:
            query = base % ('', '==', '"%s"' % tag.id)
            conditions.append(query)

        if tag_forbid_unspecified and len(tag_mays) > 0:
            acceptable = tag_mays.union(tag_musts)
            acceptable = ['"%s"' % t.id for t in acceptable]
            acceptable = ', '.join(acceptable)
            query = base % ('NOT', 'NOT IN', '(%s)' % acceptable)
            conditions.append(query)

        for tag in tag_forbids:
            query = base % ('NOT', '==', '"%s"' % tag.id)
            conditions.append(query)

        if len(conditions) == 0:
            raise ValueError('No search query provided')

        conditions = [query for query in conditions if query is not None]
        conditions = ['(%s)' % c for c in conditions]
        conditions = ' AND '.join(conditions)
        conditions = 'WHERE %s' % conditions


        query = 'SELECT * FROM photos %s' % conditions
        print(query)
        temp_cur = self.sql.cursor()
        temp_cur.execute(query)
        acceptable_tags = tag_musts.union(tag_mays)
        while True:
            fetch = temp_cur.fetchone()
            if fetch is None:
                break

            photo = self.tuple_to_photo(fetch)

            # if any(forbid in photo.tags for forbid in tag_forbids):
            #     print('Forbidden')
            #     continue

            # if tag_forbid_unspecified:
            #     if any(tag not in acceptable_tags for tag in photo.tags):
            #         print('Forbid unspecified')
            #         continue

            # if any(must not in photo.tags for must in tag_musts):
            #     print('No must')
            #     continue

            yield photo


    def get_tag(self, tagid=None, tagname=None, resolve_synonyms=True):
        '''
        Redirect to get_tag_by_id or get_tag_by_name after xor-checking the parameters.
        '''
        if not is_xor(tagid, tagname):
            raise XORException('One and only one of `tagid`, `tagname` can be passed.')

        if tagid is not None:
            return self.get_tag_by_id(tagid)
        elif tagname is not None:
            return self.get_tag_by_name(tagname, resolve_synonyms=resolve_synonyms)
        raise_nosuchtag(tagid=tagid, tagname=tagname)

    def get_tag_by_id(self, tagid):
        self.cur.execute('SELECT * FROM tags WHERE id == ?', [tagid])
        tag = self.cur.fetchone()
        if tag is None:
            return raise_nosuchtag(tagid=tagid)
        tag = self.tuple_to_tag(tag)
        return tag

    def get_tag_by_name(self, tagname, resolve_synonyms=True):
        if isinstance(tagname, Tag):
            return tagname

        tagname = normalize_tagname(tagname)

        if resolve_synonyms is True:
            self.cur.execute('SELECT * FROM tag_synonyms WHERE name == ?', [tagname])
            fetch = self.cur.fetchone()
            if fetch is not None:
                mastertagname = fetch[SQL_SYN['master']]
                tag = self.get_tag_by_name(mastertagname)
                return tag

        self.cur.execute('SELECT * FROM tags WHERE name == ?', [tagname])
        fetch = self.cur.fetchone()
        if fetch is None:
            raise_nosuchtag(tagname=tagname)

        tag = self.tuple_to_tag(fetch)
        return tag
        
    def get_tags_by_photo(self, photoid):
        '''
        Return the tags assigned to the given photo.
        '''
        temp_cur = self.sql.cursor()
        temp_cur.execute('SELECT * FROM photo_tag_rel WHERE photoid == ?', [photoid])
        tags = fetch_generator(temp_cur)
        tagobjects = set()
        for tag in tags:
            tagid = tag[SQL_PHOTOTAG['tagid']]
            tagobj = self.get_tag_by_id(tagid)
            tagobjects.add(tagobj)
        return tagobjects

    def new_photo(self, filename, tags=None, allow_duplicates=False):
        '''
        Given a filepath, determine its attributes and create a new Photo object in the
        database. Tags may be applied now or later.

        If `allow_duplicates` is False, we will first check the database for any files
        with the same path and raise PhotoExists if found.

        Returns the Photo object.
        '''
        filename = os.path.abspath(filename)
        if not allow_duplicates:
            existing = self.get_photo_by_path(filename)
            if existing is not None:
                raise PhotoExists(filename, existing)

        # I want the caller to receive any exceptions this raises.
        image = PIL.Image.open(filename)

        extension = os.path.splitext(filename)[1]
        extension = extension.replace('.', '')
        extension = normalize_tagname(extension)
        (width, height) = image.size
        area = width * height
        ratio = width / height
        bytes = os.path.getsize(filename)
        created = int(getnow())
        photoid = self.generate_id('photos')

        data = [None] * len(SQL_PHOTO_COLUMNS)
        data[SQL_PHOTO['id']] = photoid
        data[SQL_PHOTO['filepath']] = filename
        data[SQL_PHOTO['extension']] = extension
        data[SQL_PHOTO['width']] = width
        data[SQL_PHOTO['height']] = height
        data[SQL_PHOTO['area']] = area
        data[SQL_PHOTO['ratio']] = ratio
        data[SQL_PHOTO['bytes']] = bytes
        data[SQL_PHOTO['created']] = created
        photo = self.tuple_to_photo(data)

        self.cur.execute('INSERT INTO photos VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)', data)

        tags = tags or []
        for tag in tags:
            try:
                self.apply_photo_tag(photoid, tagname=tag, commit=False)
            except NoSuchTag:
                self.sql.rollback()
                raise
        self.sql.commit()
        image.close()
        return photo

    def new_tag(self, tagname):
        '''
        Register a new tag in the database and return the Tag object.
        '''
        tagname = normalize_tagname(tagname)
        try:
            self.get_tag_by_name(tagname)
            TagExists(tagname)
        except NoSuchTag:
            pass
        tagid = self.generate_id('tags')
        self.cur.execute('INSERT INTO tags VALUES(?, ?)', [tagid, tagname])
        self.sql.commit()
        tag = self.tuple_to_tag([tagid, tagname])
        return tag

    def new_tag_synonym(self, tagname, mastertagname, commit=True):
        '''
        Register a new synonym for an existing tag.
        '''
        tagname = normalize_tagname(tagname)
        mastertagname = normalize_tagname(mastertagname)

        if tagname == mastertagname:
            raise ValueError('Cannot assign synonym to itself.')

        # We leave resolve_synonyms as True, so that if this function returns
        # anything, we know the given tagname is already a synonym or master.
        tag = self.get_tag_by_name(tagname, resolve_synonyms=True)
        if tag is not None:
            raise TagExists(tagname)

        mastertag = self.get_tag_by_name(mastertagname, resolve_synonyms=True)
        if mastertag is None:
            raise NoSuchTag(mastertagname)

        self.cur.execute('INSERT INTO tag_synonyms VALUES(?, ?)', [tagname, mastertag.name])

        if commit:
            self.sql.commit()

        return mastertag

    def photo_has_tag(self, photoid, tagid=None, tagname=None):
        tag = self.get_tag(tagid=tagid, tagname=tagname, resolve_synonyms=True)
        if tag is None:
            raise_nosuchtag(tagid=tagid, tagname=tagname)

        exe = self.cur.execute
        exe('SELECT * FROM photo_tag_rel WHERE photoid == ? AND tagid == ?', [photoid, tag.id])
        fetch = self.cur.fetchone()
        has_tag = fetch is not None
        return has_tag

    @not_implemented
    def rename_tag(self, tagname, newname, apply_to_synonyms):
        pass

    def tuple_to_photo(self, tu):
        '''
        Given a tuple like the ones from an sqlite query,
        create a Photo object.
        '''
        photoid = tu[SQL_PHOTO['id']]
        tags = self.get_tags_by_photo(photoid)

        photo = Photo(
            photodb = self,
            photoid = photoid,
            filepath = tu[SQL_PHOTO['filepath']],
            extension = tu[SQL_PHOTO['extension']],
            width = tu[SQL_PHOTO['width']],
            height = tu[SQL_PHOTO['height']],
            created = tu[SQL_PHOTO['created']],
            bytes = tu[SQL_PHOTO['bytes']],
            tags = tags,
            )
        return photo

    def tuple_to_tag(self, tu):
        '''
        Given a tuple like the ones from an sqlite query,
        create a Tag object.
        '''
        tag = Tag(
            photodb = self,
            tagid = tu[SQL_TAG['id']],
            name = tu[SQL_TAG['name']]
            )
        return tag

class Photo:
    '''
    This class represents a PhotoDB entry containing information about an image file.
    Photo objects cannot exist without a corresponding PhotoDB object, because
    Photos are not the actual files, just the database entry. 
    '''
    int_properties = set(['area', 'bytes', 'created', 'height', 'id', 'width'])
    def __init__(
        self,
        photodb,
        photoid,
        filepath,
        extension,
        width,
        height,
        bytes,
        created,
        tags=None,
        ):
        if tags is None:
            tags = []

        self.photodb = photodb
        self.id = photoid
        self.filepath = filepath
        self.extension = extension
        self.width = int(width)
        self.height = int(height)
        self.ratio = self.width / self.height
        self.area = self.width * self.height
        self.bytes = int(bytes)
        self.created = int(created)
        self.tags = tags

    def __eq__(self, other):
        if not isinstance(other, Photo):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        r = ('Photo(photodb={photodb}, ',
            'photoid={photoid}, ',
            'filepath={filepath}, ',
            'extension={extension}, ',
            'width={width}, ',
            'height={height}, ',
            'created={created})'
            )
        r = ''.join(r)
        r = r.format(
            photodb = repr(self.photodb),
            photoid = repr(self.id),
            filepath = repr(self.filepath),
            extension = repr(self.extension),
            width = repr(self.width),
            height = repr(self.height),
            bytes = repr(self.bytes),
            area = repr(self.area),
            created = repr(self.created),
            )
        return r

    def __str__(self):
        return 'Photo: %s' % self.id

    def apply_photo_tag(self, tagname):
        return self.photodb.apply_photo_tag(self.id, tagname=tagname, commit=True)

    def photo_has_tag(self, tagname):
        return self.photodb.photo_has_tag(self.id, tagname=tagname)

class Tag:
    '''
    This class represents a Tag, which can be applied to Photos for
    organization.
    '''
    def __init__(self, photodb, tagid, name):
        self.photodb = photodb
        self.id = tagid
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, Tag):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        r = 'Tag(photodb={photodb}, name={name}, tagid={tagid})'
        r = r.format(
            photodb = repr(self.photodb),
            name = repr(self.name),
            tagid = repr(self.id),
            )
        return r

    def __str__(self):
        return 'Tag: %s : %s' % (self.id, self.name)

if __name__ == '__main__':
    p = PhotoDB()