import datetime
import os
import PIL.Image
import random
import sqlite3
import string
import time
import warnings

ID_LENGTH = 22
VALID_TAG_CHARS = string.ascii_lowercase + string.digits + '_-'
MIN_TAG_NAME_LENGTH = 1
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

SQL_GROUP_COLUMNS = [
    'id',
    'name',
]

SQL_TAGGROUP_COLUMNS = [
    'groupid',
    'memberid',
    'membertype',
]

SQL_GROUP = {key:index for (index, key) in enumerate(SQL_GROUP_COLUMNS)}
SQL_LASTID = {key:index for (index, key) in enumerate(SQL_LASTID_COLUMNS)}
SQL_PHOTO = {key:index for (index, key) in enumerate(SQL_PHOTO_COLUMNS)}
SQL_PHOTOTAG = {key:index for (index, key) in enumerate(SQL_PHOTOTAG_COLUMNS)}
SQL_SYN = {key:index for (index, key) in enumerate(SQL_SYN_COLUMNS)}
SQL_TAG = {key:index for (index, key) in enumerate(SQL_TAG_COLUMNS)}
SQL_TAGGROUP = {key:index for (index, key) in enumerate(SQL_TAGGROUP_COLUMNS)}


DB_INIT = '''
CREATE TABLE IF NOT EXISTS albums(
    albumid TEXT,
    photoid TEXT
);
CREATE TABLE IF NOT EXISTS tags(
    id TEXT,
    name TEXT
);
CREATE TABLE IF NOT EXISTS groups(
    id TEXT,
    name TEXT
);
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
CREATE TABLE IF NOT EXISTS photo_tag_rel(
    photoid TEXT,
    tagid TEXT
);
CREATE TABLE IF NOT EXISTS tag_group_rel(
    groupid TEXT,
    memberid TEXT,
    membertype TEXT
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

CREATE INDEX IF NOT EXISTS index_group_id on groups(id);

CREATE INDEX IF NOT EXISTS index_tagrel_photoid on photo_tag_rel(photoid);
CREATE INDEX IF NOT EXISTS index_tagrel_tagid on photo_tag_rel(tagid);

CREATE INDEX IF NOT EXISTS index_tagsyn_name on tag_synonyms(name);

CREATE INDEX IF NOT EXISTS index_grouprel_groupid on tag_group_rel(groupid);
CREATE INDEX IF NOT EXISTS index_grouprel_memberid on tag_group_rel(memberid);
'''

def basex(number, base, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    '''
    Converts an integer to a different base string.
    Based on http://stackoverflow.com/a/1181922/5430534
    '''
    if base > len(alphabet):
        raise Exception('alphabet %s does not support base %d' % (repr(alphabet), base))

    if not isinstance(number, (int, str)):
        raise TypeError('number must be an integer')

    alphabet = alphabet[:base]
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

def int_or_none(i):
    if i is None:
        return i
    return int(i)

def is_xor(*args):
    '''
    Return True if and only if one arg is truthy.
    '''
    return [bool(a) for a in args].count(True) == 1

def min_max_query_builder(name, comparator, value):
    return ' '.join([name, comparator, value])

def normalize_tagname(tagname):
    '''
    Tag names can only consist of VALID_TAG_CHARS.
    The given tagname is lowercased, gets its spaces
    replaced by underscores, and is stripped of any not-whitelisted
    characters.
    '''
    tagname = tagname.lower()
    tagname = tagname.replace(' ', '_')
    tagname = (c for c in tagname if c in VALID_TAG_CHARS)
    tagname = ''.join(tagname)

    if len(tagname) < MIN_TAG_NAME_LENGTH:
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

def raise_no_such_thing(exception_class, thing_id=None, thing_name=None, comment=''):
    if thing_id is not None:
        message = 'ID: %s. %s' % (thing_id, comment)
    elif thing_name is not None:
        message = 'Name: %s. %s' % (thing_name, comment)
    else:
        message = ''
    raise exception_class(message)

def select(sql, query, bindings=[]):
    cursor = sql.cursor()
    cursor.execute(query, bindings)
    while True:
        fetch = cursor.fetchone()
        if fetch is None:
            break
        yield fetch


####################################################################################################
####################################################################################################


class NoSuchGroup(Exception):
    pass

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

class GroupExists(Exception):
    pass


class TagTooLong(Exception):
    pass

class TagTooShort(Exception):
    pass

class XORException(Exception):
    pass


####################################################################################################
####################################################################################################


class PDBGroupMixin:
    def get_group(self, groupname=None, groupid=None):
        '''
        Redirect to get_group_by_id or get_group_by_name after xor-checking the parameters.
        '''
        if not is_xor(groupid, groupname):
            raise XORException('One and only one of `groupid`, `groupname` can be passed.')

        if groupid is not None:
            return self.get_thing_by_id('group', thing_id=groupid)
        elif groupname is not None:
            return self.get_group_by_name(groupname)
        else:
            raise_no_such_thing(NoSuchTag, thing_id=groupid, thing_name=groupname)

    def get_group_by_id(self, groupid):
        return self.get_thing_by_id('group', groupid)

    def get_group_by_name(self, groupname):
        if isinstance(groupname, Group):
            if groupname.photodb == self:
                return groupname
            groupname = groupname.name

        groupname = normalize_tagname(groupname)

        self.cur.execute('SELECT * FROM groups WHERE name == ?', [groupname])
        fetch = self.cur.fetchone()
        if fetch is None:
            raise_no_such_thing(NoSuchGroup, thing_name=groupname)

        group = Group(self, fetch)
        return group

    def get_groups(self):
        yield from self.get_things(thing_type='group')

    def new_group(self, groupname, commit=True):
        '''
        Register a new tag group and return the Group object.
        '''
        groupname = normalize_tagname(groupname)
        try:
            self.get_group_by_name(groupname)
        except NoSuchGroup:
            pass
        else:
            raise GroupExists(groupname)

        groupid = self.generate_id('groups')
        self.cur.execute('INSERT INTO groups VALUES(?, ?)', [groupid, groupname])
        if commit:
            self.sql.commit()

        group = Group(self, [groupid, groupname])
        return group


class PDBPhotoMixin:
    def get_photo_by_id(self, photoid):
        return self.get_thing_by_id('photo', photoid)

    def get_photo_by_path(self, filepath):
        filepath = os.path.abspath(filepath)
        self.cur.execute('SELECT * FROM photos WHERE filepath == ?', [filepath])
        fetch = self.cur.fetchone()
        if fetch is None:
            raise_no_such_thing(NoSuchPhoto, thing_name=filepath)
        photo = Photo(self, fetch)
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
                break
            photo = Photo(self, f)

            yield photo

            if count is None:
                continue
            count -= 1
            if count <= 0:
                break

    def get_photos_by_search(
            self,
            extension=None,
            maximums={},
            minimums={},
            no_tags=None,
            orderby=[],
            tag_musts=None,
            tag_mays=None,
            tag_forbids=None,
        ):
        '''
        extension:
            A string or list of strings of acceptable file extensions.

        maximums  
            A dictionary, where the key is an attribute of the photo,
            (area, bytes, created, height, id, or width)
            and the value is the maximum desired value for that field.

        minimums:
            A dictionary like `maximums` where the value is the minimum
            desired value for that field.

        no_tags:
            If True, require that the Photo has no tags.
            If False, require that the Photo has >=1 tag.
            If None, not considered.

        orderby:
            A list of strings like ['ratio DESC', 'created ASC'] to sort
            and subsort the results.
            Descending is assumed if not provided.

        tag_musts:
            A list of tag names or Tag objects.
            Photos MUST have ALL tags in this list.

        tag_mays:
            A list of tag names or Tag objects.
            Photos MUST have AT LEAST ONE tag in this list.

        tag_forbids:
            A list of tag names or Tag objects.
            Photos MUST NOT have ANY tag in the list.
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

        if isinstance(extension, str):
            extension = [extension]
        if extension is not None:
            extension = [e.lower() for e in extension]

        def validate_orderby(o):
            o = o.lower()
            o = o.split(' ')
            assert len(o) in (1, 2)
            if len(o) == 1:
                o.append('desc')
            assert o[0] in ['extension', 'width', 'height', 'ratio', 'area', 'bytes', 'created']
            o = ' '.join(o)
            return o

        orderby = [validate_orderby(o) for o in orderby]
        orderby = ', '.join(orderby)
        print(orderby)

        def setify(l):
            if l is None:
                return set()
            else:
                return set(self.get_tag_by_name(t) for t in l)

        tag_musts = setify(tag_musts)
        tag_mays = setify(tag_mays)
        tag_forbids = setify(tag_forbids)

        query = 'SELECT * FROM photos'
        if orderby:
            query += ' ORDER BY %s' % orderby
        print(query)
        generator = select(self.sql, query)
        for fetch in generator:
            if extension and not any(fetch[SQL_PHOTO['extension']].lower() == e for e in extension):
                #print('Failed extension')
                continue

            if any(fetch[SQL_PHOTO[key]] and fetch[SQL_PHOTO[key]] > value for (key, value) in maximums.items()):
                #print('Failed maximums')
                continue

            if any(fetch[SQL_PHOTO[key]] and fetch[SQL_PHOTO[key]] < value for (key, value) in minimums.items()):
                #print('Failed minimums')
                continue

            photo = Photo(self, fetch)
            if (no_tags is not None) or tag_musts or tag_mays or tag_forbids:
                photo_tags = photo.get_tags()

            if no_tags is True and len(photo_tags) > 0:
                continue

            if no_tags is False and len(photo_tags) == 0:
                continue

            if tag_musts and any(tag not in photo_tags for tag in tag_musts):
                #print('Failed musts')
                continue

            if tag_mays and not any(may in photo_tags for may in tag_mays):
                #print('Failed mays')
                continue

            if tag_forbids and any(forbid in photo_tags for forbid in tag_forbids):
                #print('Failed forbids')
                continue

            yield photo

    def new_photo(self, filename, tags=None, allow_duplicates=False, commit=True):
        '''
        Given a filepath, determine its attributes and create a new Photo object in the
        database. Tags may be applied now or later.

        If `allow_duplicates` is False, we will first check the database for any files
        with the same path and raise PhotoExists if found.

        Returns the Photo object.
        '''
        filename = os.path.abspath(filename)
        if not allow_duplicates:
            try:
                existing = self.get_photo_by_path(filename)
            except NoSuchPhoto:
                pass
            else:
                raise PhotoExists(filename, existing)

        try:
            image = PIL.Image.open(filename)
            (width, height) = image.size
            area = width * height
            ratio = width / height
            image.close()
        except OSError:
            # PIL did not recognize it as an image
            width = None
            height = None
            area = None
            ratio = None

        extension = os.path.splitext(filename)[1]
        extension = extension.replace('.', '')
        extension = normalize_tagname(extension)
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
        photo = Photo(self, data)

        self.cur.execute('INSERT INTO photos VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)', data)

        tags = tags or []
        for tag in tags:
            try:
                photo.apply_tag(tag, commit=False)
            except NoSuchTag:
                self.sql.rollback()
                raise
        if commit:
            self.sql.commit()
        return photo


class PDBTagMixin:
    def convert_tag_to_synonym(self, oldtagname, mastertagname):
        '''
        Convert an independent tag into a synonym for a different independent tag.
        All photos which possess the current tag will have it replaced
        with the new master tag.
        All synonyms of the old tag will point to the new tag.

        Good for when two tags need to be merged under a single name.
        '''
        oldtagname = normalize_tagname(oldtagname)
        mastertagname = normalize_tagname(mastertagname)

        oldtag = self.get_tag_by_name(oldtagname)
        if oldtag.name != oldtagname:
            # The inputted name was a synonym and we got redirected.
            raise NoSuchTag('%s is not an independent tag!' % oldtagname)

        mastertag = self.get_tag_by_name(mastertagname)
        if mastertag.name != mastertagname:
            raise NoSuchTag('%s is not an independent tag!' % mastertagname)

        # Migrate the old tag's synonyms to the new one
        # UPDATE is safe for this operation because there is no chance of duplicates.
        self.cur.execute(
            'UPDATE tag_synonyms SET mastername = ? WHERE mastername == ?',
            [mastertagname, oldtagname]
        )

        # Iterate over all photos with the old tag, and relate them to the new tag
        # if they aren't already.
        generator = select(self.sql, 'SELECT * FROM photo_tag_rel WHERE tagid == ?', [oldtag.id])
        for relationship in generator:
            photoid = relationship[SQL_PHOTOTAG['photoid']]
            self.cur.execute('SELECT * FROM photo_tag_rel WHERE tagid == ?', [mastertag.id])
            if self.cur.fetchone() is not None:
                continue
            self.cur.execute('INSERT INTO photo_tag_rel VALUES(?, ?)', [photoid, mastertag.id])

        # Then delete the relationships with the old tag
        self.cur.execute('DELETE FROM photo_tag_rel WHERE tagid == ?', [oldtag.id])
        self.cur.execute('DELETE FROM tags WHERE id == ?', [oldtag.id])
        
        # Enjoy your new life as a monk.
        mastertag.new_synonym(oldtag.name, commit=True)

    def export_tags(self):
        def print_children(obj, depth=1):
            msg = ' ' * (4 * depth)
            if isinstance(obj, Group):
                children = obj.children()
                children.sort(key=lambda x: (x._membertype, x.name))
                for child in children:
                    print(msg, child, sep='')
                    print_children(child, depth=depth+1)
            else:
                synonyms = obj.get_synonyms()
                synonyms.sort()
                for synonym in synonyms:
                    print(msg, synonym, sep='')
                

        items = list(self.get_groups()) + list(self.get_tags())
        items.sort(key=lambda x: (x._membertype, x.name))
        for item in items:
            if item.group() is not None:
                continue
            print(item)
            print_children(item)

    def get_tag(self, tagname=None, tagid=None):
        '''
        Redirect to get_tag_by_id or get_tag_by_name after xor-checking the parameters.
        '''
        if not is_xor(tagid, tagname):
            raise XORException('One and only one of `tagid`, `tagname` can be passed.')

        if tagid is not None:
            return self.get_tag_by_id(tagid)
        elif tagname is not None:
            return self.get_tag_by_name(tagname)
        else:
            raise_no_such_thing(NoSuchTag, thing_id=tagid, thing_name=tagname)

    def get_tag_by_id(self, tagid):
        return self.get_thing_by_id('tag', thing_id=tagid)

    def get_tag_by_name(self, tagname):
        if isinstance(tagname, Tag):
            if tagname.photodb == self:
                return tagname
            tagname = tagname.name

        tagname = normalize_tagname(tagname)

        while True:
            # Return if it's a toplevel, or resolve the synonym and try that.
            self.cur.execute('SELECT * FROM tags WHERE name == ?', [tagname])
            fetch = self.cur.fetchone()
            if fetch is not None:
                return Tag(self, fetch)

            self.cur.execute('SELECT * FROM tag_synonyms WHERE name == ?', [tagname])
            fetch = self.cur.fetchone()
            if fetch is None:
                # was not a top tag or synonym
                raise_no_such_thing(NoSuchTag, thing_name=tagname)
            tagname = fetch[SQL_SYN['master']]

    def get_tags(self):
        yield from self.get_things(thing_type='tag')

    def new_tag(self, tagname, commit=True):
        '''
        Register a new tag in and return the Tag object.
        '''
        tagname = normalize_tagname(tagname)
        try:
            self.get_tag_by_name(tagname)
        except NoSuchTag:
            pass
        else:
            raise TagExists(tagname)
        tagid = self.generate_id('tags')
        self.cur.execute('INSERT INTO tags VALUES(?, ?)', [tagid, tagname])
        if commit:
            self.sql.commit()
        tag = Tag(self, [tagid, tagname])
        return tag


class PhotoDB(PDBGroupMixin, PDBPhotoMixin, PDBTagMixin):
    '''
    This class represents an SQLite3 database containing the following tables:

    albums:
        Rows represent the inclusion of a photo in an album

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
        will be resolved and used instead, so a synonym never points to another synonym.
        Tag objects will ALWAYS represent the master tag.

        Note that the entries in this table do not contain ID numbers.
        The rationale here is that "coco" is a synonym for "chocolate" regardless
        of the "chocolate" tag's ID, and that if a tag is renamed, its synonyms
        do not necessarily follow.
        The `rename` method of Tag objects includes a parameter
        `apply_to_synonyms` if you do want them to follow.
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

    def generate_id(self, table):
        '''
        Create a new ID number that is unique to the given table.
        Note that this method does not commit the database. We'll wait for that
        to happen in whoever is calling us, so we know the ID is actually used.
        '''
        table = table.lower()
        if table not in ['photos', 'tags', 'groups']:
            raise ValueError('Invalid table requested: %s.', table)

        do_insert = False
        if table in self._last_ids:
            # Use cache value
            new_id_int = self._last_ids[table] + 1
        else:
            self.cur.execute('SELECT * FROM id_numbers WHERE tab == ?', [table])
            fetch = self.cur.fetchone()
            if fetch is None:
                # Register new value
                new_id_int = 1
                do_insert = True
            else:
                # Use database value
                new_id_int = int(fetch[SQL_LASTID['last_id']]) + 1
                
        new_id = str(new_id_int).rjust(self.id_length, '0')
        if do_insert:
            self.cur.execute('INSERT INTO id_numbers VALUES(?, ?)', [table, new_id])
        else:
            self.cur.execute('UPDATE id_numbers SET last_id = ? WHERE tab == ?', [new_id, table])
        self._last_ids[table] = new_id_int
        return new_id

    def get_thing_by_id(self, thing_type, thing_id):
        thing_map = self.thing_map(thing_type)

        if isinstance(thing_id, thing_map['class']):
            if thing_id.photodb == self:
                return thing_id
            thing_id = thing_id.id

        query = 'SELECT * FROM %s WHERE id == ?' % thing_map['table']
        self.cur.execute(query, [thing_id])
        thing = self.cur.fetchone()
        if thing is None:
            return raise_no_such_thing(thing_map['exception'], thing_id=thing_id)
        thing = thing_map['class'](self, thing)
        return thing

    def get_things(self, thing_type, orderby=None):
        thing_map = self.thing_map(thing_type)

        if orderby:
            self.cur.execute('SELECT * FROM %s ORDER BY %s' % (thing_map['table'], orderby))
        else:
            self.cur.execute('SELECT * FROM %s' % thing_map['table'])

        things = self.cur.fetchall()
        for thing in things:
            thing = thing_map['class'](self, row_tuple=thing)
            yield thing

    def thing_map(self, thing_type):
        if thing_type == 'tag':
            return {
                'class': Tag,
                'exception': NoSuchTag,
                'table': 'tags',
            }

        elif thing_type == 'group':
            return {
                'class': Group,
                'exception': NoSuchGroup,
                'table': 'groups',
            }

        elif thing_type == 'photo':
            return {
                'class': Photo,
                'exception': NoSuchPhoto,
                'table': 'photos',
            }

        else:
            raise Exception('Unknown type %s' % thing_type)


####################################################################################################
####################################################################################################


class ObjectBase:
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class Groupable:
    def group(self):
        '''
        Return the Group object of which this is a member, or None.
        '''
        self.photodb.cur.execute(
            'SELECT * FROM tag_group_rel WHERE memberid == ? AND membertype == ?',
            [self.id, self._membertype]
        )
        fetch = self.photodb.cur.fetchone()
        if fetch is None:
            return None

        groupid = fetch[SQL_TAGGROUP['groupid']]
        return self.photodb.get_group(groupid=groupid)

    def join(self, group, commit=True):
        '''
        Leave the current group, then call `group.add(self)`.
        '''
        group = self.photodb.get_group(group)
        self.leave_group(commit=commit)
        group.add(self, commit=commit)

    def leave_group(self, commit=True):
        '''
        Leave the current group and become independent.
        '''
        self.photodb.cur.execute(
            'DELETE FROM tag_group_rel WHERE memberid == ? AND membertype == ?',
            [self.id, self._membertype]
        )
        if commit:
            self.photodb.sql.commit()


class Group(ObjectBase, Groupable):
    '''
    A heirarchical organization of related Tags.
    '''
    _membertype = 'group'
    def __init__(self, photodb, row_tuple):
        self.photodb = photodb
        self.id = row_tuple[SQL_GROUP['id']]
        self.name = row_tuple[SQL_GROUP['name']]

    def __repr__(self):
        return 'Group:{name}'.format(name=self.name)

    def add(self, member, commit=True):
        '''
        Add a Tag or Group object to this group.

        If that object is already a member of another group, a GroupExists is raised.
        '''
        if isinstance(member, (str, Tag)):
            member = self.photodb.get_tag(member)
            membertype = 'tag'
        elif isinstance(member, Group):
            member = self.photodb.get_group(member)
            membertype = 'group'
        else:
            raise TypeError('Type `%s` cannot join a Group' % type(member))

        self.photodb.cur.execute(
            'SELECT * FROM tag_group_rel WHERE memberid == ? AND membertype == ?',
            [member.id, membertype]
        )
        fetch = self.photodb.cur.fetchone()
        if fetch is not None:
            if fetch[SQL_TAGGROUP['groupid']] == self.id:
                that_group = self
            else:
                that_group = self.photodb.get_group(groupid=fetch[SQL_TAGGROUP['groupid']])
            raise GroupExists('%s already in group %s' % (member.name, that_group.name))

        self.photodb.cur.execute(
            'INSERT INTO tag_group_rel VALUES(?, ?, ?)',
            [self.id, member.id, membertype]
        )
        if commit:
            self.photodb.sql.commit()

    def children(self):
        self.photodb.cur.execute('SELECT * FROM tag_group_rel WHERE groupid == ?', [self.id])
        fetch = self.photodb.cur.fetchall()
        results = []
        for f in fetch:
            memberid = f[SQL_TAGGROUP['memberid']]
            if f[SQL_TAGGROUP['membertype']] == 'tag':
                results.append(self.photodb.get_tag(tagid=memberid))
            else:
                results.append(self.photodb.get_group(groupid=memberid))
        return results

    def delete(self, delete_children=False, commit=True):
        '''
        Delete the group.

        delete_children:
            If True, all child groups and tags will be deleted.
            Otherwise they'll just be raised up one level.
        '''
        if delete_children:
            for child in self.children():
                child.delete()
        else:
            # Lift children
            parent = self.group()
            if parent is None:
                # Since this group was a root, children become roots by removing the row.
                self.photodb.cur.execute('DELETE FROM tag_group_rel WHERE groupid == ?', [self.id])
            else:
                # Since this group was a child, its parent adopts all its children.
                self.photodb.cur.execute(
                    'UPDATE tag_group_rel SET groupid == ? WHERE groupid == ?',
                    [parent.id, self.id]
                )
        # Note that this part comes after the deletion of children to prevent issues of recursion.
        self.photodb.cur.execute('DELETE FROM groups WHERE id == ?', [self.id])
        self.photodb.cur.execute(
            'DELETE FROM tag_group_rel WHERE memberid == ? AND membertype == "group"',
            [self.id]
        )
        if commit:
            self.photodb.sql.commit()

    def rename(self, new_name, commit=True):
        '''
        Rename the group. Does not affect its tags.
        '''
        new_name = normalize_tagname(new_name)

        try:
            existing = self.photodb.get_group(new_name)
        except NoSuchGroup:
            pass
        else:
            raise GroupExists(new_name)

        self.photodb.cur.execute('UPDATE groups SET name = ? WHERE id == ?', [new_name, self.id])

        self.name = new_name
        if commit:
            self.photodb.sql.commit()



class Photo(ObjectBase):
    '''
    A PhotoDB entry containing information about an image file.
    Photo objects cannot exist without a corresponding PhotoDB object, because
    Photos are not the actual image data, just the database entry. 
    '''
    def __init__(self, photodb, row_tuple):
        width = row_tuple[SQL_PHOTO['width']]
        height = row_tuple[SQL_PHOTO['height']]
        if width is not None:
            area = width * height
            ratio = width / height
        else:
            area = None
            ratio = None

        self.photodb = photodb
        self.id = row_tuple[SQL_PHOTO['id']]
        self.filepath = row_tuple[SQL_PHOTO['filepath']]
        self.extension = row_tuple[SQL_PHOTO['extension']]
        self.width = int_or_none(width)
        self.height = int_or_none(height)
        self.ratio = ratio
        self.area = area
        self.bytes = int(row_tuple[SQL_PHOTO['bytes']])
        self.created = int(row_tuple[SQL_PHOTO['created']])

    def __repr__(self):
        return 'Photo:{id}'.format(id=self.id)

    def apply_tag(self, tag, commit=True):
        tag = self.photodb.get_tag(tag)

        if self.has_tag(tag):
            return

        self.photodb.cur.execute('INSERT INTO photo_tag_rel VALUES(?, ?)', [self.id, tag.id])
        if commit:
            self.photodb.sql.commit()

    def delete(self, commit=True):
        '''
        Delete the Photo and its relation to any tags and albums.
        '''
        self.photodb.cur.execute('DELETE FROM photos WHERE id == ?', [self.id])
        self.photodb.cur.execute('DELETE FROM photo_tag_rel WHERE photoid == ?', [self.id])
        self.photodb.cur.execute(
            'DELETE FROM tag_group_rel WHERE memberid == ? AND membertype == "tag"',
            [self.id]
        )
        if commit:
            self.photodb.sql.commit()

    def tags(self):
        '''
        Return the tags assigned to this Photo.
        '''
        tagobjects = set()
        generator = select(
            self.photodb.sql,
            'SELECT * FROM photo_tag_rel WHERE photoid == ?',
            [self.id]
        )
        for tag in generator:
            tagid = tag[SQL_PHOTOTAG['tagid']]
            tagobj = self.photodb.get_tag(tagid=tagid)
            tagobjects.add(tagobj)
        return tagobjects

    def has_tag(self, tag):
        tag = self.photodb.get_tag(tag)

        self.photodb.cur.execute(
            'SELECT * FROM photo_tag_rel WHERE photoid == ? AND tagid == ?',
            [self.id, tag.id]
        )
        fetch = self.photodb.cur.fetchone()
        has_tag = fetch is not None
        return has_tag

    def remove_tag(self, tag, commit=True):
        tag = self.photodb.get_tag(tag)

        if not self.has_tag(tag):
            return

        self.photodb.cur.execute('DELETE FROM photo_tag_rel VALUES(?, ?)', [self.id, tag.id])
        if commit:
            self.photodb.sql.commit()


class Tag(ObjectBase, Groupable):
    '''
    A Tag, which can be applied to Photos for organization.
    '''
    _membertype = 'tag'
    def __init__(self, photodb, row_tuple):
        self.photodb = photodb
        self.id = row_tuple[SQL_TAG['id']]
        self.name = row_tuple[SQL_TAG['name']]

    def __repr__(self):
        r = 'Tag:{name}'.format(name= self.name)
        return r

    def add_synonym(self, synname, commit=True):
        synname = normalize_tagname(synname)

        if synname == self.name:
            raise ValueError('Cannot assign synonym to itself.')

        try:
            tag = self.photodb.get_tag_by_name(synname)
        except NoSuchTag:
            pass
        else:
            raise TagExists(synname)

        self.photodb.cur.execute('INSERT INTO tag_synonyms VALUES(?, ?)', [synname, self.name])

        if commit:
            self.photodb.sql.commit()

    def delete(self, commit=True):
        '''
        Delete a tag and its relationship with synonyms, groups, and photos.
        '''
        self.photodb.cur.execute('DELETE FROM tags WHERE id == ?', [self.id])
        self.photodb.cur.execute('DELETE FROM photo_tag_rel WHERE tagid == ?', [self.id])
        self.photodb.cur.execute('DELETE FROM tag_synonyms WHERE mastername == ?', [self.name])
        self.photodb.cur.execute(
            'DELETE FROM tag_group_rel WHERE memberid == ? AND membertype == "tag"',
            [self.id]
        )
        if commit:
            self.photodb.sql.commit()

    def delete_synonym(self, synname, commit=True):
        '''
        Delete a synonym.
        This will have no effect on photos or other synonyms because
        they always resolve to the master tag before application.
        '''
        synname = normalize_tagname(synname)
        self.photodb.cur.execute('SELECT * FROM tag_synonyms WHERE name == ?', [synname])
        fetch = self.photodb.cur.fetchone()
        if fetch is None:
            raise NoSuchSynonym(synname)

        self.photodb.cur.execute('DELETE FROM tag_synonyms WHERE name == ?', [synname])
        if commit:
            self.photodb.sql.commit()

    def get_synonyms(self):
        self.photodb.cur.execute('SELECT name FROM tag_synonyms WHERE mastername == ?', [self.name])
        fetch = self.photodb.cur.fetchall()
        fetch = [f[0] for f in fetch]
        return fetch

    def rename(self, new_name, apply_to_synonyms=True, commit=True):
        '''
        Rename the tag. Does not affect its relation to Photos.
        '''
        new_name = normalize_tagname(new_name)

        try:
            existing = self.photodb.get_tag(new_name)
        except NoSuchTag:
            pass
        else:
            raise TagExists(new_name)

        self.photodb.cur.execute('UPDATE tags SET name = ? WHERE id == ?', [new_name, self.id])
        if apply_to_synonyms:
            self.photodb.cur.execute(
                'UPDATE tag_synonyms SET mastername = ? WHERE mastername = ?',
                [new_name, self.name]
            )

        self.name = new_name
        if commit:
            self.photodb.sql.commit()


if __name__ == '__main__':
    p = PhotoDB()