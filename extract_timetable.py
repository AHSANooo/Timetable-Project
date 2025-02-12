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
    """Extract and filter timetable based on batch and section."""

    # Find batch colors from any valid weekday sheet
    batch_colors = {}
    for sheet_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        worksheet = spreadsheet.worksheet(sheet_name)
        batch_colors = extract_batch_colors(worksheet)
        if batch_colors:
            break  # Stop once we have extracted batch colors

    # Find the color of the user's batch
    batch_color = None
    for color, batch_name in batch_colors.items():
        if user_batch in batch_name:
            batch_color = color
            break

    if not batch_color:
        return "Batch not found!"

    output = [f"📅 Timetable for {user_batch}, Section {user_section}:"]

    for sheet_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_values()  # Get all cell values

        day_schedule = [f"\n📆 {sheet_name}:"]

        for row in data[5:]:  # Start from row 6 (index 5)
            time_slot = row[0]  # First column is the time slot
            section_found = False

            for col_idx, cell_value in enumerate(row[1:], start=1):
                cell_format = worksheet.cell(row=data.index(row) + 1, col=col_idx + 1).format
                cell_color = cell_format.backgroundColor  # Extract color

                if cell_color == batch_color and isinstance(cell_value, str):
                    if user_section in cell_value:
                        section_found = True
                        subject = cell_value.strip()
                        if subject:
                            day_schedule.append(f"{time_slot} - {subject}")

            if section_found:
                output.append("\n".join(day_schedule))

    return "\n".join(output)

