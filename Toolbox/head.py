'''
Perform a HEAD request and print the results.
'''
import sys
import json
import requests

from voussoirkit import clipext

url = clipext.resolve(sys.argv[1])
page = requests.head(url)
headers = dict(page.headers)
headers = json.dumps(headers, indent=4, sort_keys=True)
print(page)
print(headers)
