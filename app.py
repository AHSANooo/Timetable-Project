import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import extract_batch_columns, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924"


def main():
    st.title("📅 FAST-NUCES FCS Timetable System")

    # Fetch full spreadsheet object
    st.info("Fetching timetable data, please wait...")
    spreadsheet = get_google_sheets_data(SHEET_URL)

    # Extract batch names correctly
    batch_columns = extract_batch_columns(spreadsheet)

    if not batch_columns:
        st.error("No batches found. Please check if the sheet format is correct.")
        return

    # User inputs
    batch = st.text_input("Enter your batch (e.g., 'BS CS (2023)')").strip()
    section = st.text_input("Enter your section (e.g., 'A')").strip()

    # Display timetable
    if st.button("Show Timetable"):
        if not batch or not section:
            st.warning("Please enter both batch and section.")
            return

        schedule = get_timetable(spreadsheet, batch, section)

        if "Batch not found" in schedule or "No classes found" in schedule:
            st.error(schedule)
        else:
            st.success(f"Timetable for {batch}, Section {section}")
            st.markdown(f"```\n{schedule}\n```")  # Display in a formatted way


if __name__ == "__main__":
    main()
