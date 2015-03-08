from dropbox.datastore import DatastoreManager, Date, DatastoreError
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
    
    def do_logout(self):
        """log out of the current Dropbox account"""
        self.api_client = None
        os.unlink(self.TOKEN_FILE)
        self.current_path = ''
 
    
    def do_datastore(self):
        """show"""
        manager = DatastoreManager(self.api_client)
        datastore = manager.open_default_datastore()
        tasks_table = datastore.get_table('manager')
        tasks = tasks_table.query()
        l = len(tasks)
        print(l)
        for task in tasks:
            print (task.get('taskname'))
    
    def update_task(self, name):
        """update task"""
        manager = DatastoreManager(self.api_client)
        datastore = manager.open_default_datastore()
        tasks_table = datastore.get_table('task')
        tasks = tasks_table.query(taskname = name)
        
        if not tasks:
            print("add new task")
            l = len(tasks_table.query())
            try:
                tasks_table.insert(id = l+1, taskname=name, completed=False)
                datastore.commit()
            except DatastoreConflictError:
                datastore.rollback()    # roll back local changes
                datastore.load_deltas() # load new changes from Dropbox

    def do_help(self):
        # Find every "do_" attribute with a non-empty docstring and print
        # out the docstring.
        all_names = dir(self)
        cmd_names = []
        for name in all_names:
            if name[:3] == 'do_':
                cmd_names.append(name[3:])
        cmd_names.sort()
        for cmd_name in cmd_names:
            f = getattr(self, 'do_' + cmd_name)
            if f.__doc__:
                self.stdout.write('%s: %s\n' % (cmd_name, f.__doc__))
 

    def do_exit(self):
        """exit"""
        return True
 
    # the following are for command line magic and aren't Dropbox-related
    def emptyline(self):
        pass
 
    def do_EOF(self, line):
        self.stdout.write('\n')
        return True
 
    def parseline(self, line):
        parts = shlex.split(line)
        if len(parts) == 0:
            return None, None, line
        else:
            return parts[0], parts[1:], line
 

if __name__=="__main__":
    if app_secret == '' or app_key == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    os.path.dirname(os.path.realpath(__file__))
    term = DropboxAccess()
    print("self")

