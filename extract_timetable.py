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




def get_timetable(spreadsheet, user_batch, user_section):
    """Retrieve the timetable for the given batch and section."""
    batch_colors = extract_batch_colors(spreadsheet)  # Extract batch colors

    batch_color = None
    for color, batch_name in batch_colors.items():
        if user_batch in batch_name:
            batch_color = color
            break

    if not batch_color:
        return "❌ Batch not found!"

    output = [f"📅 Timetable for {user_batch}, Section {user_section}:"]

    # Get the relevant worksheets
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)  # ✅ Fetch correct sheet
        except Exception:
            continue  # Skip missing sheets

        data = worksheet.get_all_values()  # ✅ Ensure we are working with a worksheet
        if not data:
            continue  # Skip empty sheets

        day_schedule = [f"\n📆 {sheet_name}:"]

        for row in data[5:]:  # Skip the first 5 rows (header)
            time_slot = row[0] if len(row) > 0 else None
            section_found = False

            for col_idx, cell_value in enumerate(row):
                if f"C{col_idx+1}" == batch_color and isinstance(cell_value, str):
                    if user_section in cell_value:
                        section_found = True
                        subject = cell_value.strip()
                        if subject:
                            day_schedule.append(f"{time_slot} - {subject}")

            if not section_found:
                continue

        if len(day_schedule) > 1:
            output.append("\n".join(day_schedule))

    return "\n".join(output) if len(output) > 1 else "⛔ No classes found for this batch/section."
