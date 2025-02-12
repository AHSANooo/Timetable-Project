import streamlit as st
import json
from google.oauth2.service_account import Credentials
import gspread

def get_google_sheets_data(sheet_url):
    credentials_dict = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    return client.open_by_url(sheet_url)
