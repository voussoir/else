import os
import sys
import threading
import time

# pip install
# https://raw.githubusercontent.com/voussoir/else/master/_voussoirkit/voussoirkit.zip
from voussoirkit import clipext
from voussoirkit import downloady

def remove_finished(threads):
    threads = [t for t in threads if t.is_alive()]
    return threads

def download_thread(url, filename):
    url = url.strip()
    if url == '':
        return

    if os.path.exists(filename):
        print('Skipping existing file "%s"' % filename)
        return
    print(' Starting "%s"' % filename)
    downloady.download_file(url, filename, timeout=15)
    print('+Finished "%s"' % filename)

def listget(li, index, fallback):
    try:
        return li[index]
    except IndexError:
        return fallback

def threaded_dl(urls, thread_count, filename_format=None):
    threads = []
    index_digits = len(str(len(urls)))
    if filename_format is None:
        filename_format = '{now}_{index}_{basename}'
    filename_format = filename_format.replace('{index}', '{index:0%0dd}' % index_digits)
    now = int(time.time())
    for (index, url) in enumerate(urls):
        while len(threads) == thread_count:
            threads = remove_finished(threads)
            time.sleep(0.1)

        basename = downloady.basename_from_url(url)
        extension = os.path.splitext(basename)[1]
        filename = filename_format.format(
            basename=basename,
            ext=extension,
            extension=extension,
            index=index,
            now=now,
        )
        t = threading.Thread(target=download_thread, args=[url, filename])
        t.daemon = True
        threads.append(t)
        t.start()

    while len(threads) > 0:
        threads = remove_finished(threads)
        print('%d threads remaining\r' % len(threads), end='', flush=True)
        time.sleep(0.1)

def main():
    filename = sys.argv[1]
    if os.path.isfile(filename):
        f = open(filename, 'r')
        with f:
            urls = f.read()
    else:
        urls = clipext.resolve(filename)
    urls = urls.replace('\r', '').split('\n')
    thread_count = int(listget(sys.argv, 2, 4))
    filename_format = listget(sys.argv, 3, None)
    threaded_dl(urls, thread_count=thread_count, filename_format=filename_format)

if __name__ == '__main__':
    main()
