import io
import gspread
from openpyxl import load_workbook
from openpyxl.styles import PatternFill


def get_timetable(sheet, user_batch, user_section):
    """Fetch the timetable for a specific batch and section from Google Sheets."""

    # ✅ Convert Google Sheet to an in-memory Excel file
    excel_data = sheet.export(format='xlsx')  # Export as Excel binary data
    file_stream = io.BytesIO(excel_data)  # Convert to file-like object

    wb = load_workbook(file_stream, data_only=True)
    batch_colors = extract_batch_colors(wb)

    batch_color = None
    for color, batch_name in batch_colors.items():
        if user_batch in batch_name:
            batch_color = color
            break

    if not batch_color:
        return "Batch not found!"

    output = [f"Timetable for {user_batch}, Section {user_section}:"]

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        day_schedule = [f"\n{sheet_name}:"]

        for row in ws.iter_rows(min_row=6):
            time_slot = row[0].value
            section_found = False

            for cell in row:
                if cell.fill.start_color.rgb == batch_color and isinstance(cell.value, str):
                    if user_section in cell.value:
                        section_found = True
                        subject = cell.value.strip()
                        if subject:
                            day_schedule.append(f"{time_slot} - {subject}")

            if not section_found:
                continue

        if len(day_schedule) > 1:
            output.append("\n".join(day_schedule))

    return "\n".join(output)


def extract_batch_colors(wb):
    """Extract batch colors from the Excel file."""
    batch_colors = {}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]

        for col in ws.iter_cols(min_row=1, max_row=5):  # Checking first 5 rows for batch info
            for cell in col:
                if cell.value and isinstance(cell.value, str) and "BS" in cell.value:
                    color = cell.fill.start_color.rgb
                    if color and color != "00000000":  # Ignore empty colors
                        batch_colors[color] = cell.value

    return batch_colors
