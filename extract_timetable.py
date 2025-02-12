import pandas as pd
import gspread
from openpyxl.styles import PatternFill
import streamlit as st


def extract_batch_colors(spreadsheet):
    """Extract batch colors from Google Sheets for relevant timetable sheets."""
    batch_colors = {}

    # Get all available sheets
    try:
        worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}  # Get all sheets
    except AttributeError:
        raise ValueError("❌ Invalid spreadsheet object. Ensure you're passing the full Google Sheets object.")

    # Sheets to check (skip first sheet)
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        if sheet_name not in worksheets:
            continue  # Skip missing sheets

        ws = worksheets[sheet_name]  # Get correct sheet
        data = ws.get_all_values()  # Get all rows

        if not data:
            continue  # Skip empty sheets

        for col_idx in range(len(data[0])):  # Check first row
            for row_idx in range(min(5, len(data))):  # Check first 5 rows
                if col_idx >= len(data[row_idx]):
                    continue  # Skip invalid columns

                cell_value = data[row_idx][col_idx].strip()  # Remove spaces

                if "BS" in cell_value:  # If batch name found
                    batch_colors[f"C{col_idx+1}"] = cell_value  # Store batch

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

