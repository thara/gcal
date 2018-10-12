import os

from oauth2client import client, tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/calendar'
APPLICATION_NAME = 'gcal'

def get_credentials(client_secret_file, credential_path='credentials.json'):
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_file, SCOPES)
        flow.user_agent = APPLICATION_NAME
        flags = tools.argparser.parse_args(args=[])
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials
