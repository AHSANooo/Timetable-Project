import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


def get_google_sheets_data(sheet_url):
    """Fetch Google Sheets file as a gspread object."""
    credentials_dict = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=["https://spreadsheets.google.com/feeds",
                                                                            "https://www.googleapis.com/auth/drive"])

    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)

    return sheet
