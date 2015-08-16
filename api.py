"""Provide an interface for the Google Sheets API
"""
import json

import gspread
from oauth2client.client import SignedJwtAssertionCredentials


def get_gdata_credentials(json_file_path):
    """Return the client_id, client_secret pair from a GData Service Account
    formatted JSON credentials file
    """
    with open(json_file_path, 'r') as json_file:
        credential_dict = json.load(json_file)
    return credential_dict['client_email'], credential_dict['private_key']


def sheets_api_login(creds_path):
    """Return an authorized instance of the `gspread` client
    """
    id_, secret = get_gdata_credentials(creds_path)

    scope = ['https://spreadsheets.google.com/feeds']
    creds = SignedJwtAssertionCredentials(id_, secret, scope)

    return gspread.authorize(creds)
