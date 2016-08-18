import argparse
import os
import pyperclip # pip install pyperclip
import requests
import sys
import time
import urllib
import warnings

sys.path.append('C:\\git\\else\\clipext'); import clipext
sys.path.append('C:\\git\\else\\ratelimiter'); import ratelimiter
sys.path.append('C:\\git\\else\\bytestring'); import bytestring

warnings.simplefilter('ignore')

HEADERS = {
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36'
}

FILENAME_BADCHARS = '*?"<>|'

last_request = 0
CHUNKSIZE = 16 * bytestring.KIBIBYTE
TIMEOUT = 600
TEMP_EXTENSION = '.downloadytemp'

def basename_from_url(url):
    '''
    Determine the local filename appropriate for a URL.
    '''
    localname = urllib.parse.unquote(url)
    localname = localname.split('?')[0]
    localname = localname.split('/')[-1]
    return localname

def download_file(
        url,
        localname=None,
        auth=None,
        bytespersecond=None,
        callback_progress=None,
        headers=None,
        overwrite=False,
        verbose=False,
    ):
    headers = headers or {}

    url = sanitize_url(url)
    if localname in [None, '']:
        localname = basename_from_url(url)
    localname = sanitize_filename(localname)

    if verbose:
        print(url)

    plan = prepare_plan(
        url,
        localname,
        auth=auth,
        bytespersecond=bytespersecond,
        headers=headers,
        overwrite=overwrite,
    )
    #print(plan)
    if plan is None:
        return

    localname = plan['download_into']
    directory = os.path.split(localname)[0]
    if directory != '':
        os.makedirs(directory, exist_ok=True)
    touch(localname)
    file_handle = open(localname, 'r+b')
    file_handle.seek(plan['seek_to'])

    if plan['header_range_min'] is not None:
        headers['range'] = 'bytes={min}-{max}'.format(
            min=plan['header_range_min'],
            max=plan['header_range_max'],
        )

    if plan['plan_type'] == 'resume':
        bytes_downloaded = plan['seek_to']
    else:
        bytes_downloaded = 0

    download_stream = request('get', url, stream=True, headers=headers, auth=auth)
    for chunk in download_stream.iter_content(chunk_size=CHUNKSIZE):
        bytes_downloaded += len(chunk)
        file_handle.write(chunk)
        if callback_progress is not None:
            callback_progress(bytes_downloaded, plan['remote_total_bytes'])

        if plan['limiter'] is not None and bytes_downloaded < plan['remote_total_bytes']:
            plan['limiter'].limit(len(chunk))

    file_handle.close()

    if localname != plan['real_localname']:
        os.rename(localname, plan['real_localname'])

    localsize = os.path.getsize(plan['real_localname'])
    if plan['plan_type'] != 'partial' and localsize < plan['remote_total_bytes']:
        message = 'File does not contain expected number of bytes. Received {size} / {total}'
        message = message.format(size=os.path.getsize(localname), total=plan['remote_total_bytes'])
        raise Exception(message)

    return plan['real_localname']

def prepare_plan(
        url,
        localname,
        auth,
        bytespersecond,
        headers,
        overwrite,
    ):
    # Chapter 1: File existence
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
        limiter = ratelimiter.Ratelimiter(bytespersecond)

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

    # I'm using a GET instead of an actual HEAD here because some servers respond
    # differently, even though they're not supposed to.
    head = request('get', url, stream=True, headers=temp_headers, auth=auth)
    remote_total_bytes = int(head.headers.get('content-length', 0))
    server_respects_range = (head.status_code == 206 and 'content-range' in head.headers)
    head.connection.close()

    if user_provided_range and not server_respects_range:
        raise Exception('Server did not respect your range header')

    # Chapter 5: Plan definitions
    plan_base = {
        'limiter': limiter,
        'real_localname': real_localname,
        'remote_total_bytes': remote_total_bytes,
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

    print('No plan was chosen?')
    return None
    
def get_permission(prompt='y/n\n>', affirmative=['y', 'yes']):
    permission = input(prompt)
    return permission.lower() in affirmative

def progress1(bytes_downloaded, bytes_total, prefix=''):
    divisor = bytestring.get_appropriate_divisor(bytes_total)
    bytes_total_string = bytestring.bytestring(bytes_total, force_unit=divisor)
    bytes_downloaded_string = bytestring.bytestring(bytes_downloaded, force_unit=divisor)
    bytes_downloaded_string = bytes_downloaded_string.rjust(len(bytes_total_string), ' ')

    blocks = 50
    char = '█'
    percent = bytes_downloaded * 100 / bytes_total
    percent = int(min(100, percent))
    completed_blocks = char * int(blocks * percent / 100)
    incompleted_blocks = ' ' * (blocks - len(completed_blocks))
    statusbar = '{char}{complete}{incomplete}{char}'.format(
        char=char,
        complete=completed_blocks,
        incomplete=incompleted_blocks,
    )

    end = '\n' if percent == 100 else ''
    message = '\r{prefix}{bytes_downloaded} {statusbar} {bytes_total}'
    message = message.format(
        prefix=prefix, 
        bytes_downloaded=bytes_downloaded_string,
        bytes_total=bytes_total_string,
        statusbar=statusbar,
    )
    print(message, end=end, flush=True)

def progress2(bytes_downloaded, bytes_total, prefix=''):
    percent = (bytes_downloaded*100)/bytes_total
    percent = min(100, percent)
    percent_string = '%08.4f' % percent
    bytes_downloaded_string = '{0:,}'.format(bytes_downloaded)
    bytes_total_string = '{0:,}'.format(bytes_total)
    bytes_downloaded_string = bytes_downloaded_string.rjust(len(bytes_total_string), ' ')

    end = '\n' if percent == 100 else ''
    message = '\r{prefix}{bytes_downloaded} / {bytes_total} / {percent}%'
    message = message.format(
        prefix=prefix,
        bytes_downloaded=bytes_downloaded_string,
        bytes_total=bytes_total_string,
        percent=percent_string,
    )
    print(message, end=end, flush=True)

def request(method, url, stream=False, headers=None, timeout=TIMEOUT, **kwargs):
    if headers is None:
        headers = {}
    for (key, value) in HEADERS.items():
        headers.setdefault(key, value)
    session = requests.Session()
    session.max_redirects = 40

    method = {
        'get': session.get,
        'head': session.head,
        'post': session.post,
    }[method]

    req = method(url, stream=stream, headers=headers, timeout=timeout, **kwargs)
    req.raise_for_status()
    return req

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
        None: progress1,
        '1': progress1,
        '2': progress2,
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
        headers=headers,
        overwrite=args.overwrite,
        verbose=True,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('url')
    parser.add_argument('localname', nargs='?', default=None)
    parser.add_argument('-c', '--callback', dest='callback', default=progress1)
    parser.add_argument('-bps', '--bytespersecond', dest='bytespersecond', default=None)
    parser.add_argument('-ow', '--overwrite', dest='overwrite', action='store_true')
    parser.add_argument('-r', '--range', dest='range', default=None)
    parser.set_defaults(func=download_argparse)

    args = parser.parse_args()
    args.func(args)
