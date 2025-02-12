import pandas as pd
import gspread
from openpyxl.styles import PatternFill

def extract_batch_colors(worksheet):
    """Extract batch colors from the first few rows of Google Sheets."""
    batch_colors = {}
    data = worksheet.get_all_values()

    for col_idx in range(len(data[0])):  # Iterate over columns
        for row_idx in range(5):  # Check first 5 rows for batch info
            cell_value = data[row_idx][col_idx]
            if "BS" in cell_value:
                # Google Sheets API doesn't provide colors directly, assuming color detection via another approach
                batch_colors[f"C{col_idx+1}"] = cell_value  # Mapping column to batch name
                break

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
        time_slot = row[0]
        if user_section in row[batch_column]:  # Check if section is listed
            subject = row[batch_column].strip()
            if subject:
                output.append(f"{time_slot} - {subject}")

    return "\n".join(output)
