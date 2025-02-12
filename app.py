import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924#gid=1882612924"

def main():
    st.title("FAST-NUCES FCS Timetable System 📅")

    # ✅ Fetch Google Sheets data in memory
    sheet = get_google_sheets_data(SHEET_URL)

    # User input
    batch = st.text_input("Enter Batch (e.g., 'BS CS 2023')").strip()
    section = st.text_input("Enter Section (e.g., 'A')").strip()

    # Display timetable
    if st.button("Show Timetable"):
        schedule = get_timetable(sheet, batch, section)
        st.text(schedule)

if __name__ == "__main__":
    main()
