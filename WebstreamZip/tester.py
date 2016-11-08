import webstreamzip

g = webstreamzip.stream_zip({'C:\\git\\else\\readme.md':'michael.md'})

x = open('test.zip', 'wb')
for chunk in g:
    x.write(chunk)