import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import extract_batch_details, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924#gid=1882612924"

def main():
    st.title("University Timetable System 📅")

    # Fetch real-time data
    sheet = get_google_sheets_data(SHEET_URL)
    batch_details = extract_batch_details(sheet)

    if not batch_details:
        st.error("No timetable data found. Please check the sheet format.")
        return

    # User selection
    batch = st.selectbox("Select Batch", sorted(batch_details.keys()))
    dept = st.selectbox("Select Department", sorted(batch_details[batch].keys()))
    section = st.selectbox("Select Section", sorted(batch_details[batch][dept]))

    # Display timetable
    if st.button("Show Timetable"):
        schedule = get_timetable(sheet, batch, dept, section)
        st.text(schedule)

if __name__ == "__main__":
    main()
