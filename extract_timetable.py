import pandas as pd
import gspread
from openpyxl.styles import PatternFill

import streamlit as st
def extract_batch_colors(spreadsheet):
    """Extract batch colors from Google Sheets for relevant timetable sheets."""
    batch_colors = {}

    # Define sheets to check (Skipping the first sheet)
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}  # Get all sheets

    for sheet_name in timetable_sheets:
        if sheet_name not in worksheets:
            st.warning(f"⚠️ Sheet '{sheet_name}' not found, skipping.")
            continue

        ws = worksheets[sheet_name]  # Get the correct worksheet
        data = ws.get_all_values()

        if not data:
            st.warning(f"⚠️ No data found in '{sheet_name}', skipping.")
            continue

        st.write(f"📋 Checking batches in '{sheet_name}'...")  # Debugging

        for col_idx in range(len(data[0])):  # Iterate over first row columns
            for row_idx in range(min(5, len(data))):  # Check only the first 5 rows
                if col_idx >= len(data[row_idx]):
                    continue  # Skip if column doesn't exist

                cell_value = data[row_idx][col_idx].strip()  # Remove extra spaces

                if "BS" in cell_value:  # If cell contains a batch name
                    batch_colors[f"C{col_idx+1}"] = cell_value  # Store batch
                    st.write(f"✅ Found batch: {cell_value} in '{sheet_name}' at Column {col_idx+1}")  # Debugging

    if not batch_colors:
        st.error("❌ No batches detected! Check sheet formatting.")

    return batch_colors



def get_timetable(worksheet, user_batch, user_section):
    """Fetch the timetable for a specific batch and section."""
    batch_colors = extract_batch_colors(worksheet)

    # Find the column where this batch exists
    batch_column = None
    for col, batch_name in batch_colors.items():
        if user_batch in batch_name:
            batch_column = int(col[1:]) - 1  # Convert column label (e.g., C3) to index
            break

    if batch_column is None:
        return "Batch not found!"

    output = [f"Timetable for {user_batch}, Section {user_section}:"]

    data = worksheet.get_all_values()
    for row in data[6:]:  # Start from row 6 (assuming headers above)
        if len(row) <= batch_column:  # Ensure column exists in the row
            continue

        time_slot = row[0]
        if user_section in row[batch_column]:  # Check if section is listed
            subject = row[batch_column].strip()
            if subject:
                output.append(f"{time_slot} - {subject}")

    return "\n".join(output)

