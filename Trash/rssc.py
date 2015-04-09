import urllib.request

URL_BASIC = 'http://socialclub.rockstargames.com/'
URL_USER = 'http://socialclub.rockstargames.com/member/reddragon'
URL_SIGNIN = "https://socialclub.rockstargames.com/profile/signincompact"
HTML_KEYBREAK = 'input name="__RequestVerificationToken" type="hidden" value="'
KEY_USERNAME = 'login'
KEY_PASSWORD = 'password'
KEY_REMEMBERME = 'rememberme'
KEY_TOKEN = '__RequestVerificationToken'


USERNAME = 'ctU8BYeD'
PASSWORD = 'ctU8BYeD'
USERAGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'
REFERER = 'http://socialclub.rockstargames.com/member/'
CONTENTTYPE = 'application/x-www-form-urlencoded'
HOST = 'socialclub.rockstargames.com'
ORIGIN = 'http://socialclub.rockstargames.com'
ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
ENCODING = 'gzip, deflate'

def prepare_request(url, method='GET', cookies=None):
	request = urllib.request.Request(url, method=method)

	request.headers['User-Agent'] = USERAGENT
	request.headers['Accept'] = ACCEPT
	request.headers['Referer'] = REFERER
	request.headers['Content-Type'] = CONTENTTYPE
	request.headers['Host'] = HOST
	request.headers['Origin'] = ORIGIN
	#request.headers['Accept-Encoding'] = ENCODING
	if cookies:
		request.headers['Cookie'] = cookies
	request.headers['Connection'] = 'keep-alive'
	return request

def login():
	basic = prepare_request(URL_BASIC)
	basic = urllib.request.urlopen(basic)
	cookies = str(basic.headers)
	cookies = cookies.split('\n')
	cookies = [h for h in cookies if 'Set-Cookie' in h]
	cookies = ';'.join([h.split(': ')[1] for h in cookies])
	print(cookies)
	basic = basic.read()
	basic = basic.decode('utf-8', 'ignore')
	basic = basic.split(HTML_KEYBREAK)[1]
	token = basic.split('"')[0]
	del basic
	print(token)

	log = prepare_request(URL_SIGNIN, method='POST', cookies=cookies)
	log.data = ''
	log.data += '%s=%s&' % (KEY_USERNAME, USERNAME)
	log.data += '%s=%s&' % (KEY_PASSWORD, PASSWORD)
	log.data += '%s=%s&' % (KEY_TOKEN, token)
	log.data += '%s=true' % (KEY_REMEMBERME)
	log.data = log.data.encode('utf-8')

	results = urllib.request.urlopen(log)
	print(results.status)
	print(dir(results))
	print(results.headers)
	print(results.read())


login()
