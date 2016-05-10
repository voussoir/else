'''
OpenDirDL
downloads open directories

Usage:

DIGEST:
    Recursively fetch directories and build a database of file URLs.

    > opendirdl digest !clipboard <flags>
    > opendirdl digest http://website.com/directory/ <flags>

    flags:
    -f | --fullscan:
        When included, perform HEAD requests on all files, to know the size of the entire directory.

    -db "x.db" | --databasename "x.db":
        Use a custom database filename. By default, databases are named after the web domain.

DOWNLOAD:
    Download the files whose URLs are enabled in the database.

    > opendirdl download website.com.db <flags>

    flags:
    -o "x" | --outputdir "x":
        Save the files to a custom directory, "x". By default, files are saved to a folder named
        after the web domain.

    -ow | --overwrite:
        When included, download and overwrite files even if they already exist in the output directory.

    -bps 100 | --bytespersecond 100:
        Ratelimit yourself to downloading at 100 BYTES per second. The webmaster will appreciate this.

KEEP_PATTERN:
    Enable URLs which match a regex pattern. Matches are based on the percent-encoded strings!

    > opendirdl keep_pattern website.com.db ".*"

REMOVE_PATTERN:
    Disable URLs which match a regex pattern. Matches are based on the percent-encoded strings!

    > opendirdl remove_pattern website.com.db ".*"

LIST_BASENAMES:
    List enabled URLs in order of their base filename. This makes it easier to find titles of
    interest in a directory that is very scattered or poorly organized.

    > opendirdl list_basenames website.com.db <flags>

    flags:
    -o "x.txt" | --outputfile "x.txt":
        Output the results to a file instead of stdout. This is useful if the filenames contain
        special characters that crash Python, or are so long that the console becomes unreadable.

MEASURE:
    Sum up the filesizes of all enabled URLs.

    > opendirdl measure website.com.db <flags>

    flags:
    -f | --fullscan:
        When included, perform HEAD requests on any URL whose size is not known. If this flag is
        not included, and some file's size is unkown, you will receive a printed note.
'''

# Module names preceeded by two hashes indicate modules that are imported during
# a function, because they are not used anywhere else and we don't need to waste
# time importing them usually.

import sys

sys.path.append('C:\\git\\else\\ratelimiter'); import ratelimiter

import argparse
## import bs4
## import hashlib
import os
## import re
import requests
import shutil
import sqlite3
## tkinter
import urllib.parse

FILENAME_BADCHARS = '/\\:*?"<>|'

TERMINAL_WIDTH = shutil.get_terminal_size().columns

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
'.webm',
'.wma',
'.zip',
]
SKIPPABLE_FILETYPES = set(x.lower() for x in SKIPPABLE_FILETYPES)

BYTE = 1
KIBIBYTE = 1024 * BYTE
MIBIBYTE = 1024 * KIBIBYTE
GIBIBYTE = 1024 * MIBIBYTE
TEBIBYTE = 1024 * GIBIBYTE
SIZE_UNITS = (TEBIBYTE, GIBIBYTE, MIBIBYTE, KIBIBYTE, BYTE)

UNIT_STRINGS = {
    BYTE: 'b',
    KIBIBYTE: 'KiB',
    MIBIBYTE: 'MiB',
    GIBIBYTE: 'GiB',
    TEBIBYTE: 'TiB',
}

DOWNLOAD_CHUNK = 2 * KIBIBYTE


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
            # returns (root, path, filename). Keep root.
            outputdir = url_to_filepath(url)[0]
        self.outputdir = outputdir

    def download(self, overwrite=False, bytespersecond=None):
        overwrite = bool(overwrite)

        self.cur.execute('SELECT * FROM urls WHERE do_download == 1 ORDER BY url')
        while True:
            fetch = self.cur.fetchone()
            if fetch is None:
                break
            url = fetch[SQL_URL]

            ''' Creating the Path '''
            (root, folder, basename) = url_to_filepath(url)
            # Ignore this value of `root`, because we might have a custom outputdir.
            root = self.outputdir
            folder = os.path.join(root, folder)
            os.makedirs(folder, exist_ok=True)
            fullname = os.path.join(folder, basename)
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


## GENERIC #########################################################################################
##                                                                                                ##
class Generic:
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
##                                                                                                ##
## GENERIC #########################################################################################


## WALKER ##########################################################################################
##                                                                                                ##
class Walker:
    def __init__(self, walkurl, databasename=None, fullscan=False):
        if walkurl[-1] != '/':
            walkurl += '/'
        self.walkurl = walkurl
        if databasename is None or databasename == "":
            self.domain = url_to_filepath(walkurl)[0]
            databasename = self.domain + '.db'
            databasename = databasename.replace(':', '')
        self.databasename = databasename

        self.sql = sqlite3.connect(self.databasename)
        self.cur = self.sql.cursor()
        db_init(self.sql, self.cur)

        self.fullscan = bool(fullscan)
        self.queue = []
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
        soup = bs4.BeautifulSoup(response.text)
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
            if 'C=' in href and 'O=' in href:
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

        if content_type.startswith('text/html') and head.url.endswith('/'):
            # This is an index page, so extract links and queue them.
            response = do_get(url)
            hrefs = self.extract_hrefs(response)
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
        self.queue.append(url)
        try:
            while len(self.queue) > 0:
                # Popping from right helps keep the queue short because it handles the files
                # early.
                url = self.queue.pop(-1)
                self.process_url(url)
                line = '{:,} Remaining'.format(len(self.queue))
                print(line)
        except:
            self.sql.commit()
            raise
        self.sql.commit()
##                                                                                                ##
## WALKER ##########################################################################################


## GENERAL FUNCTIONS ###############################################################################
##                                                                                                ##
def bytes_to_unit_string(bytes):
    size_unit = 1
    for unit in SIZE_UNITS:
        if bytes >= unit:
            size_unit = unit
            break
    size_unit_string = UNIT_STRINGS[size_unit]
    size_string = '%.3f %s' % ((bytes / size_unit), size_unit_string)
    return size_string

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

def do_get(url):
    return do_request('GET', requests.get, url)

def do_head(url):
    return do_request('HEAD', requests.head, url)

def do_request(message, method, url):
    import sys
    message = '{message:>4s}: {url} : '.format(message=message, url=url)
    safeprint(message, end='')
    sys.stdout.flush()
    response = method(url)
    safeprint(response.status_code)
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
    INSERT or UPDATE the appropriate entry.
    '''
    if bool(url) is bool(head):
        raise ValueError('One and only one of `url` or `head` is necessary.')

    if url is not None:
        # When doing a basic scan, all we get is the URL.
        content_length = None
        content_type = None

    elif head is not None:
        # When doing a full scan, we get a Response object.
        url = head.url
        content_length = head.headers.get('Content-Length', None)
        if content_length is not None:
            content_length = int(content_length)
        content_type = head.headers.get('Content-Type', None)

    basename = url_to_filepath(url)[2]
    basename = urllib.parse.unquote(basename)
    do_download = True
    cur.execute('SELECT * FROM urls WHERE url == ?', [url])
    existing_entry = cur.fetchone()
    is_new = existing_entry is None
    data = (url, basename, content_length, content_type, do_download)
    if is_new:
        
        cur.execute('INSERT INTO urls VALUES(?, ?, ?, ?, ?)', data)
    else:
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

    return (root, folder, filename)
##                                                                                                ##
## GENERAL FUNCTIONS ###############################################################################


## COMMANDLINE FUNCTIONS ###########################################################################
##                                                                                                ##
def digest(args):
    fullscan = args.fullscan
    if isinstance(fullscan, str):
        fullscan = bool(eval(fullscan))
    walkurl = args.walkurl
    if walkurl == '!clipboard':
        walkurl = get_clipboard()
        safeprint('From clipboard: %s' % walkurl)
    walker = Walker(
        databasename=args.databasename,
        fullscan=fullscan,
        walkurl=walkurl,
        )
    walker.walk()

def download(args):
    bytespersecond = args.bytespersecond
    if isinstance(bytespersecond, str):
        bytespersecond = eval(bytespersecond)

    downloader = Downloader(
        databasename=args.databasename,
        outputdir=args.outputdir,
        )
    downloader.download(
        bytespersecond=bytespersecond,
        overwrite=args.overwrite,
        )

def filter_pattern(databasename, regex, action='keep', *trash):
    '''
    When `action` is 'keep', then any URLs matching the regex will have their
    `do_download` flag set to True.

    When `action` is 'remove', then any URLs matching the regex will have their
    `do_download` flag set to False.

    Actions will not act on each other's behalf. A 'keep' will NEVER disable a url,
    and 'remove' will NEVER enable one.
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
                safeprint('Keeping "%s"' % url)
                cur.execute('UPDATE urls SET do_download = 1 WHERE url == ?', [url])
            if remove and contains and current_do_dl:
                safeprint('Removing "%s"' % url)
                cur.execute('UPDATE urls SET do_download = 0 WHERE url == ?', [url])
    sql.commit()

def keep_pattern(args):
    '''
    See `filter_pattern`.
    '''
    filter_pattern(
        action='keep',
        databasename=args.databasename,
        regex=args.regex,
        )

def list_basenames(args):
    '''
    Given a database, print the entries in order of the file basenames.
    This makes it easier to find interesting titles without worrying about
    what directory they're in.
    '''
    databasename = args.databasename
    outputfile = args.outputfile

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur.execute('SELECT basename FROM urls WHERE do_download == 1 ORDER BY LENGTH(basename) DESC LIMIT 1')

    fetch = cur.fetchone()
    if fetch is None:
        return
    longest = len(fetch[0])
    cur.execute('SELECT * FROM urls WHERE do_download == 1 ORDER BY LOWER(basename)')
    form = '{bn:<%ds}  :  {url}  :  {byt}' % longest
    if outputfile:
        outputfile = open(outputfile, 'w', encoding='utf-8')
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        byt = fetch[SQL_CONTENT_LENGTH]
        if byt is None:
            byt = ''
        else:
            byt = '{:,}'.format(byt)
        line = form.format(bn=fetch[SQL_BASENAME], url=fetch[SQL_URL], byt=byt)
        if outputfile:
            outputfile.write(line + '\n')
        else:
            print(line)
    if outputfile:
        outputfile.close()

def measure(args):
    '''
    Given a database, print the sum of all Content-Lengths.
    If `fullscan`, then URLs with no Content-Length will be
    HEAD requested, and the result will be saved back into the file.
    '''
    databasename = args.databasename
    fullscan = args.fullscan
    if isinstance(fullscan, str):
        fullscan = bool(fullscan)

    totalsize = 0
    sql = sqlite3.connect(databasename)
    cur1 = sql.cursor()
    cur2 = sql.cursor()
    cur2.execute('SELECT * FROM urls WHERE do_download == 1')
    filecount = 0
    files_without_size = 0
    try:
        while True:
            fetch = cur2.fetchone()
            if fetch is None:
                break
            size = fetch[SQL_CONTENT_LENGTH]
            if size is None:
                if fullscan:
                    url = fetch[SQL_URL]
                    head = do_head(url)
                    fetch = smart_insert(sql, cur1, head=head, commit=False)
                    size = fetch[SQL_CONTENT_LENGTH]
                    if size is None:
                        safeprint('"%s" is not revealing Content-Length' % url)
                        size = 0
                else:
                    files_without_size += 1
                    size = 0
            totalsize += size
            filecount += 1
    except:
        sql.commit()
        raise

    sql.commit()
    short_string = bytes_to_unit_string(totalsize)
    totalsize_string = '{} ({:,} bytes) in {:,} files'.format(short_string, totalsize, filecount)
    print(totalsize_string)
    if files_without_size > 0:
        print('Note: %d files do not have a stored Content-Length.' % files_without_size)
        print('Run `measure` with `-f` or `--fullscan` to HEAD request those files.')
    return totalsize

def remove_pattern(args):
    '''
    See `filter_pattern`.
    '''
    filter_pattern(
        action='remove',
        databasename=args.databasename,
        regex=args.regex,
        )
##                                                                                                ##
## COMMANDLINE FUNCTIONS ###########################################################################


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_digest = subparsers.add_parser('digest')
    p_digest.add_argument('walkurl')
    p_digest.add_argument('-db', '--database', dest='databasename', default=None)
    p_digest.add_argument('-f', '--fullscan', action='store_true')
    p_digest.set_defaults(func=digest)

    p_download = subparsers.add_parser('download')
    p_download.add_argument('databasename')
    p_download.add_argument('-o', '--outputdir', dest='outputdir', default=None)
    p_download.add_argument('-ow', '--overwrite', dest='overwrite', default=False)
    p_download.add_argument('-bps', '--bytespersecond', dest='bytespersecond', default=None)
    p_download.set_defaults(func=download)

    p_keep_pattern = subparsers.add_parser('keep_pattern')
    p_keep_pattern.add_argument('databasename')
    p_keep_pattern.add_argument('regex')
    p_keep_pattern.set_defaults(func=keep_pattern)

    p_list_basenames = subparsers.add_parser('list_basenames')
    p_list_basenames.add_argument('databasename')
    p_list_basenames.add_argument('-o', '--outputfile', dest='outputfile', default=None)
    p_list_basenames.set_defaults(func=list_basenames)

    p_measure = subparsers.add_parser('measure')
    p_measure.add_argument('databasename')
    p_measure.add_argument('-f', '--fullscan', action='store_true')
    p_measure.set_defaults(func=measure)

    p_remove_pattern = subparsers.add_parser('remove_pattern')
    p_remove_pattern.add_argument('databasename')
    p_remove_pattern.add_argument('regex')
    p_remove_pattern.set_defaults(func=remove_pattern)

    args = parser.parse_args()
    args.func(args)
