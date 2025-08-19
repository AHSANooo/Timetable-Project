import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from extract_timetable import extract_batch_colors, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1cmDXt7UTIKBVXBHhtZ0E4qMnJrRoexl2GmDFfTBl0Z4/edit?usp=drivesdk"


def get_google_sheets_data(sheet_url):
    """Fetch Google Sheets data with formatting using Sheets API v4"""
    credentials_dict = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        credentials_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )

    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = sheet_url.split('/d/')[1].split('/')[0]

    # Get spreadsheet with cell formatting
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        includeGridData=True
    ).execute()

    return spreadsheet


def main():
    st.title("FAST-NUCES FCS Timetable System")

    # Fetch full spreadsheet data
    st.info("Welcome Everyone!")
    try:
        spreadsheet = get_google_sheets_data(SHEET_URL)
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        return

    # Extract batch-color mappings
    batch_colors = extract_batch_colors(spreadsheet)

    if not batch_colors:
        st.error("⚠️ No batches found. Please check the sheet format.")
        return

    # Dropdown for batch selection
    batch_list = list(batch_colors.values())

    with st.expander("✅ **Select Your Batch and Department:**"):
        batch = st.radio("Select your batch:", batch_list, index=None)

    # User input for section
    section = st.text_input("🔠 Enter your section (e.g., 'A')").strip().upper()

    # Submit button
    if st.button("Show Timetable"):
        if not batch or not section:
            st.warning("⚠️ Please enter both batch and section.")
            return

        schedule = get_timetable(spreadsheet, batch, section)

        if schedule.startswith("⚠️"):
            st.error(schedule)
        else:
            st.markdown(f"## Timetable for **{batch}, Section {section}**")
            st.markdown(schedule)


if __name__ == "__main__":
    main()

    # Footer with support contact and LinkedIn profile
    st.markdown("---")
    st.markdown("📧 **For any issues or support, please contact:** [i230553@isb.nu.edu.pk](mailto:i230553@isb.nu.edu.pk)")

    st.markdown("🔗 **Connect with me on LinkedIn:** [Muhammad Ahsan](https://www.linkedin.com/in/muhammad-ahsan-7612701a7)")

