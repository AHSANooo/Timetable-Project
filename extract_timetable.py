import pandas as pd
import gspread
from openpyxl.styles import PatternFill

import streamlit as st

def extract_batch_colors(worksheet):
    """Extract batch colors from the first few rows of Google Sheets."""
    batch_colors = {}
    data = worksheet.get_all_values()

    st.write("🔍 Checking first few rows for batch info:", data[:5])  # Debugging Output

    if not data:
        st.error("❌ No data found in the sheet.")
        return batch_colors

    for col_idx in range(len(data[0])):  # Iterate over columns in the first row
        for row_idx in range(min(5, len(data))):  # Check only available rows
            if col_idx >= len(data[row_idx]):  # Ensure column exists in row
                continue

            cell_value = data[row_idx][col_idx].strip()  # Remove spaces

            if "BS" in cell_value:  # Check if batch name is found
                batch_colors[f"C{col_idx+1}"] = cell_value  # Map column to batch name
                st.write(f"✅ Found batch: {cell_value} at column {col_idx+1}")  # Debugging

    if not batch_colors:
        st.warning("⚠️ No batches detected! Check if the format is correct.")

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

