import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import extract_batch_columns, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924"

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
    st.json(batch_details)  # Display batch mappings in JSON format

    # User inputs
    batch = st.text_input("🆔 Enter your batch (e.g., 'BS CS (2023)')").strip()
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
