import argparse
import io
import json
import os
import requests
import sys
import time
import traceback
import zipfile

from voussoirkit import clipext

FILENAME_BADCHARS = '\\/:*?<>|"'

WEBSTORE_URL = 'https://chrome.google.com/webstore/detail/x/{extension_id}'
CRX_URL = 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=59.0&x=id%3D{extension_id}%26installsource%3Dondemand%26uc'

def sanitize_filename(name):
    for c in FILENAME_BADCHARS:
        name = name.replace(c, '-')
    return name

def prompt_permission(prompt):
    answer = input(prompt)
    return answer.lower() in {'yes', 'y'}

def get_webstore_name_version(extension_id):
    url = WEBSTORE_URL.format(extension_id=extension_id)
    response = requests.get(url)
    try:
        name = response.text
        name = name.split('meta property="og:title" content="')[1]
        name = name.split('"')[0]
    except IndexError:
        name = None

    try:
        version = response.text
        version = version.split('meta itemprop="version" content="')[1]
        version = version.split('"')[0]
    except IndexError:
        version = None

    return (name, version)

def get_crx_name_version(crx_bytes):
    crx_handle = io.BytesIO(crx_bytes)
    crx_archive = zipfile.ZipFile(crx_handle)
    manifest = json.loads(crx_archive.read('manifest.json'))
    name = manifest.get('name', None)
    version = manifest.get('version', None)
    return (name, version)

def getcrx(extension_id, auto_overwrite=None):
    url = CRX_URL.format(extension_id=extension_id)
    response = requests.get(url)
    response.raise_for_status()

    (name, version) = get_webstore_name_version(extension_id)
    if name is None or version is None:
        (crx_name, crx_ver) = get_crx_name_version(response.content)
        name = name or crx_name
        version = version or crx_version

    name = name or extension_id
    version = version or time.strftime('%Y%m%d')

    version = version or response.url.split('/')[-1]

    crx_filename = '{name} ({id}) [{version}]'
    crx_filename = crx_filename.format(
        name=name,
        id=extension_id,
        version=version,
    )

    if not crx_filename.endswith('.crx'):
        crx_filename += '.crx'

    crx_filename = sanitize_filename(crx_filename)
    if os.path.isfile(crx_filename):
        if auto_overwrite is None:
            message = '"%s" already exists. Overwrite?' % crx_filename
            permission = prompt_permission(message)
        else:
            permission = False
    else:
        permission = True

    if permission:
        crx_handle = open(crx_filename, 'wb')
        crx_handle.write(response.content)
        print('Downloaded "%s".' % crx_filename)

def getcrx_argparse(args):
    extension_ids = []

    if len(args.extension_ids) == 1:
        extension_ids.extend(clipext.resolve(args.extension_ids[0], split_lines=True))

    elif args.extension_ids:
        extension_ids.extend(args.extension_ids)

    if args.file:
        with open(args.file, 'r') as handle:
            lines = handle.readlines()
        extension_ids.extend(lines)

    extension_ids = [x.split('/')[-1].strip() for x in extension_ids]

    if args.overwrite and not args.dont_overwrite:
        auto_overwrite = True
    elif args.dont_overwrite and not args.overwrite:
        auto_overwrite = False
    else:
        auto_overwrite = None

    for extension_id in extension_ids:
        try:
            getcrx(extension_id, auto_overwrite=auto_overwrite)
        except Exception:
            if args.fail_early:
                raise
            else:
                traceback.print_exc()
                print('Resuming...')

def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('extension_ids', nargs='*', default=None)
    parser.add_argument('--file', dest='file', default=None)
    parser.add_argument('--fail_early', dest='fail_early', action='store_true')
    parser.add_argument('--overwrite', dest='overwrite', action='store_true')
    parser.add_argument('--dont_overwrite', dest='dont_overwrite', action='store_true')
    parser.set_defaults(func=getcrx_argparse)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
