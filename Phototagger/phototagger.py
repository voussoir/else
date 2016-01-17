import datetime
import os
import PIL.Image
import random
import sqlite3
import string
import warnings

# UIDs consist of hex characters, so keyspace is 16 ** UID_CHARACTERS.
UID_CHARACTERS = 16
VALID_TAG_CHARS = string.ascii_lowercase + string.digits + '_-'
MAX_TAG_NAME_LENGTH = 32

SQL_PHOTO_COLUMNCOUNT = 8
SQL_PHOTO_ID = 0
SQL_PHOTO_FILEPATH = 1
SQL_PHOTO_EXTENSION = 2
SQL_PHOTO_WIDTH = 3
SQL_PHOTO_HEIGHT = 4
SQL_PHOTO_AREA = 5
SQL_PHOTO_BYTES = 6
SQL_PHOTO_CREATED = 7

SQL_PHOTOTAG_COLUMNCOUNT = 2
SQL_PHOTOTAG_PHOTOID = 0
SQL_PHOTOTAG_TAGID = 1

SQL_SYN_COLUMNCOUNT = 2
SQL_SYN_NAME = 0
SQL_SYN_MASTER = 1

SQL_TAG_COLUMNCOUNT = 2
SQL_TAG_ID = 0
SQL_TAG_NAME = 1

DB_INIT = '''
CREATE TABLE IF NOT EXISTS photos(
    id TEXT,
    filepath TEXT,
    extension TEXT,
    width INT,
    height INT,
    area INT,
    bytes INT,
    created INT
    );
CREATE TABLE IF NOT EXISTS tags(
    id TEXT,
    name TEXT
    );
CREATE TABLE IF NOT EXISTS photo_tag_rel(
    photoid TEXT,
    tagid TEXT
    );
CREATE TABLE IF NOT EXISTS tag_synonyms(
    name TEXT,
    mastername TEXT
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

def getnow(timestamp=True):
    '''
    Return the current UTC timestamp or datetime object.
    '''
    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp:
        return now.timestamp()
    return now

def is_xor(x, y):
    '''
    Return True if and only if one of (x, y) is truthy.
    '''
    same = (bool(x) == bool(y))
    return not same

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
        raise ValueError('Normalized tagname of length 0.')
    return tagname

def not_implemented(function):
    '''
    Great for keeping track of which functions still need to be filled out.
    '''
    warnings.warn('%s is not implemented' % function.__name__)
    return function

def uid(length=None):
    '''
    Generate a u-random hex string..
    '''
    if length is None:
        length = UID_CHARACTERS
    identifier = ''.join('{:02x}'.format(x) for x in os.urandom(math.ceil(length / 2)))
    if len(identifier) > length:
        identifier = identifier[:length]
    return identifier


class NoSuchPhoto(Exception):
    pass

class NoSuchTag(Exception):
    pass

class PhotoExists(Exception):
    pass

class TagExists(Exception):
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
        of the "chocolate" tag's ID, or the fact that you decided to rename your
        "chocolate" tag to "candy" after applying it to a few photos.
        The `rename_tag` method includes a parameter `apply_to_synonyms` if you do
        want them to follow.
    '''
    def __init__(self, databasename='phototagger.db'):
        self.databasename = databasename
        self.sql = sqlite3.connect(databasename)
        self.cur = self.sql.cursor()
        statements = DB_INIT.split(';')
        for statement in statements:
            self.cur.execute(statement)

    def __repr__(self):
        return 'PhotoDB(databasename={dbname})'.format(dbname=repr(self.databasename))

    def add_photo_tag(self, photoid, tag=None, commit=True):
        '''
        Apply a tag to a photo. `tag` may be the name of the tag or a Tag
        object from the same PhotoDB.

        `tag` may NOT be the tag's ID, since an ID would also have been a valid name.
        '''
        if isinstance(tag, Tag) and tag.photodb is self:
            tagid = tag.id
        else:
            tag = self.get_tag_by_name(tag)
            if tag is None:
                raise NoSuchTag(tag)
            tagid = tag.id

        self.cur.execute('SELECT * FROM photos WHERE id == ?', [photoid])
        if self.cur.fetchone() is None:
            raise NoSuchPhoto(photoid)

        self.cur.execute('SELECT * FROM photo_tag_rel WHERE photoid == ? AND tagid == ?', [photoid, tagid])
        if self.cur.fetchone() is not None:
            warning = 'Photo {photoid} already has tag {tagid}'.format(photoid=photoid, tagid=tagid)
            warnings.warn(warning)
            return

        self.cur.execute('INSERT INTO photo_tag_rel VALUES(?, ?)', [photoid, tagid])
        if commit:
            self.sql.commit()

    @not_implemented
    def convert_tag_to_synonym(self, tagname, mastertag):
        '''
        Convert an independent tag into a synonym for a different tag.
        All photos which possess the current tag will have it replaced
        with the master tag.
        '''
        photos = self.get_photos_by_tag(musts=[tagname])

    def get_photo_by_id(self, photoid):
        '''
        Return this Photo object, or None if it does not exist.
        '''
        self.cur.execute('SELECT * FROM photos WHERE id == ?', [photoid])
        photo = cur.fetchone()
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

    def get_photos_by_recent(self):
        '''
        Yield photo objects in order of creation time.
        '''
        # We're going to use a second cursor because the first one may
        # get used for something else, deactivating this query.
        cur2 = self.sql.cursor()
        cur2.execute('SELECT * FROM photos ORDER BY created DESC')
        while True:
            f = cur2.fetchone()
            if f is None:
                return
            photo = self.tuple_to_photo(f)
            yield photo

    @not_implemented
    def get_photos_by_tag(
        self,
        musts=None,
        mays=None,
        forbids=None,
        forbid_unspecified=False,
        ):
        '''
        Given one or multiple tags, yield photos possessing those tags.

        Parameters:
            musts :
                A list of strings or Tag objects.
                Photos MUST have ALL tags in this list.
            mays :
                A list of strings or Tag objects.
                If `forbid_unspecified` is True, then Photos MUST have AT LEAST ONE tag in this list.
                If `forbid_unspecified` is False, then Photos MAY or MAY NOT have ANY tag in this list.
            forbids :
                A list of strings or Tag objects.
                Photos MUST NOT have ANY tag in the list.
            forbid_unspecified :
                True or False.
                If False, Photos need only comply with the `musts`.
                If True, Photos need to comply with both `musts` and `mays`.
        '''
        if all(arg is None for arg in (musts, mays, forbids)):
            raise TypeError('All arguments cannot be None')

    def get_tag_by_id(self, tagid):
        self.cur.execute('SELECT * FROM tags WHERE id == ?', [tagid])
        tag = self.cur.fetchone()
        if tag is None:
            return None
        tag = self.tuple_to_tag(tag)
        return tag

    def get_tag_by_name(self, tagname):
        '''
        Return the Tag object that the given tagname resolves to.

        If the given tagname is a synonym, the master tag will be returned.
        '''
        if isinstance(tagname, Tag):
            return tagname

        self.cur.execute('SELECT * FROM tag_synonyms WHERE name == ?', [tagname])
        fetch = self.cur.fetchone()
        if fetch is not None:
            mastertagid = fetch[SQL_SYN_MASTER]
            tag = self.get_tag_by_id(mastertagid)
            return tag

        self.cur.execute('SELECT * FROM tags WHERE name == ?', [tagname])
        fetch = self.cur.fetchone()
        if fetch is None:
            return None

        tag = self.tuple_to_tag(fetch)
        return tag
        
    def get_tags_by_photo(self, photoid):
        '''
        Return the tags assigned to the given photo.
        '''
        self.cur.execute('SELECT * FROM photo_tag_rel WHERE photoid == ?', [photoid])
        tags = self.cur.fetchall()
        tagobjects = []
        for tag in tags:
            tagid = tag[SQL_PHOTOTAG_TAGID]
            tagobj = self.get_tag_by_id(tagid)
            if tagobj is None:
                warnings.warn('Photo {photid} contains unkown tagid {tagid}'.format(photoid=photoid, tagid=tagid))
                continue
            tagobjects.append(tagobj)
        return tagobjects

    def new_photo(self, filename, tags=[], allow_duplicates=False):
        '''
        Given a filepath, determine its attributes and create a new Photo object in the
        database. Tags may be applied now or later.

        If `allow_duplicates` is False, we will first check the database for any files
        with the same path and raise PhotoExists if found.
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
        (width, height) = image.size
        area = width * height
        bytes = os.path.getsize(filename)
        created = int(getnow())
        photoid = self.new_uid('photos')
        data = [None] * SQL_PHOTO_COLUMNCOUNT
        data[SQL_PHOTO_ID] = photoid
        data[SQL_PHOTO_FILEPATH] = filename
        data[SQL_PHOTO_EXTENSION] = extension
        data[SQL_PHOTO_WIDTH] = width
        data[SQL_PHOTO_HEIGHT] = height
        data[SQL_PHOTO_AREA] = area
        data[SQL_PHOTO_BYTES] = bytes
        data[SQL_PHOTO_CREATED] = created
        photo = self.tuple_to_photo(data)
        self.cur.execute('INSERT INTO photos VALUES(?, ?, ?, ?, ?, ?, ?, ?)', data)
        for tag in tags:
            try:
                self.add_photo_tag(photoid, tag, commit=False)
            except NoSuchTag:
                self.sql.rollback()
                raise
        self.sql.commit()
        return photo

    def new_tag(self, tagname):
        '''
        Register a new tag.
        '''
        tagname = normalize_tagname(tagname)
        if self.get_tag_by_name(tagname) is not None:
            raise TagExists(tagname)
        tagid = self.new_uid('tags')
        self.cur.execute('INSERT INTO tags VALUES(?, ?)', [tagid, tagname])
        self.sql.commit()
        tag = self.tuple_to_tag([tagid, tagname])
        return tag

    def new_tag_synonym(self, tagname, mastertagname):
        '''
        Register a new synonym for an existing tag.
        '''
        tagname = normalize_tagname(tagname)
        mastertagname = normalize_tagname(mastertagname)

        if tagname == mastertagname:
            raise TagExists(tagname)

        tag = self.get_tag_by_name(tagname)
        if tag is not None:
            raise TagExists(tagname)

        mastertag = self.get_tag_by_name(mastertagname)
        if mastertag is None:
            raise NoSuchTag(mastertagname)
        mastertagname = mastertag.name

        self.cur.execute('INSERT INTO tag_synonyms VALUES(?, ?)', [tagname, mastertagname])
        self.sql.commit()

    def new_uid(self, table):
        '''
        Create a new UID that is unique to the given table.
        '''
        result = None
        # Well at least we won't get sql injection this way.
        table = normalize_tagname(table)
        query = 'SELECT * FROM {table} WHERE id == ?'.format(table=table)
        while result is None:
            i = uid()
            # Just gotta be sure, man.
            self.cur.execute(query, [i])
            if self.cur.fetchone() is None:
                result = i
        return result

    @not_implemented
    def remove_photo(self):
        pass

    @not_implemented
    def remove_tag(self, tagid=None, tagname=None):
        '''
        Delete a tag and its relation to any photos.
        '''
        if not is_xor(tagid, tagname):
            raise XORException('One and only one of `tagid`, `tagname` can be passed.')

        if tagid is not None:
            self.cur.execute('SELECT * FROM tags WHERE id == ?', [tagid])
            tag = self.cur.fetchone()

        elif tagname is not None:
            tagname = normalize_tagname(tagname)
            self.cur.execute('SELECT * from tags WHERE name == ?', [tagname])
            tag = self.cur.fetchone()

        if tag is None:
            raise NoSuchTag(tagid or tagname)

        tag = self.tuple_to_tag(tag)

        self.cur.execute('DELETE FROM tags WHERE id == ?', [tag.id])
        self.cur.execute('DELETE FROM photo_tag_rel WHERE tagid == ?', [tag.id])
        self.cur.execute('DELETE FROM tag_synonyms WHERE mastername == ?', [tag.name])
        self.sql.commit()

    @not_implemented
    def remove_tag_synonym(self, tagname):
        pass

    def tuple_to_photo(self, tu):
        '''
        Given a tuple like the ones from an sqlite query,
        create a Photo object.
        '''
        photoid = tu[SQL_PHOTO_ID]
        tags = self.get_tags_by_photo(photoid)

        photo = Photo(
            photodb = self,
            photoid = photoid,
            filepath = tu[SQL_PHOTO_FILEPATH],
            extension = tu[SQL_PHOTO_EXTENSION],
            width = tu[SQL_PHOTO_WIDTH],
            height = tu[SQL_PHOTO_HEIGHT],
            area = tu[SQL_PHOTO_AREA],
            created = tu[SQL_PHOTO_CREATED],
            bytes = tu[SQL_PHOTO_BYTES],
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
            tagid = tu[SQL_TAG_ID],
            name = tu[SQL_TAG_NAME]
            )
        return tag

class Photo:
    '''
    This class represents a PhotoDB entry containing information about an image file.
    Photo objects cannot exist without a corresponding PhotoDB object, because
    Photos are not the actual files, just the database entry. 
    '''
    def __init__(
        self,
        photodb,
        photoid,
        filepath,
        extension,
        width,
        height,
        area,
        bytes,
        created,
        tags=[],
        ):
        self.photodb = photodb
        self.id = photoid
        self.filepath = filepath
        self.extension = extension
        self.width = width
        self.height = height
        self.area = area
        self.bytes = bytes
        self.created = created
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
            'area={area}, ',
            'bytes={bytes} ',
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

    def add_photo_tag(self, tagname):
        return self.photodb.add_photo_tag(self.id, tagname, commit=True)

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