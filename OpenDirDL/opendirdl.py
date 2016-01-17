import bs4
import hashlib
import json
import os
import re
import requests
import string
import sys
import time
import traceback
import urllib.parse

FILENAME_BADCHARS = '/\\:*?"<>|'
DOWNLOAD_CHUNK = 2048

# When doing a basic scan, we will not send HEAD requests to URLs that end in these strings,
# because they're probably files.
# This isn't meant to be a comprehensive filetype library, but it covers enough of the
# typical opendir to speed things up.
SKIPPABLE_FILETYPES = [
'.avi',
'.bmp',
'.epub',
'.db',
'.flac',
'.ico',
'.iso',
'.jpg',
'.m4a',
'.mkv',
'.mov',
'.mp3',
'.mp4',
'.pdf',
'.png',
'.srt',
'.txt',
'.webm',
'.zip',
]

SKIPPABLE_FILETYPES = [x.lower() for x in SKIPPABLE_FILETYPES]

class Downloader:
    def __init__(self, urlfile, outputdir=None, headers=None):
        jdict = file_to_dict(urlfile)
        self.urls = [item[0] for item in jdict.items()]
        self.urls.sort(key=str.lower)
        self.outputdir = outputdir

        if self.outputdir is None or self.outputdir == "":
            # returns (root, path, filename). Keep root.
            self.outputdir = url_to_filepath(self.urls[0])[0]

    def download(self, overwrite=False):
        overwrite = bool(overwrite)
        for url in self.urls:
            ''' Creating the Path '''
            (root, folder, filename) = url_to_filepath(url)
            # In case the user has set a custom download directory,
            # ignore the above value of `root`.
            root = self.outputdir
            folder = os.path.join(root, folder)
            if not os.path.exists(folder):
                os.makedirs(folder)
            localname = os.path.join(folder, filename)
            temporary_basename = hashit(url, 16) + '.oddltemporary'
            temporary_localname = os.path.join(folder, temporary_basename)

            ''' Managing overwrite '''
            if os.path.isfile(localname):
                if overwrite is True:
                    os.remove(localname)
                else:
                    safeprint('Skipping "%s". Use `overwrite=True`' % localname)
                    continue

            safeprint('Downloading "%s" as "%s"' % (localname, temporary_basename))
            filehandle = open(temporary_localname, 'wb')
            try:
                download_file(url, filehandle, hookfunction=hook1)
                os.rename(temporary_localname, localname)
            except:
                filehandle.close()
                raise

class Walker:
    def __init__(self, website, outputfile, fullscan=False):
        self.website = website
        self.fullscan = bool(fullscan)
        if os.path.exists(outputfile):
            self.results = file_to_dict(outputfile)
        else:
            self.results = {}
        self.already_seen = set()

    def add_head_to_results(self, head):
        if isinstance(head, str):
            # For when we're doing a basic scan, which skips urls that
            # look like a file.
            self.results[head] = {
                'Content-Length': -1,
                'Content-Type': '?',
            }
            self.already_seen.add(head)
        else:
            # For when we're doing a full scan, which does a HEAD request
            # for all urls.
            self.results[head.url] = {
                'Content-Length': int(head.headers.get('Content-Length', -1)),
                'Content-Type': head.headers.get('Content-Type', '?'),
            }
            self.already_seen.add(head.url)

    def extract_hrefs(self, response):
        soup = bs4.BeautifulSoup(response.text)
        elements = soup.findAll('a')
        hrefs = []
        for element in elements:
            try:
                href = element['href']
            except KeyError:
                continue
            href = urllib.parse.urljoin(response.url, href)
            if not href.startswith(self.website):
                # Don't go to other sites or parent directories
                continue
            if 'C=' in href and 'O=' in href:
                # Alternative sort modes for index pages
                continue
            if href.endswith('desktop.ini'):
                # I hate these things
                continue
            hrefs.append(href)
        return hrefs

    def walk(self, url=None):
        if url is None:
            url = self.website
        else:
            url = urllib.parse.urljoin(self.website, url)

        results = []

        urll = url.lower()
        if self.fullscan is False and any(urll.endswith(ext) for ext in SKIPPABLE_FILETYPES):
            print('Skipping "%s" due to extension' % url)
            self.add_head_to_results(url)
            return results

        if not url.startswith(self.website):
            # Don't follow external links or parent directory.
            return results

        head = requests.head(url)
        head.raise_for_status()

        safeprint('HEAD: %s : %s' % (url, head))
        content_type = head.headers.get('Content-Type', '?')
        self.already_seen.add(head.url)

        if content_type.startswith('text/html') and head.url.endswith('/'):
            # This is an index page, let's get recursive.
            page = requests.get(url)
            safeprint(' GET: %s : %s' % (url, page))
            hrefs = self.extract_hrefs(page)
            for url in hrefs:
                if url not in self.results and url not in self.already_seen:
                    results += self.walk(url)
        else:
            # Don't add index pages to the results.
            self.add_head_to_results(head)

        return results


def dict_to_file(jdict, filename):
    filehandle = open(filename, 'wb')
    text = json.dumps(jdict, indent=4, sort_keys=True)
    text = text.encode('utf-8')
    filehandle.write(text)
    filehandle.close()

def download_file(url, filehandle, getsizeheaders=True, hookfunction=None, headers={}, auth=None):
    if getsizeheaders:
        totalsize = requests.head(url, headers=headers, auth=auth)
        totalsize = int(totalsize.headers['content-length'])
    else:
        totalsize = 1
    currentblock = 0
    downloading = requests.get(url, stream=True, headers=headers, auth=auth)
    for chunk in downloading.iter_content(chunk_size=DOWNLOAD_CHUNK):
        if chunk:
            currentblock += 1
            filehandle.write(chunk)
            if hookfunction is not None:
                hookfunction(currentblock, DOWNLOAD_CHUNK, totalsize)
    filehandle.close()
    size = os.path.getsize(filehandle.name)
    if size < totalsize:
        raise Exception('Did not receive expected total size. %d / %d' % (size, totalsize))
    return True

def file_to_dict(filename):
    filehandle = open(filename, 'rb')
    jdict = json.loads(filehandle.read().decode('utf-8'))
    filehandle.close()
    return jdict

def filepath_sanitize(text, exclusions=''):
    bet = FILENAME_BADCHARS.replace(exclusions, '')
    for char in bet:
        text = text.replace(char, '')
    return text

def hashit(text, length=None):
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

def safeprint(text, **kwargs):
    text = str(text)
    text = text.encode('ascii', 'replace').decode()
    text = text.replace('?', '_')
    print(text, **kwargs)

def url_to_filepath(text):
    text = urllib.parse.unquote(text)
    parts = urllib.parse.urlsplit(text)
    root = parts.netloc
    (folder, filename) = os.path.split(parts.path)
    while folder.startswith('/'):
        folder = folder[1:]

    # Folders are allowed to have slashes
    folder = filepath_sanitize(folder, exclusions='/\\')
    folder = folder.replace('\\', os.path.sep)
    folder = folder.replace('/', os.path.sep)
    # But Files are not.
    filename = filepath_sanitize(filename)
    return (root, folder, filename)

## Commandline functions ####################################################\\
def digest(website, outputfile, fullscan, *trash):
    fullscan = bool(fullscan)
    if website[-1] != '/':
        website += '/'
    walker = Walker(website, outputfile, fullscan=fullscan)
    try:
        walker.walk()
        dict_to_file(walker.results, outputfile)
    except:
        dict_to_file(walker.results, outputfile)
        traceback.print_exc()
        print('SAVED PROGRESS SO FAR')

def download(urlfile, outputdir, overwrite, *trash):
    downloader = Downloader(urlfile, outputdir)
    downloader.download(overwrite)

def filter_pattern(urlfile, patterns, negative=False, *trash):
    '''
    When `negative` is True, items are kept when they do NOT match the pattern,
    allowing you to delete trash files.

    When `negative` is False, items are keep when they DO match the pattern,
    allowing you to keep items of interest.
    '''
    if isinstance(patterns, str):
        patterns = [patterns]
    jdict = file_to_dict(urlfile)
    keys = list(jdict.keys())
    for key in keys:
        for pattern in patterns:
            contains = re.search(pattern, key) is not None
            if contains ^ negative:
                safeprint('Removing "%s"' % key)
                del jdict[key]
    dict_to_file(jdict, urlfile)

def keep_pattern(urlfile, patterns, *trash):
    filter_pattern(urlfile=urlfile, patterns=patterns, negative=True)

def measure(urlfile, *trash):
    jdict = file_to_dict(urlfile)
    totalbytes = 0
    for (url, info) in jdict.items():
        bytes = info['Content-Length']
        if bytes > 0:
            totalbytes += bytes
    bytestring = '{:,}'.format(totalbytes)
    print(bytestring)
    return totalbytes

def remove_pattern(urlfile, patterns, *trash):
    filter_pattern(urlfile=urlfile, patterns=patterns, negative=False)

def listget(l, index, default=None):
    try:
        return l[index]
    except IndexError:
        return default
cmdfunctions = [digest, download, keep_pattern, measure, remove_pattern]
## End of commandline functions #############################################//
    
if __name__ == '__main__':
    command = listget(sys.argv, 1, None)
    arg1 = listget(sys.argv, 2, None)
    arg2 = listget(sys.argv, 3, None)
    arg3 = listget(sys.argv, 4, None)
    if command is None:
        quit()
    did_something = False
    for function in cmdfunctions:
        if command == function.__name__:
            function(arg1, arg2, arg3)
            did_something = True
            break
    if not did_something:
        print('No matching function')