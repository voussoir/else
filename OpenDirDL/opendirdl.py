# voussoir
'''
OpenDirDL
downloads open directories

The basics:
1. Create a database of the directory's files with
    > opendirdl digest http://website.com/directory/
2. Enable and disable the files you are interested in with
    > opendirdl website.com.db remove_pattern ".*"
    > opendirdl website.com.db keep_pattern "Daft%20Punk"
    > opendirdl website.com.db remove_pattern "folder\.jpg"
   Note the percent-encoded string.
3. Download the enabled files with
    > opendirdl website.com.db download


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
    -bps 100k | -bps "100 kb" | -bps 100kib | -bps 1.2m
        Ratelimit your download speed. Supports units like "k", "m" according
        to `bytestring.parsebytes`.

keep_pattern:
    Enable URLs which match a regex pattern. Matches are based on the percent-
    encoded strings!

    > opendirdl keep_pattern website.com.db ".*"

remove_pattern:
    Disable URLs which match a regex pattern. Matches are based on the percent-
    encoded strings!

    > opendirdl remove_pattern website.com.db ".*"

list_basenames:
    List Enabled URLs alphabetized by their base filename. This makes it easier
    to find titles of interest in a directory that is very scattered or poorly
    organized.

    > opendirdl list_basenames website.com.db <flags>

    flags:
    -o "x.txt" | --outputfile "x.txt":
        Output the results to a file instead of stdout. This is useful if the
        filenames contain special characters that crash Python, or are so long
        that the console becomes unreadable.

list_urls:
    List Enabled URLs in alphabetical order. No stylization, just dumped.

    > opendirdl list_urls website.com.db <flags>

    flags:
    -o "x.txt" | --outputfile "x.txt":
        Output the results to a file instead of stdout.

measure:
    Sum up the filesizes of all Enabled URLs.

    > opendirdl measure website.com.db <flags>

    flags:
    -f | --fullscan:
        When included, perform HEAD requests on all files to update their size.

    -n | --new_only:
        When included, perform HEAD requests only on files that haven't gotten
        one yet.

    -t 4 | --threads 4:
        The number of threads to use for performing requests.

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


# Module names preceeded by `## ` indicate modules that are imported during
# a function, because they are not used anywhere else and we don't need to waste
# time importing them usually, but I still want them listed here for clarity.
import argparse
## import bs4
import collections
import concurrent.futures
## import hashlib
import os
## import re
import requests
import shutil
import sqlite3
import sys
import threading
import time
## import tkinter
import urllib.parse

# pip install voussoirkit
from voussoirkit import bytestring
from voussoirkit import downloady
from voussoirkit import fusker
from voussoirkit import treeclass
import pathtree
sys.path.append('D:\\git\\else\\threadqueue'); import threadqueue

DOWNLOAD_CHUNK = 16 * bytestring.KIBIBYTE
FILENAME_BADCHARS = '/\\:*?"<>|'
TERMINAL_WIDTH = shutil.get_terminal_size().columns

# When doing a basic scan, we will not send HEAD requests to URLs that end in
# these strings, because they're probably files.
# This isn't meant to be a comprehensive filetype library, but it covers
# enough of the typical opendir to speed things up.
SKIPPABLE_FILETYPES = [
    '.3gp',
    '.7z',
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
    '.sfv',
    '.srt',
    '.tar',
    '.ttf',
    '.txt',
    '.wav',
    '.webm',
    '.wma',
    '.xml',
    '.zip',
]
SKIPPABLE_FILETYPES = set(x.lower() for x in SKIPPABLE_FILETYPES)
SKIPPABLE_FILETYPES.update(fusker.fusker('.r[0-99]'))
SKIPPABLE_FILETYPES.update(fusker.fusker('.r[00-99]'))
SKIPPABLE_FILETYPES.update(fusker.fusker('.r[000-099]'))
SKIPPABLE_FILETYPES.update(fusker.fusker('.[00-99]'))

# Will be ignored completely. Are case-sensitive
BLACKLISTED_FILENAMES = [
    'desktop.ini',
    'thumbs.db',
]

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
    '''
    This class manages the extraction and saving of URLs, given a starting root url.
    '''
    def __init__(self, root_url, databasename=None, fullscan=False, threads=1):
        if not root_url.endswith('/'):
            root_url += '/'
        if '://' not in root_url.split('.')[0]:
            root_url = 'http://' + root_url
        self.root_url = root_url

        if databasename in (None, ''):
            domain = url_split(self.root_url)['domain']
            databasename = domain + '.db'
            databasename = databasename.replace(':', '#')
        self.databasename = databasename

        write('Opening %s' % self.databasename)
        self.sql = sqlite3.connect(self.databasename)
        self.cur = self.sql.cursor()
        db_init(self.sql, self.cur)

        self.thread_queue = threadqueue.ThreadQueue(threads)
        self._main_thread = threading.current_thread().ident
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
        External links, index sort links, and blacklisted files are discarded.
        '''
        import bs4
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        elements = soup.find_all(tag)
        for element in elements:
            try:
                href = element[attribute]
            except KeyError:
                continue
            href = urllib.parse.urljoin(response.url, href)

            if href.startswith('javascript:'):
                continue

            if not href.startswith(self.root_url):
                # Don't go to other sites or parent directories.
                continue

            if any(sorter in href for sorter in ('?C=', '?O=', '?M=', '?D=', '?N=', '?S=')):
                # Alternative sort modes for index pages.
                continue

            if any(href.endswith(blacklisted) for blacklisted in BLACKLISTED_FILENAMES):
                continue

            yield href

    def process_url(self, url=None):
        '''
        Given a URL, check whether it is an index page or an actual file.
        If it is an index page, its links are extracted and queued.
        If it is a file, its information is saved to the database.

        We perform a
        HEAD:
            when `self.fullscan` is True.
            when `self.fullscan` is False but the url is not a SKIPPABLE_FILETYPE.
            when the url is an index page.
        GET:
            when the url is an index page.
        '''
        if url is None:
            url = self.root_url
        else:
            url = urllib.parse.urljoin(self.root_url, url)

        if url in self.seen_directories:
            # We already picked this up at some point
            return

        # if not url.startswith(self.root_url):
        #     # Don't follow external links or parent directory.
        #     write('Skipping "%s" due to external url.' % url)
        #     return

        urll = url.lower()
        if self.fullscan is False:
            skippable = any(urll.endswith(ext) for ext in SKIPPABLE_FILETYPES)
            if skippable:
                write('Skipping "%s" due to extension.' % url)
                #self.smart_insert(url=url, commit=False)
                #return {'url': url, 'commit': False}
                self.thread_queue.behalf(self._main_thread, self.smart_insert, url=url, commit=False)
                return
            skippable = lambda: self.cur.execute('SELECT * FROM urls WHERE url == ?', [url]).fetchone()
            skippable = self.thread_queue.behalf(self._main_thread, skippable)
            #print(skippable)
            skippable = skippable is not None
            #skippable = self.cur.fetchone() is not None
            if skippable:
                write('Skipping "%s" since we already have it.' % url)
                return

        try:
            head = do_head(url)
        except requests.exceptions.HTTPError as exception:
            if exception.response.status_code == 403:
                write('403 FORBIDDEN!')
                return
            if exception.response.status_code == 404:
                write('404 NOT FOUND!')
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
                    #self.queue.append(href)
                    self.thread_queue.add(self.process_url, href)
                    added += 1
            write('Queued %d urls' % added)
        else:
            # This is not an index page, so save it.
            #self.smart_insert(head=head, commit=False)
            self.thread_queue.behalf(self._main_thread, self.smart_insert, head=head, commit=False)
            #return {'head': head, 'commit': False}

    def walk(self, url=None):
        '''
        Given a starting URL (defaults to self.root_url), continually extract
        links from the page and repeat.
        '''
        #self.queue.appendleft(url)
        try:
            self.thread_queue.add(self.process_url, url)
            for return_value in self.thread_queue.run(hold_open=False):
                pass
        except KeyboardInterrupt:
            self.sql.commit()
            raise
        else:
            self.sql.commit()
##                                                                                                ##
## WALKER ##########################################################################################


## GENERAL FUNCTIONS ###############################################################################
##                                                                                                ##
def build_file_tree(databasename):
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()
    cur.execute('SELECT * FROM urls WHERE do_download == 1')
    fetch_all = cur.fetchall()
    sql.close()

    if len(fetch_all) == 0:
        return

    path_datas = []
    # :|| is my temporary (probably not temporary) hack for including the URL
    # scheme without causing the pathtree processor to think there's a top
    # level directory called 'http'.
    # It will be replaced with :// in the calling `tree` function.
    path_form = '{scheme}:||{domain}\\{folder}\\{filename}'
    for item in fetch_all:
        url = item[SQL_URL]
        size = item[SQL_CONTENT_LENGTH]
        path_parts = url_split(item[SQL_URL])
        path = path_form.format(**path_parts)
        path = urllib.parse.unquote(path)
        path_data = {'path': path, 'size': size, 'data': url}
        path_datas.append(path_data)

    return pathtree.from_paths(path_datas, root_name=databasename)

def db_init(sql, cur):
    lines = DB_INIT.split(';')
    for line in lines:
        cur.execute(line)
    sql.commit()
    return True

def do_get(url, raise_for_status=True):
    return do_request('GET', requests.get, url, raise_for_status=raise_for_status)

def do_head(url, raise_for_status=True):
    return do_request('HEAD', requests.head, url, raise_for_status=raise_for_status)

def do_request(message, method, url, raise_for_status=True):
    form = '{message:>4s}: {url} : {status}'
    write(form.format(message=message, url=url, status=''))
    while True:
        try:
            response = method(url)
            break
        except requests.exceptions.ConnectionError:
            pass
    write(form.format(message=message, url=url, status=response.status_code))
    if raise_for_status:
        response.raise_for_status()
    return response

def fetch_generator(cur):
    while True:
        fetch = cur.fetchone()
        if fetch is None:
            break
        yield fetch

def filepath_sanitize(text, allowed=''):
    '''
    Remove forbidden characters from the text, unless specifically sanctioned.
    '''
    badchars = FILENAME_BADCHARS
    badchars = set(char for char in FILENAME_BADCHARS if char not in allowed)
    text = ''.join(char for char in text if char not in badchars)
    return text

def get_clipboard():
    import tkinter
    t = tkinter.Tk()
    clip = t.clipboard_get()
    t.destroy()
    return clip

def hashit(text, length=None):
    import hashlib
    sha = hashlib.sha512(text.encode('utf-8')).hexdigest()
    if length is not None:
        sha = sha[:length]
    return sha

def int_none(x):
    if x is None:
        return x
    return int(x)

def promise_results(promises):
    promises = promises[:]
    while len(promises) > 0:
        for (index, promise) in enumerate(promises):
            if not promise.done():
                continue
            yield promise.result()
            promises.pop(index)
            break

def safeindex(sequence, index, fallback=None):
    try:
        return sequence[index]
    except IndexError:
        return fallback

def safeprint(*texts, **kwargs):
    texts = [str(text).encode('ascii', 'replace').decode() for text in texts]
    print(*texts, **kwargs)

def smart_insert(sql, cur, url=None, head=None, commit=True):
    '''
    INSERT or UPDATE the appropriate entry, or DELETE if the head
    shows a 403 / 404.
    '''
    if bool(url) is bool(head) and not isinstance(head, requests.Response):
        raise ValueError('One and only one of `url` or `head` is necessary.')

    if url is not None:
        # When doing a basic scan, all we get is the URL.
        content_length = None
        content_type = None

    elif head is not None:
        url = head.url
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

    basename = url_split(url)['filename']
    #basename = urllib.parse.unquote(basename)
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

def url_split(url):
    '''
    Given a url, return a dictionary of its components.
    '''
    #url = urllib.parse.unquote(url)
    parts = urllib.parse.urlsplit(url)
    if any(part == '' for part in [parts.scheme, parts.netloc]):
        raise ValueError('Not a valid URL')
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
        'domain': urllib.parse.unquote(root),
        'folder': urllib.parse.unquote(folder),
        'filename': urllib.parse.unquote(filename),
    }
    return result

def write(line, file_handle=None, **kwargs):
    if file_handle is None:
        safeprint(line, **kwargs)
    else:
        file_handle.write(line + '\n', **kwargs)
##                                                                                                ##
## GENERAL FUNCTIONS ###############################################################################


## COMMANDLINE FUNCTIONS ###########################################################################
##                                                                                                ##
def digest(root_url, databasename=None, fullscan=False, threads=1):
    if root_url in ('!clipboard', '!c'):
        root_url = get_clipboard()
        write('From clipboard: %s' % root_url)
    walker = Walker(
        databasename=databasename,
        fullscan=fullscan,
        root_url=root_url,
        threads=threads,
    )
    walker.walk()

def digest_argparse(args):
    return digest(
        databasename=args.databasename,
        fullscan=args.fullscan,
        root_url=args.root_url,
        threads=int(args.threads),
    )

def download(
        databasename,
        outputdir=None,
        bytespersecond=None,
        headers=None,
        overwrite=False,
    ):
    '''
    Download all of the Enabled files. The filepaths will match that of the
    website, using `outputdir` as the root directory.

    Parameters:
        outputdir:
            The directory to mirror the files into. If not provided, the domain
            name is used.

        bytespersecond:
            The speed to ratelimit the downloads. Can be an integer, or a string like
            '500k', according to the capabilities of `bytestring.parsebytes`

            Note that this is bytes, not bits.

        headers:
            Additional headers to pass to each `download_file` call.

        overwrite:
            If True, delete local copies of existing files and rewrite them.
            Otherwise, completed files are skipped.
    '''
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()

    if outputdir in (None, ''):
        # This assumes that all URLs in the database are from the same domain.
        # If they aren't, it's the user's fault because Walkers don't leave the given site
        # on their own.
        cur.execute('SELECT url FROM urls LIMIT 1')
        url = cur.fetchone()[0]
        outputdir = url_split(url)['domain']
        outputdir = outputdir.replace(':', '#')

    if isinstance(bytespersecond, str):
        bytespersecond = bytestring.parsebytes(bytespersecond)

    cur.execute('SELECT * FROM urls WHERE do_download == 1 ORDER BY url')
    for fetch in fetch_generator(cur):
        url = fetch[SQL_URL]

        url_filepath = url_split(url)
        folder = os.path.join(outputdir, url_filepath['folder'])
        os.makedirs(folder, exist_ok=True)

        fullname = os.path.join(folder, url_filepath['filename'])

        write('Downloading "%s"' % fullname)
        downloady.download_file(
            url,
            localname=fullname,
            bytespersecond=bytespersecond,
            callback_progress=downloady.Progress2,
            headers=headers,
            overwrite=overwrite,
        )

def download_argparse(args):
    return download(
        databasename=args.databasename,
        outputdir=args.outputdir,
        overwrite=args.overwrite,
        bytespersecond=args.bytespersecond,
    )

def filter_pattern(databasename, regex, action='keep'):
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

    cur.execute('SELECT * FROM urls')
    items = cur.fetchall()
    for item in items:
        url = item[SQL_URL]
        for pattern in regex:
            contains = re.search(pattern, url) is not None

            if keep and contains and not item[SQL_DO_DOWNLOAD]:
                write('Enabling "%s"' % url)
                cur.execute('UPDATE urls SET do_download = 1 WHERE url == ?', [url])
            if remove and contains and item[SQL_DO_DOWNLOAD]:
                write('Disabling "%s"' % url)
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

def list_urls(databasename, output_filename=None):
    '''
    Print the Enabled entries in order of the file basenames.
    This makes it easier to find interesting titles without worrying about
    what directory they're in.
    '''
    sql = sqlite3.connect(databasename)
    cur = sql.cursor()

    cur.execute('SELECT * FROM urls WHERE do_download == 1')
    items = cur.fetchall()
    items.sort(key=lambda x: x[SQL_URL].lower())

    if output_filename is not None:
        output_file = open(output_filename, 'w', encoding='utf-8')
    else:
        output_file = None

    for item in items:
        write(item[SQL_URL], output_file)

    if output_file:
        output_file.close()

def list_urls_argparse(args):
    return list_urls(
        databasename=args.databasename,
        output_filename=args.outputfile,
    )

def measure(databasename, fullscan=False, new_only=False, threads=4):
    '''
    Given a database, print the sum of all Content-Lengths.
    URLs will be HEAD requested if:
        `new_only` is True and the file has no stored content length, or
        `fullscan` is True and `new_only` is False
    '''
    if isinstance(fullscan, str):
        fullscan = bool(fullscan)

    sql = sqlite3.connect(databasename)
    cur = sql.cursor()

    if new_only:
        cur.execute('SELECT * FROM urls WHERE do_download == 1 AND content_length IS NULL')
    else:
        cur.execute('SELECT * FROM urls WHERE do_download == 1')

    items = cur.fetchall()
    filecount = len(items)
    totalsize = 0
    unmeasured_file_count = 0

    if threads is None:
        threads = 1

    thread_queue = threadqueue.ThreadQueue(threads)

    try:
        for fetch in items:
            size = fetch[SQL_CONTENT_LENGTH]

            if fullscan or new_only:
                url = fetch[SQL_URL]
                thread_queue.add(do_head, url, raise_for_status=False)

            elif size is None:
                # Unmeasured and no intention to measure.
                unmeasured_file_count += 1

            else:
                totalsize += size

        for head in thread_queue.run():
            fetch = smart_insert(sql, cur, head=head, commit=False)
            size = fetch[SQL_CONTENT_LENGTH]
            if size is None:
                write('"%s" is not revealing Content-Length' % url)
                size = 0
            totalsize += size
    except (Exception, KeyboardInterrupt):
        sql.commit()
        raise

    sql.commit()
    size_string = bytestring.bytestring(totalsize)
    totalsize_string = '{size_short} ({size_exact:,} bytes) in {filecount:,} files'
    totalsize_string = totalsize_string.format(
        size_short=size_string,
        size_exact=totalsize,
        filecount=filecount,
    )
    write(totalsize_string)
    if unmeasured_file_count > 0:
        write(UNMEASURED_WARNING % unmeasured_file_count)
    return totalsize

def measure_argparse(args):
    return measure(
        databasename=args.databasename,
        fullscan=args.fullscan,
        new_only=args.new_only,
        threads=int_none(args.threads),
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
    tree_root = build_file_tree(databasename)
    tree_root.path = None
    for node in tree_root.walk():
        if node.path:
            node.path = node.path.replace(':||', '://')
            node.display_name = node.display_name.replace(':||', '://')

    if output_filename is not None:
        output_file = open(output_filename, 'w', encoding='utf-8')
        use_html = output_filename.lower().endswith('.html')
    else:
        output_file = None
        use_html = False

    size_details = pathtree.recursive_get_size(tree_root)


    if size_details['unmeasured'] > 0:
        footer = UNMEASURED_WARNING % size_details['unmeasured']
    else:
        footer = None

    line_generator = pathtree.recursive_print_node(tree_root, use_html=use_html, footer=footer)
    for line in line_generator:
        write(line, output_file)


    if output_file is not None:
        output_file.close()
    return tree_root

def tree_argparse(args):
    return tree(
        databasename=args.databasename,
        output_filename=args.outputfile,
    )
##                                                                                                ##
## COMMANDLINE FUNCTIONS ###########################################################################

def main(argv):
    if safeindex(argv, 1, '').lower() in ('help', '-h', '--help', ''):
        write(__doc__)
        return
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_digest = subparsers.add_parser('digest')
    p_digest.add_argument('root_url')
    p_digest.add_argument('-db', '--database', dest='databasename', default=None)
    p_digest.add_argument('-f', '--fullscan', dest='fullscan', action='store_true')
    p_digest.add_argument('-t', '--threads', dest='threads', default=1)
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

    p_list_urls = subparsers.add_parser('list_urls')
    p_list_urls.add_argument('databasename')
    p_list_urls.add_argument('-o', '--outputfile', dest='outputfile', default=None)
    p_list_urls.set_defaults(func=list_urls_argparse)

    p_measure = subparsers.add_parser('measure')
    p_measure.add_argument('databasename')
    p_measure.add_argument('-f', '--fullscan', dest='fullscan', action='store_true')
    p_measure.add_argument('-n', '--new_only', '--new-only', dest='new_only', action='store_true')
    p_measure.add_argument('-t', '--threads', dest='threads', default=1)
    p_measure.set_defaults(func=measure_argparse)

    p_remove_pattern = subparsers.add_parser('remove_pattern')
    p_remove_pattern.add_argument('databasename')
    p_remove_pattern.add_argument('regex')
    p_remove_pattern.set_defaults(func=remove_pattern_argparse)

    p_tree = subparsers.add_parser('tree')
    p_tree.add_argument('databasename')
    p_tree.add_argument('-o', '--outputfile', dest='outputfile', default=None)
    p_tree.set_defaults(func=tree_argparse)

    # Allow interchangability of the command and database name
    # opendirdl measure test.db -n = opendirdl test.db measure -n
    if argv[0] != 'digest' and os.path.isfile(argv[0]):
        (argv[0], argv[1]) = (argv[1], argv[0])
    #print(argv)

    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
