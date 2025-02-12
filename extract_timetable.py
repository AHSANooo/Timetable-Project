from openpyxl import load_workbook
from openpyxl.styles import PatternFill

def extract_batch_colors(file_path):
    """Extract batch colors from the timetable file."""
    wb = load_workbook(filename=file_path, data_only=True)
    batch_colors = {}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]

        for col in ws.iter_cols(min_row=1, max_row=5):  # Check first 5 rows for batch info
            for cell in col:
                if cell.value and isinstance(cell.value, str) and "BS" in cell.value:
                    color = cell.fill.start_color.rgb
                    if color and color != "00000000":  # Ignore empty colors
                        batch_colors[color] = cell.value.strip()

    return batch_colors

def get_timetable(file_path, user_batch, user_section):
    """Fetch the timetable for a specific batch and section based on color."""
    wb = load_workbook(filename=file_path, data_only=True)
    batch_colors = extract_batch_colors(file_path)

    batch_color = None
    for color, batch_name in batch_colors.items():
        if user_batch in batch_name:
            batch_color = color
            break

    if not batch_color:
        return f"❌ Batch '{user_batch}' not found!"

    output = [f"📅 Timetable for {user_batch}, Section {user_section}:"]

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        day_schedule = [f"\n📌 {sheet_name}:"]

        for row in ws.iter_rows(min_row=6):  # Start from row 6 (assuming first rows are headers)
            time_slot = row[0].value
            section_found = False

            for cell in row:
                if cell.fill.start_color.rgb == batch_color and isinstance(cell.value, str):
                    if f"({user_section})" in cell.value:  # Ensure section match
                        section_found = True
                        subject = cell.value.strip()
                        if subject:
                            day_schedule.append(f"🕒 {time_slot} - {subject}")

            if not section_found:
                continue

        if len(day_schedule) > 1:
            output.append("\n".join(day_schedule))

    return "\n".join(output) if len(output) > 1 else f"❌ No classes found for {user_batch} - Section {user_section}."

