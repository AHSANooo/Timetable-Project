import streamlit as st
from google_sheets import get_google_sheets_data
from extract_timetable import extract_batch_columns, get_timetable

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dk0Raaf9gtbSdoMAGZal3y4m1kwr7UiuulxFxDKpM8Q/edit?gid=1882612924"


def main():
    st.title("📅 FAST-NUCES FCS Timetable System")

    st.info("Fetching timetable data, please wait...")
    try:
        spreadsheet = get_google_sheets_data(SHEET_URL)
    except Exception as e:
        st.error(f"Failed to fetch data: {str(e)}")
        return

    batch_columns = extract_batch_columns(spreadsheet)
    if not batch_columns:
        st.error("No batches found. Please check the sheet format.")
        return

    batch = st.text_input("Enter your batch (e.g., 'BS CS (2023)')").strip()
    section = st.text_input("Enter your section (e.g., 'A')").strip().upper()

    if st.button("Show Timetable"):
        if not batch or not section:
            st.warning("Please enter both batch and section.")
            return

        schedule = get_timetable(spreadsheet, batch, section)

        if "not found" in schedule.lower() or "no classes" in schedule.lower():
            st.error(schedule)
        else:
            st.success(f"Timetable for {batch}, Section {section}")
            st.markdown(f"```\n{schedule}\n```")


if __name__ == "__main__":
    main()