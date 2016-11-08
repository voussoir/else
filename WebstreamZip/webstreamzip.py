import threading
import zipfile
import tarfile


class Stream:
    def __init__(self):
        self.active_chunk = None
        self.write_ready = threading.Event()
        self.read_ready = threading.Event()
        self.write_ready.set()
        self.all_done = False

    def write(self, chunk):
        if chunk == b'':
            self.all_done = True

        if self.all_done:
            return 0

        self.write_ready.wait()
        #print('writing', chunk)
        self.active_chunk = chunk
        self.write_ready.clear()
        self.read_ready.set()
        return 0

    def tell(self):
        return 0

    def read(self, size=None):
        if self.all_done:
            return b''

        self.read_ready.wait()
        chunk = self.active_chunk
        self.active_chunk = None
        self.read_ready.clear()
        self.write_ready.set()
        return chunk

    def close(self):
        #print('Internal close')
        self.all_done = True
        while not self.write_ready.is_set():
            #print('writeset')
            self.write_ready.set()
        while not self.read_ready.is_set():
            #print('readset')
            self.read_ready.set()

    def flush(self):
        #print('flushy')
        pass

def _stream_tar(memstream, filenames):
    z = tarfile.TarFile(fileobj=memstream, mode='w')
    if isinstance(filenames, dict):
        for (realpath, fakepath) in filenames.items():
            z.add(realpath, arcname=fakepath)
    else:
        for filename in filenames:
            z.add(filename)
    #print('zclosing')
    z.close()
    memstream.close()
    #print('zclosed')
    return

def stream_tar(filenames):
    memstream = Stream()
    zip_thread = threading.Thread(target=_stream_tar, args=(memstream, filenames))
    zip_thread.start()
    while True:
        #print('reading')
        chunk = memstream.read()
        yield chunk
        if not chunk:
            break
    memstream.close()
    #print('ending')
