import gspread

def extract_batch_colors(spreadsheet):
    """Extract batch names and their corresponding colors from the first four rows."""
    batch_details = {}  # Store batch names and colors
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
            fmt = worksheet.get_format()  # Get cell formatting (color info)
        except gspread.exceptions.WorksheetNotFound:
            continue

        if not data or len(data) < 5:
            continue

        for row_idx in range(4):  # Check first 4 rows for batch names
            for col_idx, cell in enumerate(data[row_idx]):
                if "BS" in cell:
                    color = fmt[row_idx][col_idx].get("backgroundColor", None)
                    batch_details[cell.strip()] = (col_idx, color)  # Store batch name, column index, and color

    return batch_details


def get_timetable(spreadsheet, user_batch, user_section):
    """Extract and filter timetable based on batch, department, and section."""

    batch_details = extract_batch_colors(spreadsheet)

    if user_batch not in batch_details:
        return "Batch not found!"

    batch_column, batch_color = batch_details[user_batch]  # Get column index and color
    output = [f"📅 Timetable for {user_batch}, Section {user_section}:\n"]

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
            fmt = worksheet.get_format()  # Get cell formatting (for color matching)
        except gspread.exceptions.WorksheetNotFound:
            continue

        if len(data) < 6:
            continue

        section_classes = []
        class_timings = data[4]  # Row 5 contains class timings
        lab_timings = data[42] if len(data) > 43 else []  # Row 43 contains lab timings
        room_columns = batch_column - 1  # Room number column

        for row_idx, row in enumerate(data[5:], start=6):  # Start from row 6
            if len(row) > batch_column:
                class_entry = row[batch_column].strip()

                # Ensure this class is for the correct batch by matching the color
                cell_color = fmt[row_idx][batch_column].get("backgroundColor", None)
                if cell_color != batch_color:
                    continue  # Skip if color doesn't match the batch

                # Ensure the class is for the correct section
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
