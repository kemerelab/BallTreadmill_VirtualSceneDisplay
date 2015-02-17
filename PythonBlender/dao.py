import cmd
import locale
import os
import pprint
import shlex
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from dropbox import client, rest, session

app_key = 'x41qnsve1e8gffl'
app_secret = 'o42m6t2emjq8kqc'

class DropboxAccess():
    TOKEN_FILE = "token_store.txt"

    def __init__(self):
        self.app_key = app_key
        self.app_secret = app_secret
        self.current_path = ''
        self.api_client = None
        try:
            serialized_token = open(self.TOKEN_FILE).read()
            if serialized_token.startswith('oauth2:'):
                access_token = serialized_token[len('oauth2:'):]
                self.api_client = client.DropboxClient(access_token)
                print("[loaded OAuth 2 access token]")
            else:
                print("Malformed access token in %r." % (self.TOKEN_FILE,))
                return
        except:
            flow = client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
            authorize_url = flow.start()
            sys.stdout.write("1. Go to: " + authorize_url + "\n")
            sys.stdout.write("2. Click \"Allow\" (you might have to log in first).\n")
            sys.stdout.write("3. Copy the authorization code.\n")
            code = input("Enter the authorization code here: ").strip()

            try:
                access_token, user_id = flow.finish(code)
            except rest.ErrorResponse:
                self.stdout.write('Error: %s\n' % str(e))
                return

            with open(self.TOKEN_FILE, 'w') as f:
                f.write('oauth2:' + access_token)
            self.api_client = client.DropboxClient(access_token)

if __name__=="__main__":
    if app_secret == '' or app_key == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    os.path.dirname(os.path.realpath(__file__))
    term = DropboxAccess()
    print("self")

