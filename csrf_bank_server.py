#!/usr/bin/python
'''
Cross Site Request Forgery Demo
-------------------------------
Author: Adrian Stoll
Date: May 27, 2017
Description: Here is a simple website that is vulnerable to CSRF
'''

import base64, cgi, os, sys, urlparse
from twisted.web.server import Site
from twisted.web import server, resource
from twisted.internet import reactor, endpoints
from twisted.web.util import redirectTo

users = {
	'victim': {'password':'unhashed', 'session_cookie': None, 'balance': 10000},
	'dr evil': {'password':'mini me', 'session_cookie': None, 'balance': 0}
}

def getUser(session_cookie):
	if not session_cookie: return None
	for username in users:
		user = users[username]
		if user['session_cookie'] == session_cookie:
			return {
				'username': username,
				'balance': user['balance']
			}
	return None

class BankSite(resource.Resource):
	isLeaf = True
	def notFound(self, request):
		request.setResponseCode(404)
		return '404'

	def error(self, msg):
		content = '''
		<html>
			<p>error: %s</p>
			<a href="/">Home</a>
		</html>
		'''
		return content % cgi.escape(msg)

	def login(self, request):
		params = urlparse.parse_qs(request.content.read())
		#if valid request
		if 'username' not in params or 'password' not in params:
			return self.error('invalid post request')
		username = params['username'][0]
		password = params['password'][0]
		user = users.get(username)

		if not user or password != user['password']:
			return self.error('invalid user name or password')

		#give then session cookie
		session_cookie = base64.b64encode(os.urandom(16))
		user['session_cookie'] = session_cookie
		#TODO: set secure=True
		request.addCookie('session_cookie', session_cookie)
		return redirectTo('/', request)

	def logout(self, request):
		user = getUser(request.getCookie('session_cookie'))
		if user:
			users[user['username']]['session_cookie'] = None
		return redirectTo('/', request)

	def transfer(self, request):
		params = urlparse.parse_qs(request.content.read())
		if 'dest' not in params or 'amount' not in params:
			return self.error('invalid post request')
		dest = params['dest'][0]
		amount = params['amount'][0]

		if not amount.isdigit():
			return self.error('invalid transfer amount')
		amount = int(amount)

		if dest not in users:
			return self.error('recipient not found')

		session_cookie = request.getCookie('session_cookie')
		user = getUser(session_cookie)

		if not user:
			return self.error('you are not logged in')
		if int(amount) > user['balance']:
			return self.error('insufficient funds')

		users[user['username']]['balance'] -= amount
		users[dest]['balance'] += amount

		return '<html>Transfer Successful <a href="/">Home</a><html>'

	def render_POST(self, request):
		if request.path == '/login':
			return self.login(request)
		if request.path == '/transfer':
			return self.transfer(request)
		return self.notFound(request)

	def render_GET(self, request):
		if request.path == '/logout':
			return self.logout(request)

		if request.path not in ['', '/', '/index.html']:
			return self.notFound(request)

		#see if user is logged in
		user = getUser(request.getCookie('session_cookie'))
		if user:
			username = cgi.escape(user['username'])
			balance  = user['balance']
			return '''
<html>
<body>
<h1>Bank of CSRF</h1>
<form action="/transfer" method="post">
	%s's balance: %d</br>
	Destination account: <input type="text" name="dest" /></br>
	Transfer amount: <input type="number" name="amount" min="0" max="%d" /></br>
	<input type="submit" value="Transfer" />
</form>
<a href="/logout">Logout</a>
</body>
</html>''' % (username, balance, balance)
		else:
			return  '''
<html>
<body>
<h1>Bank of CSRF</h1>
<form action="/login" method="post">
		username: <input type="text" name="username" />
		password: <input type="password" name="password" />
		<input type="submit" value="Login" />
</form>
</body>
</html>'''

def usage():
	print "usage: %s [port]" % sys.argv[0]
	sys.exit(1)

if __name__ == '__main__':
	if len(sys.argv) == 1:
		port = 8080
	elif len(sys.argv) == 2:
		if not sys.argv[1].isdigit():
			usage()
		port = int(sys.argv[1])
		if port <= 0 or port >= (1<<16): usage()
	else:
		usage()

	reactor.listenTCP(port, Site(BankSite()))
	print 'starting server on port %s...' % port
	reactor.run()
