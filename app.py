import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import extract_batch_colors, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924#gid=1882612924"

def main():
    st.title("FAST-NUCES FCS Timetable System 📅")

    # Fetch full spreadsheet object (not just one worksheet)
    spreadsheet = get_google_sheets_data(SHEET_URL)

    # Extract batch details correctly
    batch_details = extract_batch_colors(spreadsheet)  # Pass full spreadsheet object

    if not batch_details:
        st.error("No timetable data found. Please check the sheet format.")
        return

    # User selection
    batch = st.selectbox("Select Batch", sorted(batch_details.values()))
    section = st.text_input("Enter Section (e.g., 'A')")

    # Display timetable
    if st.button("Show Timetable"):
        schedule = get_timetable(spreadsheet, batch, section)  # Pass full spreadsheet
        st.text(schedule)

if __name__ == "__main__":
    main()
