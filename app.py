import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924#gid=1882612924"

def main():
    st.title("📅 FAST-NUCES FCS Timetable System")

    # Fetch real-time data
    sheet = get_google_sheets_data(SHEET_URL)
    worksheet = sheet.sheet1  # Select the first worksheet

    # User input
    batch = st.text_input("Enter Batch (e.g., 'BS CS 2023')")
    section = st.text_input("Enter Section (e.g., 'A')")

    if st.button("Show Timetable"):
        if batch and section:
            schedule = get_timetable(worksheet, batch, section)
            st.text(schedule)
        else:
            st.error("Please enter both Batch and Section.")

if __name__ == "__main__":
    main()
