import gspread

def extract_batch_columns(spreadsheet):
    """Extract batch names and their corresponding column indices from the first four rows."""
    batch_columns = {}

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()  # Read all values from the sheet
        except gspread.exceptions.WorksheetNotFound:
            continue

        if not data or len(data) < 5:
            continue

        for row_idx in range(4):  # Check first 4 rows for batch names
            for col_idx, cell in enumerate(data[row_idx]):
                if "BS" in cell:  # Identify batch names
                    batch_columns[cell.strip()] = col_idx  # Store batch name and its column index

    return batch_columns


def get_timetable(spreadsheet, user_batch, user_section):
    """Extract and filter timetable based on batch, department, and section."""

    batch_columns = extract_batch_columns(spreadsheet)

    if user_batch not in batch_columns:
        return "Batch not found!"

    batch_column = batch_columns[user_batch]  # Get column index of requested batch
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
        room_columns = batch_column - 1  # Room number is typically before batch column

        for row_idx, row in enumerate(data[5:], start=6):  # Start from row 6
            if len(row) > batch_column:
                class_entry = row[batch_column].strip()

                # Check if the class belongs to the requested section
                if f"({user_section})" in class_entry or f"-{user_section}" in class_entry:
                    class_time = class_timings[batch_column] if batch_column < len(class_timings) else "Unknown Time"
                    room = row[room_columns] if room_columns >= 0 and len(row) > room_columns else "Unknown Room"

                    # Check if it's a lab (row 43 and beyond)
                    if row_idx >= 43:
                        class_type = "Lab"
                        class_time = lab_timings[batch_column] if batch_column < len(lab_timings) else class_time
                    else:
                        class_type = "Class"

                    section_classes.append(f"{sheet_name}: {class_time} | Room: {room} | {class_type}: {class_entry}")

        if section_classes:
            output.extend(section_classes)

    return "\n".join(output) if len(output) > 1 else "No classes found for the selected batch and section."
