from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def get_google_sheets_data(sheet_url):
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file('path/to/credentials.json', scopes=scopes)
    service = build('sheets', 'v4', credentials=creds)

    spreadsheet_id = sheet_url.split('/d/')[1].split('/')[0]
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        includeGridData=True
    ).execute()

    return spreadsheet