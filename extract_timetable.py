import gspread

def extract_batch_colors(spreadsheet):
    """Extract batch names from the first four rows of each timetable sheet."""
    batch_colors = {}

    # Define timetable sheets
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()  # Read all values from the sheet
        except gspread.exceptions.WorksheetNotFound:
            continue  # Skip if sheet is missing

        if not data or len(data) < 5:
            continue  # Ensure the sheet has enough rows

        # Iterate over the first four rows to find batch names
        for row in data[:4]:  # Only check first 4 rows
            for cell in row:
                if "BS" in cell:
                    batch_colors[cell] = cell  # Store batch name

    return batch_colors


def get_timetable(spreadsheet, user_batch, user_section):
    """Extract and filter timetable based on batch and section."""

    batch_colors = extract_batch_colors(spreadsheet)

    # Ensure batch exists
    if user_batch not in batch_colors:
        return "Batch not found!"

    output = [f"📅 Timetable for {user_batch}, Section {user_section}:"]

    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet_name in timetable_sheets:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            continue

        if not data or len(data) < 5:
            continue

        day_schedule = [f"\n📆 {sheet_name}:"]

        class_timings = data[4]  # 5th row contains class timings
        lab_timings = data[42] if len(data) > 42 else []  # 43rd row contains lab timings

        for row_idx, row in enumerate(data[5:], start=6):  # Start from row 6
            time_slot = class_timings[row_idx - 5] if row_idx - 5 < len(class_timings) else "Unknown Time"

            for col_idx, cell_value in enumerate(row[1:], start=1):  # Skip first column
                if isinstance(cell_value, str) and user_section in cell_value:
                    subject = cell_value.strip()
                    day_schedule.append(f"{time_slot} - {subject}")

        # Process lab timings separately
        if lab_timings:
            lab_schedule = []
            for col_idx, lab_cell in enumerate(lab_timings[1:], start=1):
                if isinstance(lab_cell, str) and user_section in lab_cell:
                    subject = lab_cell.strip()
                    time_slot = "Lab Time"  # Since lab timing is fixed
                    lab_schedule.append(f"{time_slot} - {subject}")

            if lab_schedule:
                day_schedule.append("\n🔬 Labs:")
                day_schedule.extend(lab_schedule)

        if len(day_schedule) > 1:
            output.append("\n".join(day_schedule))

    return "\n".join(output)
