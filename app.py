import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from extract_timetable import extract_batch_columns, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924"

def get_google_sheets_data(sheet_url):
    """Fetch Google Sheets file as a gspread object."""
    credentials_dict = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=["https://spreadsheets.google.com/feeds",
                                                                            "https://www.googleapis.com/auth/drive"])

    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)

    return sheet

def main():
    st.title("📅 FAST-NUCES FCS Timetable System")

    # Fetch full spreadsheet object
    spreadsheet = get_google_sheets_data(SHEET_URL)

    if not spreadsheet:
        st.error("❌ Error: Failed to connect to Google Sheets. Check your credentials.")
        return

    # Extract all batch names correctly
    batch_details = extract_batch_columns(spreadsheet)

    if not batch_details:
        st.error("⚠️ No batches found. Please check if the sheet format is correct.")
        return

    # Display available batches for reference
    st.write("✅ **Available Batches:**")
    for batch in batch_details.keys():
        st.write(f"- {batch}")

    # User inputs
    batch = st.text_input("🆔 Enter your batch (e.g., 'BS SE (2021)')").strip()
    section = st.text_input("🔠 Enter your section (e.g., 'A')").strip()

    # Display timetable
    if st.button("📅 Show Timetable"):
        if not batch or not section:
            st.warning("⚠️ Please enter both batch and section.")
        else:
            schedule = get_timetable(spreadsheet, batch, section)
            st.text(schedule)

if __name__ == "__main__":
    main()
