import gspread


def extract_batch_colors(spreadsheet):
    """Extract batch names and their corresponding column indices from the first four rows."""
    batch_colors = {}

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()  # Read all values from the sheet
        except gspread.exceptions.WorksheetNotFound:
            continue

        if not data or len(data) < 5:
            continue

        # First 4 rows contain batch names
        for col_idx, cell in enumerate(data[0]):
            if "BS" in cell:  # Identify batch names
                batch_colors[cell] = col_idx  # Store batch name and column index

    return batch_colors


def get_timetable(spreadsheet, user_batch, user_section):
    """Extract and filter timetable based on batch and section, including room and lab details."""

    batch_colors = extract_batch_colors(spreadsheet)

    if user_batch not in batch_colors:
        return "Batch not found!"

    batch_column = batch_colors[user_batch]  # Get column index of requested batch
    output = [f"📅 Timetable for {user_batch}, Section {user_section}:\n"]

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            continue

        if len(data) < 5:
            continue

        section_classes = []
        class_timings = data[4]  # Row 5 contains class timings
        room_details = data[3] if len(data) > 3 else ["Unknown"] * len(data[4])  # Row 4 for room numbers
        lab_details = data[42] if len(data) > 42 else [""] * len(data[4])  # Row 43 for labs

        for row in data[5:]:  # Start from row 6, where classes begin
            if len(row) > batch_column:
                class_entry = row[batch_column].strip()

                # Check if the class belongs to the requested section
                if f"({user_section})" in class_entry or f"-{user_section}" in class_entry:
                    class_time = class_timings[batch_column] if batch_column < len(class_timings) else "Unknown Time"
                    room = room_details[batch_column] if batch_column < len(room_details) else "Unknown Room"
                    lab = lab_details[batch_column] if batch_column < len(lab_details) and lab_details[
                        batch_column] else None

                    if lab:
                        section_classes.append(f"{sheet_name}: {class_time} | Lab: {lab} | {class_entry}")
                    else:
                        section_classes.append(f"{sheet_name}: {class_time} | Room: {room} | {class_entry}")

        if section_classes:
            output.extend(section_classes)

    return "\n".join(output) if len(output) > 1 else "No classes found for the selected batch and section."
