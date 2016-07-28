import sys
sys.path.append('C:\\git\\else\\ratelimiter'); import ratelimiter
sys.path.append('C:\\git\\else\\bytestring'); import bytestring

import argparse
import os
import pyperclip # pip install pyperclip
import requests
import time
import urllib
import warnings
warnings.simplefilter('ignore')

HEADERS = {
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36'
}
SLEEPINESS = 3

FILENAME_BADCHARS = '*?"<>|'

last_request = 0
CHUNKSIZE = 16 * bytestring.KIBIBYTE
STOP = False
TIMEOUT = 600

def download_file(
        url,
        localname=None,
        auth=None,
        bytespersecond=None,
        callback_progress=None,
        headers=None,
        overwrite=None
    ):
    if headers is None:
        headers = {}
    ''' Determine local filename '''
    url = url.replace('%3A//', '://')
    if localname in [None, '']:
        localname = localize(url)

    localname = filepath_sanitize(localname)

    directory = os.path.split(localname)[0]
    if directory != '':
        os.makedirs(directory, exist_ok=True)
    
    if bytespersecond is None:
        limiter = None
    else:
        limiter = ratelimiter.Ratelimiter(bytespersecond, period=1)

    ''' Prepare condition variables '''
    local_exists = os.path.exists(localname)
    if local_exists and overwrite is False:
        print('Overwrite off. Nothing to do.')
        return

    user_provided_range = 'range' in headers
    if user_provided_range:
        user_range_min = int(headers['range'].split('bytes=')[1].split('-')[0])
        user_range_max = headers['range'].split('-')[1]
        if user_range_max != '':
            user_range_max = int(user_range_max)
    else:
        # Included to determine whether the server supports this
        headers['range'] = 'bytes=0-'

    # I'm using a GET instead of an actual HEAD here because some servers respond
    # differently, even though they're not supposed to.
    head = request('get', url, stream=True, headers=headers, auth=auth)
    remote_total_bytes = int(head.headers.get('content-length', 1))
    server_respects_range = (head.status_code == 206 and 'content-range' in head.headers)
    seek_to = 0
    header_range_min = None
    header_range_max = None
    head.connection.close()

    if not user_provided_range:
        del headers['range']

    touch(localname)
    file_handle = open(localname, 'r+b')
    file_handle.seek(0)

    ''' THINGS THAT CAN HAPPEN '''
    if local_exists:
        local_existing_bytes = os.path.getsize(localname)
        if overwrite is True:
            file_handle.truncate()
            if user_provided_range:
                header_range_min = user_range_min
                header_range_max = user_range_max
                seek_to = user_range_min

            elif not user_provided_range:
                pass

        elif overwrite is None:
            if local_existing_bytes == remote_total_bytes:
                print('File is 100%. Nothing to do.')
                return

            if user_provided_range:
                if server_respects_range:
                    seek_to = user_range_min

                else:
                    raise Exception('The server did not respect your range header')

            elif not user_provided_range:
                if server_respects_range:
                    print('Resuming from %d' % local_existing_bytes)
                    header_range_min = local_existing_bytes
                    header_range_max = ''
                    seek_to = local_existing_bytes

                else:
                    print('File exists, but server doesn\'t allow resumes. Restart from 0?')
                    permission = get_permission()
                    if permission:
                        file_handle.truncate()

                    else:
                        raise Exception('Couldn\'t resume')

        else:
            raise TypeError('Invalid value for `overwrite`. Must be True, False, or None')

    elif not local_exists:
        if user_provided_range:
            if server_respects_range:
                file_handle.seek(user_range_min)
                file_handle.write(b'\0')

                header_range_min = user_range_min
                header_range_max = user_range_max
                seek_to = user_range_min

            else:
                raise Exception('The server did not respect your range header')

        elif not user_provided_range:
            pass

    if header_range_min is not None:
        headers['range'] = 'bytes={0}-{1}'.format(header_range_min, header_range_max)

    bytes_downloaded = seek_to
    file_handle.seek(seek_to)
    download_stream = request('get', url, stream=True, headers=headers, auth=auth)

    ''' Begin download '''
    for chunk in download_stream.iter_content(chunk_size=CHUNKSIZE):
        bytes_downloaded += len(chunk)
        file_handle.write(chunk)
        if callback_progress is not None:
            callback_progress(bytes_downloaded, remote_total_bytes)

        if limiter is not None and bytes_downloaded < remote_total_bytes:
            limiter.limit(len(chunk))

    file_handle.close()
    return localname

def filepath_sanitize(text, exclusions=''):
    bet = FILENAME_BADCHARS.replace(exclusions, '')
    for char in bet:
        text = text.replace(char, '')
    return text

def get_permission(prompt='y/n\n>', affirmative=['y', 'yes']):
    permission = input(prompt)
    return permission.lower() in affirmative

def is_clipboard(s):
    return s.lower() in ['!c', '!clip', '!clipboard']

def localize(url):
    '''
    Determine the local filename appropriate for a URL.
    '''
    localname = urllib.parse.unquote(url)
    localname = localname.split('?')[0]
    localname = localname.split('/')[-1]
    return localname

def progress(bytes_downloaded, bytes_total, prefix=''):
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
    percent = '%08.4f' % percent
    bytes_downloaded_string = '{0:,}'.format(bytes_downloaded)
    bytes_total_string = '{0:,}'.format(bytes_total)
    bytes_downloaded_string = bytes_downloaded_string.rjust(len(bytes_total_string), ' ')

    end = '\n' if percent == 100 else ''
    message = '\r{prefix}{bytes_downloaded} / {bytes_total} / {percent}%'
    message = message.format(
        prefix=prefix,
        bytes_downloaded=bytes_downloaded_string,
        bytes_total=bytes_total_string,
        percent=percent,
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

def touch(filename):
    f = open(filename, 'ab')
    f.close()
    return


def download_argparse(args):
    url = args.url
    if is_clipboard(url):
        url = pyperclip.paste()
        print(url)

    overwrite = {
        'y':True, 't':True,
        'n':False, 'f':False,
    }.get(args.overwrite.lower(), None)

    callback = {
        None: progress,
        '1': progress,
        '2': progress2,
    }.get(args.callback, None)

    callback = args.callback
    if callback == '1':
        callback = progress
    if callback == '2':
        callback = progress2

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
        overwrite=overwrite,
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    #p_download_file = subparsers.add_parser('download_file')
    parser.add_argument('url')
    parser.add_argument('localname', nargs='?', default=None)
    parser.add_argument('-c', '--callback', dest='callback', default=progress)
    parser.add_argument('-bps', '--bytespersecond', dest='bytespersecond', default=None)
    parser.add_argument('-ow', '--overwrite', dest='overwrite', default='')
    parser.add_argument('-r', '--range', dest='range', default=None)
    parser.set_defaults(func=download_argparse)

    args = parser.parse_args()
    args.func(args)