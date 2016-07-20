DOCSTRING='''
OpenDirDL
downloads open directories

The basics:
1. Create a database of the directory's files with
    > opendirdl digest http://website.com/directory/
2. Enable and disable the files you are interested in with
    > opendirdl remove_pattern ".*"
    > opendirdl keep_pattern "Daft%20Punk"
    > opendirdl remove_pattern "folder\.jpg"
   Note the percent-encoded string.
3. Download the enabled files with
    > opendirdl download website.com.db


The specifics:
digest:
    Recursively fetch directories and build a database of file URLs.

    > opendirdl digest http://website.com/directory/ <flags>
    > opendirdl digest !clipboard <flags>

    flags:
    -f | --fullscan:
        When included, perform HEAD requests on all files, to know the size of
        the entire directory.

    -db "x.db" | --databasename "x.db":
        Use a custom database filename. By default, databases are named after
        the web domain.

download:
    Download the files whose URLs are Enabled in the database.

    > opendirdl download website.com.db <flags>

    flags:
    -o "x" | --outputdir "x":
        Save the files to a custom directory, "x". By default, files are saved
        to a folder named after the web domain.

    -ow | --overwrite:
        When included, download and overwrite files even if they already exist
        in the output directory.

    -bps 100 | --bytespersecond 100:
        Ratelimit yourself to downloading at 100 BYTES per second.
        The webmaster will appreciate this.

keep_pattern:
    Enable URLs which match a regex pattern. Matches are based on the percent-
    encoded strings!

    > opendirdl keep_pattern website.com.db ".*"

remove_pattern:
    Disable URLs which match a regex pattern. Matches are based on the percent-
    encoded strings!

    > opendirdl remove_pattern website.com.db ".*"

list_basenames:
    List Enabled URLs in order of their base filename. This makes it easier to
    find titles of interest in a directory that is very scattered or poorly
    organized.

    > opendirdl list_basenames website.com.db <flags>

    flags:
    -o "x.txt" | --outputfile "x.txt":
        Output the results to a file instead of stdout. This is useful if the
        filenames contain special characters that crash Python, or are so long
        that the console becomes unreadable.

measure:
    Sum up the filesizes of all Enabled URLs.

    > opendirdl measure website.com.db <flags>

    flags:
    -f | --fullscan:
        When included, perform HEAD requests on all files to update their size.

    -n | --new_only:
        When included, perform HEAD requests only on files that haven't gotten
        one yet.

    If a file's size is not known by the time this operation completes, you
    will receive a printed note.

tree:
    Print the file / folder tree.

    > opendirdl tree website.com.db <flags>

    flags:
    -o "x.txt" | --outputfile "x.txt":
        Output the results to a file instead of stdout. This is useful if the
        filenames contain special characters that crash Python, or are so long
        that the console becomes unreadable.

        If the filename ends with ".html", the created page will have
        collapsible boxes rather than a plaintext diagram.
'''


# Module names preceeded by `## ~` indicate modules that are imported during
# a function, because they are not used anywhere else and we don't need to waste
# time importing them usually.
import sys

# Please consult my github repo for these files
# https://github.com/voussoir/else
sys.path.append('C:\\git\\else\\ratelimiter'); import ratelimiter
sys.path.append('C:\\git\\else\\bytestring'); import bytestring

import argparse
## ~import bs4
import collections
## ~import hashlib
import os
## ~import re
import requests
import shutil
import sqlite3
## ~tkinter
import traceback
import urllib.parse

FILENAME_BADCHARS = '/\\:*?"<>|'

TERMINAL_WIDTH = shutil.get_terminal_size().columns

DOWNLOAD_CHUNK = 16 * bytestring.KIBIBYTE

UNKNOWN_SIZE_STRING = '???'

# When doing a basic scan, we will not send HEAD requests to URLs that end in these strings,
# because they're probably files.
# This isn't meant to be a comprehensive filetype library, but it covers enough of the
# typical opendir to speed things up.
SKIPPABLE_FILETYPES = [
'.aac',
'.avi',
'.bin',
'.bmp',
'.bz2',
'.epub',
'.exe',
'.db',
'.flac',
'.gif',
'.gz',
'.ico',
'.iso',
'.jpeg',
'.jpg',
'.m3u',
'.m4a',
'.m4v',
'.mka',
'.mkv',
'.mov',
'.mp3',
'.mp4',
'.nfo',
'.ogg',
'.ott',
'.pdf',
'.png',
'.rar',
'.srt',
'.tar',
'.ttf',
'.txt',
'.wav',
'.webm',
'.wma',
'.zip',
]
SKIPPABLE_FILETYPES = set(x.lower() for x in SKIPPABLE_FILETYPES)

# oh shit
HTML_TREE_HEADER = '''
<meta charset="UTF-8">

<script type="text/javascript">
function collapse(id)
{
    div = document.getElementById(id);
    if (div.style.display != "none")
    {
        div.style.display = "none";
    }
    else
    {
        div.style.display = "block";
    }
}
</script>

<style>
*
{
    font-family: Consolas;
}

button
{
    display: block;
}

div
{
    padding: 10px;
    padding-left: 15px;
    margin-bottom: 10px;
    border: 1px solid #000;
    box-shadow: 1px 1px 2px 0px rgba(0,0,0,0.3);
}

.directory_even
{
    background-color: #fff;
}

.directory_odd
{
    background-color: #eee;
}
</style>
'''

DB_INIT = '''
CREATE TABLE IF NOT EXISTS urls(
    url TEXT,
    basename TEXT,
    content_length INT,
    content_type TEXT,
    do_download INT
);
CREATE INDEX IF NOT EXISTS urlindex on urls(url);
CREATE INDEX IF NOT EXISTS baseindex on urls(basename);
CREATE INDEX IF NOT EXISTS sizeindex on urls(content_length);
'''.strip()
SQL_URL = 0
SQL_BASENAME = 1
SQL_CONTENT_LENGTH = 2
SQL_CONTENT_TYPE = 3
SQL_DO_DOWNLOAD = 4


UNMEASURED_WARNING = '''
Note: %d files do not have a stored Content-Length.
Run `measure` with `-f`|`--fullscan` or `-n`|`--new_only` to HEAD request
those files.
'''.strip()


## WALKER ##########################################################################################
##                                                                                                ##
class Walker:
    def __init__(self, walkurl, databasename=None, fullscan=False):
        if walkurl[-1] != '/':
            walkurl += '/'
        self.walkurl = walkurl
        if databasename is None or databasename == "":
            self.domain = url_to_filepath(walkurl)['root']
            databasename = self.domain + '.db'
            databasename = databasename.replace(':', '#')
        self.databasename = databasename

        safeprint('Opening %s' % self.databasename)
        self.sql = sqlite3.connect(self.databasename)
        self.cur = self.sql.cursor()
        db_init(self.sql, self.cur)

        self.fullscan = bool(fullscan)
        self.queue = collections.deque()
        self.seen_directories = set()

    def smart_insert(self, url=None, head=None, commit=True):
        '''
        See `smart_insert`.
        '''
        smart_insert(self.sql, self.cur, url=url, head=head, commit=commit)

    def extract_hrefs(self, response, tag='a', attribute='href'):
        '''
        Given a Response object, extract href urls.
        External links, index sort links, and desktop.ini are discarded.
        '''
        import bs4
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        elements = soup.findAll(tag)
        for element in elements:
            try:
                href = element[attribute]
            except KeyError:
                continue
            href = urllib.parse.urljoin(response.url, href)
            if not href.startswith(self.walkurl):
                # Don't go to other sites or parent directories.
                continue
            #if 'C=' in href and 'O=' in href:
            if any(sorter in href for sorter in ('?C=', '?O=', '?M=', '?D=', '?N=', '?S=')):
                # Alternative sort modes for index pages.
                continue
            if href.endswith('desktop.ini'):
                # I hate these things.
                continue
            yield href

    def process_url(self, url=None):
        '''
        Given a URL, check whether it is an index page or an actual file.
        If it is an index page, it's links are extracted and queued.
        If it is a file, its information is saved to the database.

        We perform a 
        HEAD:
            when `self.fullscan` is True.
            when `self.fullscan` is False but the url is not a SKIPPABLE_FILETYPE.
            when the url is an index page.
        GET:
            when the url is a index page.
        '''
        if url is None:
            url = self.walkurl
        else:
            url = urllib.parse.urljoin(self.walkurl, url)

        if url in self.seen_directories:
            # We already picked this up at some point
            return

        if not url.startswith(self.walkurl):
            # Don't follow external links or parent directory.
            safeprint('Skipping "%s" due to external url.' % url)
            return

        urll = url.lower()
        if self.fullscan is False:
            skippable = any(urll.endswith(ext) for ext in SKIPPABLE_FILETYPES)
            if skippable:
                safeprint('Skipping "%s" due to extension.' % url)
                self.smart_insert(url=url, commit=False)
                return
            self.cur.execute('SELECT * FROM urls WHERE url == ?', [url])
            skippable = self.cur.fetchone() is not None
            if skippable:
                safeprint('Skipping "%s" since we already have it.' % url)
                return

        try:
            head = do_head(url)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print('403 FORBIDDEN!')
                return
            if e.response.status_code == 404:
                print('404 NOT FOUND!')
                return
            raise
        content_type = head.headers.get('Content-Type', '?')
        #print(content_type)
        if content_type.startswith('text/html'):# and head.url.endswith('/'):
            # This is an index page, so extract links and queue them.
            response = do_get(url)
            hrefs = self.extract_hrefs(response)
            # Just in case the URL we used is different than the real one,
            # such as missing a trailing slash, add both.
            self.seen_directories.add(url)
            self.seen_directories.add(head.url)
            added = 0
            for href in hrefs:
                if href in self.seen_directories:
                    continue
                else:
                    self.queue.append(href)
                    added += 1
            print('Queued %d urls' % added)
        else:
            # This is not an index page, so save it.
            self.smart_insert(head=head, commit=False)

    def walk(self, url=None):
        self.queue.appendleft(url)
        try:
            while len(self.queue) > 0:
                # Popping from right helps keep the queue short because it handles the files
                # early.
                url = self.queue.popleft()
                self.process_url(url)
                line = '{:,} Remaining'.format(len(self.queue))
                print(line)
        except:
            self.sql.commit()
            raise
        self.sql.commit()
##                                                                                                ##
## WALKER ##########################################################################################


## DOWNLOADER ######################################################################################
##                                                                                                ##
class Downloader:
    def __init__(self, databasename, outputdir=None, headers=None):
        self.databasename = databasename
        self.sql = sqlite3.connect(databasename)
        self.cur = self.sql.cursor()

        if outputdir is None or outputdir == "":
            # This assumes that all URLs in the database are from the same domain.
            # If they aren't, it's the user's fault.
            self.cur.execute('SELECT url FROM urls LIMIT 1')
            url = self.cur.fetchone()[0]
            outputdir = url_to_filepath(url)['root']
        self.outputdir = outputdir

    def download(self, overwrite=False, bytespersecond=None):
        overwrite = bool(overwrite)

        self.cur.execute('SELECT * FROM urls WHERE do_download == 1 ORDER BY url')
        while True:
            fetch = self.cur.fetchone()
            if fetch is None:
                break
            url = fetch[SQL_URL]

            ''' Creating the permanent and temporary filenames '''
            url_filepath = url_to_filepath(url)
            # Ignore this value of `root`, because we might have a custom outputdir.
            root = url_filepath['root']
            folder = os.path.join(root, url_filepath['folder'])
            os.makedirs(folder, exist_ok=True)
            fullname = os.path.join(folder, url_filepath['filename'])
            temporary_basename = hashit(url, 16) + '.oddltemporary'
            temporary_fullname = os.path.join(folder, temporary_basename)

            ''' Managing overwrite '''
            if os.path.isfile(fullname):
                if overwrite is True:
                    os.remove(fullname)
                else:
                    safeprint('Skipping "%s". Use `--overwrite`' % fullname)
                    continue

            safeprint('Downloading "%s" as "%s"' % (fullname, temporary_basename))
            filehandle = open(temporary_fullname, 'wb')
            try:
                download_file(url, filehandle, hookfunction=hook1, bytespersecond=bytespersecond)
                os.rename(temporary_fullname, fullname)
            except:
                filehandle.close()
                raise
##                                                                                                ##
## DOWNLOADER ######################################################################################


## OTHER CLASSES ###################################################################################
##                                                                                                ##
class Generic:
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])


class TreeExistingChild(Exception):
    pass

class TreeInvalidIdentifier(Exception):
    pass

class TreeNode:
    def __init__(self, identifier, data, parent=None):
        assert isinstance(identifier, str)
        assert '\\' not in identifier
        self.identifier = identifier
        self.data = data
        self.parent = parent
        self.children = {}

    def __getitem__(self, key):
        return self.children[key]

    def __repr__(self):
        return 'TreeNode %s' % self.abspath()

    def abspath(self):
        node = self
        nodes = [node]
        while node.parent is not None:
            node = node.parent
            nodes.append(node)
        nodes.reverse()
        nodes = [node.identifier for node in nodes]
        return '\\'.join(nodes)

    def add_child(self, other_node, overwrite_parent=False):
        self.check_child_availability(other_node.identifier)
        if other_node.parent is not None and not overwrite_parent:
            raise ValueError('That node already has a parent. Try `overwrite_parent=True`')

        other_node.parent = self
        self.children[other_node.identifier] = other_node
        return other_node

    def check_child_availability(self, identifier):
        if ':' in identifier:
            raise TreeInvalidIdentifier('Only roots may have a colon')
        if identifier in self.children:
            raise TreeExistingChild('Node %s already has child %s' % (self.identifier, identifier))

    def detach(self):
        del self.parent.children[self.identifier]
        self.parent = None

    def listnodes(self, customsort=None):
        items = list(self.children.items())
        if customsort is None:
            items.sort(key=lambda x: x[0].lower())
        else:
            items.sort(key=customsort)
        return [item[1] for item in items]

    def merge_other(self, othertree, otherroot=None):
        newroot = None
        if ':' in othertree.identifier:
            if otherroot is None:
                raise Exception('Must specify a new name for the other tree\'s root')
            else:
                newroot = otherroot
        else:
            newroot = othertree.identifier
        othertree.identifier = newroot
        othertree.parent = self
        self.check_child_availability(newroot)
        self.children[newroot] = othertree

    def printtree(self, customsort=None):
        for node in self.walk(customsort):
            print(node.abspath())

    def sorted_children(self, customsort=None):
        if customsort:
            keys = sorted(self.children.keys(), key=customsort)
        else:
            keys = sorted(self.children.keys())
        for key in keys:
            yield (key, self.children[key])

    def walk(self, customsort=None):
        yield self
        for child in self.listnodes(customsort=customsort):
            #print(child)
            #print(child.listnodes())
            yield from child.walk(customsort=customsort)
##                                                                                                ##
## OTHER CLASSES ###################################################################################


## GENERAL FUNCTIONS ###############################################################################
##                                                                                                ##
def db_init(sql, cur):
    lines = DB_INIT.split(';')
    for line in lines:
        cur.execute(line)
    sql.commit()
    return True

def dict_to_file(jdict, filename):
    text = dict_to_string(jdict)
    text = text.encode('utf-8')
    filehandle = open(filename, 'wb')
    filehandle.write(text)
    filehandle.close()

def do_get(url, raise_for_status=True):
    return do_request('GET', requests.get, url)

def do_head(url, raise_for_status=True):
    return do_request('HEAD', requests.head, url)

def do_request(message, method, url, raise_for_status=True):
    message = '{message:>4s}: {url} : '.format(message=message, url=url)
    safeprint(message, end='', flush=True)
    response = method(url)
    safeprint(response.status_code)
    if raise_for_status:
        response.raise_for_status()
    return response
    
def download_file(url, filehandle, hookfunction=None, headers={}, bytespersecond=None):
    if bytespersecond is not None:
        limiter = ratelimiter.Ratelimiter(allowance_per_period=bytespersecond, period=1)
    else:
        limiter = None

    currentblock = 0
    downloading = requests.get(url, stream=True, headers=headers)
    totalsize = int(downloading.headers.get('content-length', 1))
    for chunk in downloading.iter_content(chunk_size=DOWNLOAD_CHUNK):
        if not chunk:
            break
        currentblock += 1
        filehandle.write(chunk)
        if limiter is not None:
            limiter.limit(len(chunk))
        if hookfunction is not None:
            hookfunction(currentblock, DOWNLOAD_CHUNK, totalsize)

    filehandle.close()
    size = os.path.getsize(filehandle.name)
    if size < totalsize:
        raise Exception('Did not receive expected total size. %d / %d' % (size, totalsize))
    return True

def filepath_sanitize(text, allowed=''):
    bet = FILENAME_BADCHARS.replace(allowed, '')
    for char in bet:
        text = text.replace(char, '')
    return text

def get_clipboard():
    import tkinter
    t = tkinter.Tk()
    clip = t.clipboard_get()
    t.destroy()
    return clip

def hashit(text, length=None):
    import hashlib
    h = hashlib.sha512(text.encode('utf-8')).hexdigest()
    if length is not None:
        h = h[:length]
    return h

def hook1(currentblock, chunksize, totalsize):
    currentbytes = currentblock * chunksize
    if currentbytes > totalsize:
        currentbytes = totalsize
    currentbytes = '{:,}'.format(currentbytes)
    totalsize = '{:,}'.format(totalsize)
    currentbytes = currentbytes.rjust(len(totalsize), ' ')
    print('%s / %s bytes' % (currentbytes, totalsize), end='\r')
    if currentbytes == totalsize:
        print()

def listget(l, index, default=None):
    try:
        return l[index]
    except IndexError:
        return default

def longest_length(li):
    longest = 0
    for item in li:
        longest = max(longest, len(item))
    return longest

def safeprint(text, **kwargs):
    text = str(text)
    text = text.encode('ascii', 'replace').decode()
    text = text.replace('?', '_')
    print(text, **kwargs)

def smart_insert(sql, cur, url=None, head=None, commit=True):
    '''
    INSERT or UPDATE the appropriate entry, or DELETE if the head
    shows a 403 / 404.
    '''
    if bool(url) is bool(head):
        raise ValueError('One and only one of `url` or `head` is necessary.')

    if url is not None:
        # When doing a basic scan, all we get is the URL.
        content_length = None
        content_type = None

    elif head is not None:
        # When doing a full scan, we get a Response object.
        if head.status_code in [403, 404]:
            cur.execute('DELETE FROM urls WHERE url == ?', [url])
            if commit:
                sql.commit()
            return (url, None, 0, None, 0)
        else:
            url = head.url
            content_length = head.headers.get('Content-Length', None)
            if content_length is not None:
                content_length = int(content_length)
            content_type = head.headers.get('Content-Type', None)

    basename = url_to_filepath(url)['filename']
    basename = urllib.parse.unquote(basename)
    do_download = True

    cur.execute('SELECT * FROM urls WHERE url == ?', [url])
    existing_entry = cur.fetchone()
    is_new = existing_entry is None

    data = (url, basename, content_length, content_type, do_download)
    if is_new:
        cur.execute('INSERT INTO urls VALUES(?, ?, ?, ?, ?)', data)
    else:
        print(url)
        command = '''
            UPDATE urls SET
            content_length = coalesce(?, content_length),
            content_type = coalesce(?, content_type)
            WHERE url == ?
        '''
        cur.execute(command, [content_length, content_type, url])

    if commit:
        sql.commit()
    return data

def url_to_filepath(text):
    text = urllib.parse.unquote(text)
    parts = urllib.parse.urlsplit(text)
    scheme = parts.scheme
    root = parts.netloc
    (folder, filename) = os.path.split(parts.path)
    while folder.startswith('/'):
        folder = folder[1:]

    # Folders are allowed to have slashes...
    folder = filepath_sanitize(folder, allowed='/\\')
    folder = folder.replace('\\', os.path.sep)
    folder = folder.replace('/', os.path.sep)
    # ...but Files are not.
    filename = filepath_sanitize(filename)

    result = {
        'scheme': scheme,
        'root': root,
        'folder': folder,
        'filename': filename,
    }
    return result

def write(line, file_handle=None):
    if file_handle is None:
        safeprint(line)
    else:
        file_handle.write(line + '\n')
##                                                                                                ##
## GENERAL FUNCTIONS ###############################################################################


## COMMANDLINE FUNCTIONS ###########################################################################
##                                                                                                ##
def digest(databasename, walkurl, fullscan=False):
    if walkurl in ('!clipboard', '!c'):
        walkurl = get_clipboard()
        safeprint('From clipboard: %s' % walkurl)
    walker = Walker(
        databasename=databasename,
        fullscan=fullscan,
        walkurl=walkurl,
    )
    walker.walk()

def digest_argparse(args):
    return digest(
        databasename=args.databasename,
        walkurl=args.walkurl,
        fullscan=args.fullscan,
    )

def download(databasename, outputdir=None, overwrite=False, bytespersecond=None):
    if isinstance(bytespersecond, str):
        bytespersecond = eval(bytespersecond)

    downloader = Downloader(
        databasename=databasename,
        outputdir=outputdir,
    )
    downloader.download(
        bytespersecond=bytespersecond,
        overwrite=overwrite,
    )

def download_argparse(args):
    return download(
        databasename=args.databasename,
        outputdir=args.outputdir,
        overwrite=args.overwrite,
        bytespersecond=args.bytespersecond,
    )

def filter_pattern(databasename, regex, action='keep', *trash):
    '''
    When `action` is 'keep', then any URLs matching the regex will have their
    `do_download` flag set to True.

    When `action` is 'remove', then any URLs matching the regex will have their
    `do_download` flag set to False.

    Actions will not act on each other's behalf. Keep will NEVER disable a url,
    and remove will NEVER enable one.
    '''
    import re
    if isinstance(regex, str):
        regex = [regex]

    keep = action == 'keep'
    remove = action == 'remove'

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur2 = sql.cursor()

    cur2.execute('SELECT * FROM urls')
    while True:
        fetch = cur2.fetchone()
        if fetch is None:
            break
        url = fetch[SQL_URL]
        current_do_dl = fetch[SQL_DO_DOWNLOAD]
        for pattern in regex:
            contains = re.search(pattern, url) is not None

            should_keep = (keep and contains)
            if keep and contains and not current_do_dl:
                safeprint('Enabling "%s"' % url)
                cur.execute('UPDATE urls SET do_download = 1 WHERE url == ?', [url])
            if remove and contains and current_do_dl:
                safeprint('Disabling "%s"' % url)
                cur.execute('UPDATE urls SET do_download = 0 WHERE url == ?', [url])
    sql.commit()

def keep_pattern_argparse(args):
    '''
    See `filter_pattern`.
    '''
    return filter_pattern(
        action='keep',
        databasename=args.databasename,
        regex=args.regex,
    )

def list_basenames(databasename, output_filename=None):
    '''
    Print the Enabled entries in order of the file basenames.
    This makes it easier to find interesting titles without worrying about
    what directory they're in.
    '''
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()

    cur.execute('SELECT * FROM urls WHERE do_download == 1')
    items = cur.fetchall()
    longest = max(items, key=lambda x: len(x[SQL_BASENAME]))
    longest = len(longest[SQL_BASENAME])
    items.sort(key=lambda x: x[SQL_BASENAME].lower())

    if output_filename is not None:
        output_file = open(output_filename, 'w', encoding='utf-8')
    else:
        output_file = None

    form = '{basename:<%ds}  :  {url}  :  {size}' % longest
    for item in items:
        size = item[SQL_CONTENT_LENGTH]
        if size is None:
            size = ''
        else:
            size = bytestring.bytestring(size)
        line = form.format(
            basename=item[SQL_BASENAME],
            url=item[SQL_URL],
            size=size,
        )
        write(line, output_file)

    if output_file:
        output_file.close()

def list_basenames_argparse(args):
    return list_basenames(
        databasename=args.databasename,
        output_filename=args.outputfile,
    )

def measure(databasename, fullscan=False, new_only=False):
    '''
    Given a database, print the sum of all Content-Lengths.
    URLs will be HEAD requested if:
        `new_only` is True and the file has no stored content length, or
        `fullscan` is True and `new_only` is False
    '''
    if isinstance(fullscan, str):
        fullscan = bool(fullscan)

    totalsize = 0
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()

    if new_only:
        cur.execute('SELECT * FROM urls WHERE do_download == 1 AND content_length IS NULL')
    else:
        cur.execute('SELECT * FROM urls WHERE do_download == 1')

    items = cur.fetchall()

    filecount = 0
    unmeasured_file_count = 0
    try:
        for fetch in items:
            size = fetch[SQL_CONTENT_LENGTH]

            if fullscan or new_only:
                url = fetch[SQL_URL]
                head = do_head(url, raise_for_status=False)
                fetch = smart_insert(sql, cur, head=head, commit=True)
                size = fetch[SQL_CONTENT_LENGTH]
                if size is None:
                    safeprint('"%s" is not revealing Content-Length' % url)
                    size = 0


            elif fetch[SQL_CONTENT_LENGTH] is None:
                unmeasured_file_count += 1
                size = 0

            totalsize += size
            filecount += 1
    except:
        sql.commit()
        raise

    sql.commit()
    short_string = bytestring.bytestring(totalsize)
    totalsize_string = '{} ({:,} bytes) in {:,} files'.format(short_string, totalsize, filecount)
    print(totalsize_string)
    if unmeasured_file_count > 0:
        print(UNMEASURED_WARNING % unmeasured_file_count)
    return totalsize

def measure_argparse(args):
    return measure(
        databasename=args.databasename,
        fullscan=args.fullscan,
        new_only=args.new_only,
    )

def remove_pattern_argparse(args):
    '''
    See `filter_pattern`.
    '''
    return filter_pattern(
        action='remove',
        databasename=args.databasename,
        regex=args.regex,
    )

def tree(databasename, output_filename=None):
    '''
    Print a tree diagram of the directory-file structure.

    If an .html file is given for `output_filename`, the page will have
    collapsible boxes and clickable filenames. Otherwise the file will just
    be a plain text drawing.
    '''

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur.execute('SELECT * FROM urls WHERE do_download == 1')
    items = cur.fetchall()
    if len(items) == 0:
        return

    items.sort(key=lambda x: x[SQL_URL])

    path_parts = url_to_filepath(items[0][SQL_URL])
    root_identifier = path_parts['root']
    #print('Root', root_identifier)
    root_data = {'name': root_identifier, 'item_type': 'directory'}
    root_identifier = root_identifier.replace(':', '')
    tree = TreeNode(
        identifier=root_identifier,
        data=root_data
    )
    node_map = {}

    unmeasured_file_count = 0

    for item in items:
        path = url_to_filepath(item[SQL_URL])
        scheme = path['scheme']

        # I join and re-split because 'folder' may contain slashes of its own
        # and I want to break all the pieces
        path = '\\'.join([path['root'], path['folder'], path['filename']])
        parts = path.split('\\')
        #print(path)
        for (index, part) in enumerate(parts):
            this_path = '/'.join(parts[:index + 1])
            parent_path = '/'.join(parts[:index])
            #safeprint('this:' + this_path)
            #safeprint('parent:' + parent_path)

            #input()
            data = {
                'name': part,
                'url': scheme + '://' + this_path,
            }
            this_identifier = this_path.replace(':', '')
            parent_identifier = parent_path.replace(':', '')

            if (index + 1) == len(parts):
                data['item_type'] = 'file'
                if item[SQL_CONTENT_LENGTH]:
                    data['size'] = item[SQL_CONTENT_LENGTH]
                else:
                    unmeasured_file_count += 1
                    data['size'] = None
            else:
                data['item_type'] = 'directory'


            # Ensure this comment is in a node of its own
            this_node = node_map.get(this_identifier, None)
            if this_node:
                # This ID was detected as a parent of a previous iteration
                # Now we're actually filling it in.
                this_node.data = data
            else:
                this_node = TreeNode(this_identifier, data)
                node_map[this_identifier] = this_node

            # Attach this node to the parent.
            if parent_identifier == root_identifier:
                try:
                    tree.add_child(this_node)
                except TreeExistingChild:
                    pass
            else:
                parent_node = node_map.get(parent_identifier, None)
                if not parent_node:
                    parent_node = TreeNode(parent_identifier, data=None)
                    node_map[parent_identifier] = parent_node
                try:
                    parent_node.add_child(this_node)
                except TreeExistingChild:
                    pass
                this_node.parent = parent_node
            #print(this_node.data)

    def recursive_get_size(node):
        size = node.data.get('size', 0)
        if size:
            # Files have this attribute, dirs don't
            return size

        for child in node.children.values():
            child_size = recursive_get_size(child)
            child_size = child_size or 0
            size += child_size
        node.data['size'] = size
        return size

    def recursive_print_node(node, depth=0, output_file=None):
        size = node.data['size']
        if size is None:
            size = UNKNOWN_SIZE_STRING
        else:
            size = bytestring.bytestring(size)

        if use_html:
            if depth % 2 == 0:
                css_class = 'directory_even'
            else:
                css_class = 'directory_odd'

            if node.data['item_type'] == 'directory':
                div_id = hashit(node.identifier, 16)
                line = '<button onclick="collapse(\'{div_id}\')">{name} ({size})</button>'
                line += '<div class="%s" id="{div_id}" style="display:none">' % css_class
                line = line.format(
                    div_id=div_id,
                    name=node.data['name'],
                    size=size,
                )
            else:
                line = '<a href="{url}">{name} ({size})</a><br>'
                line = line.format(
                    url=node.data['url'],
                    name=node.data['name'],
                    size=size,
                )
        else:
            line = '{space}{bar}{name} : ({size})'
            line = line.format(
                space='|   '*(depth-1),
                bar='|---' if depth > 0 else '',
                name=node.data['name'],
                size=size
            )
        write(line, output_file)

        # Sort by type (directories first) then subsort by lowercase path
        customsort = lambda x: (
            node.children[x].data['item_type'] == 'file',
            node.children[x].data['url'].lower(),
        )

        for (key, child) in node.sorted_children(customsort=customsort):
            recursive_print_node(child, depth=depth+1, output_file=output_file)

        if node.data['item_type'] == 'directory':
            if use_html:
                write('</div>', output_file)
            else:
                # This helps put some space between sibling directories
                write('|   ' * (depth), output_file)


    if output_filename is not None:
        output_file = open(output_filename, 'w', encoding='utf-8')
        use_html = output_filename.lower().endswith('.html')
    else:
        output_file = None
        use_html = False


    if use_html:
        write(HTML_TREE_HEADER, file_handle=output_file)

    recursive_get_size(tree)
    recursive_print_node(tree, output_file=output_file)
    if unmeasured_file_count > 0:
        write(UNMEASURED_WARNING % unmeasured_file_count, file_handle=output_file)

    if output_file is not None:
        output_file.close()
    return tree

def tree_argparse(args):
    return tree(
        databasename=args.databasename,
        output_filename=args.outputfile,
    )

##                                                                                                ##
## COMMANDLINE FUNCTIONS ###########################################################################

def main(argv):
    if listget(argv, 1, '').lower() in ('help', '-h', '--help', ''):
        print(DOCSTRING)
        return
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_digest = subparsers.add_parser('digest')
    p_digest.add_argument('walkurl')
    p_digest.add_argument('-db', '--database', dest='databasename', default=None)
    p_digest.add_argument('-f', '--fullscan', dest='fullscan', action='store_true')
    p_digest.set_defaults(func=digest_argparse)

    p_download = subparsers.add_parser('download')
    p_download.add_argument('databasename')
    p_download.add_argument('-o', '--outputdir', dest='outputdir', default=None)
    p_download.add_argument('-bps', '--bytespersecond', dest='bytespersecond', default=None)
    p_download.add_argument('-ow', '--overwrite', dest='overwrite', action='store_true')
    p_download.set_defaults(func=download_argparse)

    p_keep_pattern = subparsers.add_parser('keep_pattern')
    p_keep_pattern.add_argument('databasename')
    p_keep_pattern.add_argument('regex')
    p_keep_pattern.set_defaults(func=keep_pattern_argparse)

    p_list_basenames = subparsers.add_parser('list_basenames')
    p_list_basenames.add_argument('databasename')
    p_list_basenames.add_argument('-o', '--outputfile', dest='outputfile', default=None)
    p_list_basenames.set_defaults(func=list_basenames_argparse)

    p_measure = subparsers.add_parser('measure')
    p_measure.add_argument('databasename')
    p_measure.add_argument('-f', '--fullscan', dest='fullscan', action='store_true')
    p_measure.add_argument('-n', '--new_only', dest='new_only', action='store_true')
    p_measure.set_defaults(func=measure_argparse)

    p_remove_pattern = subparsers.add_parser('remove_pattern')
    p_remove_pattern.add_argument('databasename')
    p_remove_pattern.add_argument('regex')
    p_remove_pattern.set_defaults(func=remove_pattern_argparse)

    p_tree = subparsers.add_parser('tree')
    p_tree.add_argument('databasename')
    p_tree.add_argument('-o', '--outputfile', dest='outputfile', default=None)
    p_tree.set_defaults(func=tree_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
