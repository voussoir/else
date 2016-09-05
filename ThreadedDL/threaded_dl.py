import os
import sys
import threading
import time

sys.path.append('C:\\git\\else\\clipext'); import clipext
sys.path.append('C:\\git\\else\\downloady'); import downloady

def remove_finished(threads):
    threads = [t for t in threads if t.is_alive()]
    return threads

def download_thread(url, filename_prefix=''):
    url = url.strip()
    if url == '':
        return

    basename = downloady.basename_from_url(url)
    basename = filename_prefix + basename
    if os.path.exists(basename):
        print('Skipping existing file "%s"' % basename)
        return
    print('Starting "%s"' % basename)
    downloady.download_file(url, basename)
    print('Finished "%s"' % basename)

def listget(li, index, fallback):
    try:
        return li[index]
    except IndexError:
        return fallback

def threaded_dl(urls, thread_count, prefix=None):
    threads = []
    prefix_digits = len(str(len(urls)))
    if prefix is None:
        prefix = now = int(time.time())
    prefix_text = '{prefix}_{{index:0{digits}d}}_'.format(prefix=prefix, digits=prefix_digits)
    for (index, url) in enumerate(urls):
        while len(threads) == thread_count:
            threads = remove_finished(threads)
            time.sleep(0.1)

        prefix = prefix_text.format(index=index)
        t = threading.Thread(target=download_thread, args=[url, prefix])
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
        urls = urls.split('\n')
    else:
        urls = clipext.resolve(filename)
        urls = urls.split('\n')
    thread_count = int(listget(sys.argv, 2, 4))
    prefix = listget(sys.argv, 3, None)
    threaded_dl(urls, thread_count=thread_count, prefix=prefix)

if __name__ == '__main__':
    main()