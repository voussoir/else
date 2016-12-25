import argparse
import os
import pyperclip
import requests
import sys
import time
import urllib
import warnings

# pip install voussoirkit
from voussoirkit import bytestring
from voussoirkit import ratelimiter
from voussoirkit import clipext

warnings.simplefilter('ignore')

HEADERS = {
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36'
}

FILENAME_BADCHARS = '*?"<>|\r'

last_request = 0
CHUNKSIZE = 4 * bytestring.KIBIBYTE
TIMEOUT = 60
TEMP_EXTENSION = '.downloadytemp'

PRINT_LIMITER = ratelimiter.Ratelimiter(allowance=5, mode='reject')


def download_file(
        url,
        localname=None,
        auth=None,
        bytespersecond=None,
        callback_progress=None,
        do_head=True,
        headers=None,
        overwrite=False,
        raise_for_undersized=True,
        timeout=None,
        verbose=False,
    ):
    headers = headers or {}

    url = sanitize_url(url)
    if localname in [None, '']:
        localname = basename_from_url(url)
    if os.path.isdir(localname):
        localname = os.path.join(localname, basename_from_url(url))
    localname = sanitize_filename(localname)
    if localname != os.devnull:
        localname = os.path.abspath(localname)

    if verbose:
        safeprint(' URL:', url)
        safeprint('File:', localname)

    plan = prepare_plan(
        url,
        localname,
        auth=auth,
        bytespersecond=bytespersecond,
        callback_progress=callback_progress,
        do_head=do_head,
        headers=headers,
        overwrite=overwrite,
        raise_for_undersized=raise_for_undersized,
        timeout=timeout,
    )
    #print(plan)
    if plan is None:
        return

    return download_plan(plan)

def download_plan(plan):
    localname = plan['download_into']
    directory = os.path.split(localname)[0]
    if directory != '':
        os.makedirs(directory, exist_ok=True)
    touch(localname)
    file_handle = open(localname, 'r+b')
    file_handle.seek(plan['seek_to'])

    if plan['header_range_min'] is not None:
        plan['headers']['range'] = 'bytes={min}-{max}'.format(
            min=plan['header_range_min'],
            max=plan['header_range_max'],
        )

    if plan['plan_type'] == 'resume':
        bytes_downloaded = plan['seek_to']
    elif plan['plan_type'] == 'partial':
        bytes_downloaded = plan['seek_to']
    else:
        bytes_downloaded = 0

    download_stream = request(
        'get',
        plan['url'],
        stream=True,
        auth=plan['auth'],
        headers=plan['headers'],
        timeout=plan['timeout'],
    )

    if plan['remote_total_bytes'] is None:
        # Since we didn't do a head, let's fill this in now.
        plan['remote_total_bytes'] = int(download_stream.headers.get('Content-Length', 0))

    callback_progress = plan['callback_progress']
    if callback_progress is not None:
        callback_progress = callback_progress(plan['remote_total_bytes'])

    for chunk in download_stream.iter_content(chunk_size=CHUNKSIZE):
        bytes_downloaded += len(chunk)
        file_handle.write(chunk)
        if callback_progress is not None:
            callback_progress.step(bytes_downloaded)

        if plan['limiter'] is not None and bytes_downloaded < plan['remote_total_bytes']:
            plan['limiter'].limit(len(chunk))

    file_handle.close()

    # Don't try to rename /dev/null
    if os.devnull not in [localname, plan['real_localname']]:
        localsize = os.path.getsize(localname)
        undersized = plan['plan_type'] != 'partial' and localsize < plan['remote_total_bytes']
        if plan['raise_for_undersized'] and undersized:
            message = 'File does not contain expected number of bytes. Received {size} / {total}'
            message = message.format(size=localsize, total=plan['remote_total_bytes'])
            raise Exception(message)

        if localname != plan['real_localname']:
            os.rename(localname, plan['real_localname'])

    return plan['real_localname']

def prepare_plan(
        url,
        localname,
        auth=None,
        bytespersecond=None,
        callback_progress=None,
        do_head=True,
        headers=None,
        overwrite=False,
        raise_for_undersized=True,
        timeout=TIMEOUT,
    ):
    # Chapter 1: File existence
    headers = headers or {}
    user_provided_range = 'range' in headers
    real_localname = localname
    temp_localname = localname + TEMP_EXTENSION
    real_exists = os.path.exists(real_localname)

    if real_exists and overwrite is False and not user_provided_range:
        print('File exists and overwrite is off. Nothing to do.')
        return None
    temp_exists = os.path.exists(temp_localname)
    real_localsize = int(real_exists and os.path.getsize(real_localname))
    temp_localsize = int(temp_exists and os.path.getsize(temp_localname))

    # Chapter 2: Ratelimiting
    if bytespersecond is None:
        limiter = None
    elif isinstance(bytespersecond, ratelimiter.Ratelimiter):
        limiter = bytespersecond
    else:
        limiter = ratelimiter.Ratelimiter(allowance=bytespersecond)

    # Chapter 3: Extracting range
    if user_provided_range:
        user_range_min = int(headers['range'].split('bytes=')[1].split('-')[0])
        user_range_max = headers['range'].split('-')[1]
        if user_range_max != '':
            user_range_max = int(user_range_max)
    else:
        user_range_min = None
        user_range_max = None

    # Chapter 4: Server range support
    # Always include a range on the first request to figure out whether the
    # server supports it. Use 0- to get correct remote_total_bytes
    temp_headers = headers
    temp_headers.update({'range': 'bytes=0-'})

    if do_head:
        # I'm using a GET instead of an actual HEAD here because some servers respond
        # differently, even though they're not supposed to.
        head = request('get', url, stream=True, headers=temp_headers, auth=auth)
        remote_total_bytes = int(head.headers.get('content-length', 0))
        server_respects_range = (head.status_code == 206 and 'content-range' in head.headers)
        head.connection.close()
    else:
        remote_total_bytes = None
        server_respects_range = False

    if user_provided_range and not server_respects_range:
        if not do_head:
            raise Exception('Cannot determine range support without the head request')
        else:
            raise Exception('Server did not respect your range header')

    # Chapter 5: Plan definitions
    plan_base = {
        'url': url,
        'auth': auth,
        'callback_progress': callback_progress,
        'limiter': limiter,
        'headers': headers,
        'real_localname': real_localname,
        'raise_for_undersized': raise_for_undersized,
        'remote_total_bytes': remote_total_bytes,
        'timeout': timeout,
    }
    plan_fulldownload = dict(
        plan_base,
        download_into=temp_localname,
        header_range_min=None,
        header_range_max=None,
        plan_type='fulldownload',
        seek_to=0,
    )
    plan_resume = dict(
        plan_base,
        download_into=temp_localname,
        header_range_min=temp_localsize,
        header_range_max='',
        plan_type='resume',
        seek_to=temp_localsize,
    )
    plan_partial = dict(
        plan_base,
        download_into=real_localname,
        header_range_min=user_range_min,
        header_range_max=user_range_max,
        plan_type='partial',
        seek_to=user_range_min,
    )

    # Chapter 6: Redeem your meal vouchers here
    if real_exists:
        if overwrite:
            os.remove(real_localname)

        if user_provided_range:
            return plan_partial

        return plan_fulldownload

    elif temp_exists and temp_localsize > 0:
        if overwrite:
            return plan_fulldownload

        if user_provided_range:
            return plan_partial

        if server_respects_range:
            print('Resume from byte %d' % plan_resume['seek_to'])
            return plan_resume

    else:
        if user_provided_range:
            return plan_partial

        return plan_fulldownload

    raise Exception('No plan was chosen?')


class Progress1:
    def __init__(self, total_bytes):
        self.limiter = ratelimiter.Ratelimiter(allowance=8, mode='reject')
        self.limiter.balance = 1
        self.total_bytes = max(1, total_bytes)
        self.divisor = bytestring.get_appropriate_divisor(total_bytes)
        self.total_format = bytestring.bytestring(total_bytes, force_unit=self.divisor)
        self.downloaded_format = '{:>%d}' % len(self.total_format)
        self.blank_char = ' '
        self.solid_char = '█'

    def step(self, bytes_downloaded):
        #print(self.limiter.balance)
        percent = bytes_downloaded / self.total_bytes
        percent = min(1, percent)
        if self.limiter.limit(1) is False and percent < 1:
            return

        downloaded_string = bytestring.bytestring(bytes_downloaded, force_unit=self.divisor)
        downloaded_string = self.downloaded_format.format(downloaded_string)
        block_count = 50
        solid_blocks = self.solid_char * int(block_count * percent)
        statusbar = solid_blocks.ljust(block_count, self.blank_char)
        statusbar = self.solid_char + statusbar + self.solid_char

        end = '\n' if percent == 1 else ''
        message = '\r{bytes_downloaded} {statusbar} {total_bytes}'
        message = message.format(
            bytes_downloaded=downloaded_string,
            total_bytes=self.total_format,
            statusbar=statusbar,
        )
        print(message, end=end, flush=True)


class Progress2:
    def __init__(self, total_bytes):
        self.total_bytes = max(1, total_bytes)
        self.limiter = ratelimiter.Ratelimiter(allowance=8, mode='reject')
        self.limiter.balance = 1
        self.total_bytes_string = '{:,}'.format(self.total_bytes)
        self.bytes_downloaded_string = '{:%d,}' % len(self.total_bytes_string)

    def step(self, bytes_downloaded):
        percent = (bytes_downloaded * 100) / self.total_bytes
        percent = min(100, percent)
        if self.limiter.limit(1) is False and percent < 100:
            return

        percent_string = '%08.4f' % percent
        bytes_downloaded_string = self.bytes_downloaded_string.format(bytes_downloaded)

        end = '\n' if percent == 100 else ''
        message = '\r{bytes_downloaded} / {total_bytes} / {percent}%'
        message = message.format(
            bytes_downloaded=bytes_downloaded_string,
            total_bytes=self.total_bytes_string,
            percent=percent_string,
        )
        print(message, end=end, flush=True)


def basename_from_url(url):
    '''
    Determine the local filename appropriate for a URL.
    '''
    localname = urllib.parse.unquote(url)
    localname = localname.split('?')[0]
    localname = localname.split('/')[-1]
    return localname
    
def get_permission(prompt='y/n\n>', affirmative=['y', 'yes']):
    permission = input(prompt)
    return permission.lower() in affirmative

def request(method, url, stream=False, headers=None, timeout=TIMEOUT, **kwargs):
    if headers is None:
        headers = {}
    for (key, value) in HEADERS.items():
        headers.setdefault(key, value)
    session = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=30)
    b = requests.adapters.HTTPAdapter(max_retries=30)
    session.mount('http://', a)
    session.mount('https://', b)
    session.max_redirects = 40

    method = {
        'get': session.get,
        'head': session.head,
        'post': session.post,
    }[method]
    req = method(url, stream=stream, headers=headers, timeout=timeout, **kwargs)
    req.raise_for_status()
    return req

def safeprint(*texts, **kwargs):
    texts = [str(text).encode('ascii', 'replace').decode() for text in texts]
    print(*texts, **kwargs)

def sanitize_filename(text, exclusions=''):
    bet = FILENAME_BADCHARS.replace(exclusions, '')
    for char in bet:
        text = text.replace(char, '')
    return text

def sanitize_url(url):
    url = url.replace('%3A//', '://')
    return url

def touch(filename):
    f = open(filename, 'ab')
    f.close()
    return


def download_argparse(args):
    url = args.url

    url = clipext.resolve(url)
    callback = {
        None: Progress1,
        '1': Progress1,
        '2': Progress2,
    }.get(args.callback, args.callback)

    bytespersecond = args.bytespersecond
    if bytespersecond is not None:
        bytespersecond = bytestring.parsebytes(bytespersecond)

    headers = {}
    if args.range is not None:
        headers['range'] = 'bytes=%s' % args.range

    download_file(
        url=url,
        localname=args.localname,
        bytespersecond=bytespersecond,
        callback_progress=callback,
        do_head=args.no_head is False,
        headers=headers,
        overwrite=args.overwrite,
        timeout=int(args.timeout),
        verbose=True,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('url')
    parser.add_argument('localname', nargs='?', default=None)
    parser.add_argument('-c', '--callback', dest='callback', default=Progress1)
    parser.add_argument('-bps', '--bytespersecond', dest='bytespersecond', default=None)
    parser.add_argument('-ow', '--overwrite', dest='overwrite', action='store_true')
    parser.add_argument('-r', '--range', dest='range', default=None)
    parser.add_argument('--timeout', dest='timeout', default=TIMEOUT)
    parser.add_argument('--no-head', dest='no_head', action='store_true')
    parser.set_defaults(func=download_argparse)

    args = parser.parse_args()
    args.func(args)
