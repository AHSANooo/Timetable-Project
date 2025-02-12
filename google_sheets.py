import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets API Setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
CREDS_FILE = 'time-table-project-450013-7023b4e6dd12.json'  # Update this with your downloaded JSON

def get_google_sheets_data(sheet_url):
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_url(sheet_url)
