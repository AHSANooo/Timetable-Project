import gspread

def extract_batch_columns(spreadsheet):
    """Extract batch names along with their column indices, accounting for merged cells."""
    batch_columns = {}

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            continue

        if not data or len(data) < 5:
            continue

        for row_idx in range(4):  # Scan first 4 rows for batch names
            row = data[row_idx]
            col_idx = 0

            while col_idx < len(row):
                cell_value = row[col_idx].strip()
                if "BS" in cell_value:
                    # Ensure batch spans two columns
                    if col_idx + 1 < len(row):
                        batch_columns[cell_value] = (col_idx, col_idx + 1)
                    else:
                        batch_columns[cell_value] = (col_idx, col_idx)  # Handle single-column cases
                col_idx += 1  # Move to next column

    print(f"[DEBUG] Extracted Batch Columns: {batch_columns}")  # Debugging output
    return batch_columns


def get_timetable(spreadsheet, user_batch, user_section):
    """Extract timetable ensuring correct batch-column mapping and section filtering."""
    batch_columns = extract_batch_columns(spreadsheet)

    if user_batch not in batch_columns:
        return f"⚠️ Batch '{user_batch}' not found! Please enter a valid batch."

    batch_col_start, batch_col_end = batch_columns[user_batch]
    output = [f"📅 Timetable for {user_batch}, Section {user_section}:\n"]

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            continue

        if len(data) < 6:
            continue

        section_classes = []
        class_timings = data[4]  # Row 5 contains class timings
        lab_timings = data[42] if len(data) > 43 else []  # Row 43 contains lab timings
        room_column = batch_col_start - 1  # Room numbers column is before batch start

        for row_idx, row in enumerate(data[5:], start=6):  # Start from row 6
            if len(row) > batch_col_end:
                class_entry = " ".join(row[batch_col_start:batch_col_end + 1]).strip()

                # Verify the subject belongs to the requested section
                if f"({user_section})" in class_entry or f"-{user_section}" in class_entry:
                    class_time = class_timings[batch_col_start] if batch_col_start < len(class_timings) else "Unknown Time"
                    room = row[room_column] if room_column >= 0 and len(row) > room_column else "Unknown Room"

                    # Check if it's a lab (Row 43 and beyond)
                    if row_idx >= 43:
                        class_type = "Lab"
                        class_time = lab_timings[batch_col_start] if batch_col_start < len(lab_timings) else class_time
                    else:
                        class_type = "Class"

                    section_classes.append(f"{sheet_name}: {class_time} | Room: {room} | {class_type}: {class_entry}")

        if section_classes:
            output.extend(section_classes)

    return "\n".join(output) if len(output) > 1 else "⚠️ No classes found for the selected batch and section."
