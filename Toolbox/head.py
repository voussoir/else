'''
Perform a HEAD request and print the results.
'''
import sys
import json
import requests

from voussoirkit import clipext

urls = clipext.resolve(sys.argv[1], split_lines=True)
for url in urls:
    page = requests.head(url)
    headers = dict(page.headers)
    headers = json.dumps(headers, indent=4, sort_keys=True)
    print(page)
    print(headers)
