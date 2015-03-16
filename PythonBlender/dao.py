
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

app_key = '33g92yzpn2tivdk'
app_secret = 'r95jod5npowzz2n'

class DropboxAccess():
    TOKEN_FILE = "token_store.txt"

    def __init__(self):
        self.app_key = app_key
        self.app_secret = app_secret
        self.current_path = ''
        self.api_client = None
        try:
            print(self.TOKEN_FILE)
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
        
    def upload_file(self, filename, destination):
        """upload"""
        f = open(filename, 'rb')
        self.api_client.put_file(destination, f, True)
        
    def download_file(self, filename, destination):
        """download"""
        f, metadata = self.api_client.get_file_and_metadata(filename)
        out = open(destination, 'wb')
        out.write(f.read())
        out.close()
    
    def update_file(self, directory, line, mode):
        with open(directory, mode) as f:
            f.write(line)

if __name__=="__main__":
    if app_secret == '' or app_key == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    os.path.dirname(os.path.realpath(__file__))
    term = DropboxAccess()
