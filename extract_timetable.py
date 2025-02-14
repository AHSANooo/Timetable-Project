from datetime import datetime

def extract_batch_colors(spreadsheet):
    """Extract batch-color mappings from spreadsheet"""
    batch_colors = {}
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        grid_data = sheet.get('data', [{}])[0].get('rowData', [])

        # Check first 4 rows (0-indexed)
        for row_idx in range(4):
            if row_idx >= len(grid_data):
                continue

            row_data = grid_data[row_idx].get('values', [])
            for cell in row_data:
                if 'formattedValue' in cell and 'BS' in cell['formattedValue']:
                    # Get background color
                    color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                    # Convert color to hex string
                    color_hex = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"
                    batch_colors[color_hex] = cell['formattedValue'].strip()

    return batch_colors


def parse_time_slot(time_slot):
    """Extracts the start time from a given time slot string and converts it to a sortable datetime object."""
    if time_slot == "Unknown":
        return datetime.max  # Place unknown times at the end

    # Handle formats like "08:30-09:50 AM"
    time_parts = time_slot.split('-')
    if time_parts:
        first_time = time_parts[0].strip()  # Extract first time part
        try:
            return datetime.strptime(first_time, "%I:%M %p")  # Convert to datetime with AM/PM
        except ValueError:
            pass  # Continue if parsing fails

    return datetime.max  # Default to max if parsing fails



def get_timetable(spreadsheet, user_batch, user_section):
    """Generate timetable using color-based matching and return formatted output"""
    batch_colors = extract_batch_colors(spreadsheet)

    # Find target color for user's batch
    target_color = next((color for color, batch in batch_colors.items() if batch == user_batch), None)

    if not target_color:
        return f"⚠️ Batch '{user_batch}' not found!"

    timetable = {}
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        grid_data = sheet.get('data', [{}])[0].get('rowData', [])
        if len(grid_data) < 6:
            continue

        # Extract class timings (Row 5)
        class_time_row = grid_data[4] if len(grid_data) > 4 else None

        # Detect the correct lab row dynamically
        lab_time_row_index = 42  # Default to row 42
        for i in range(41, 45):  # Search within a small range
            if i < len(grid_data) and "Lab" in str(grid_data[i].get('values', [{}])[0].get('formattedValue', '')):
                lab_time_row_index = i
                break

        lab_time_row = grid_data[lab_time_row_index] if len(grid_data) > lab_time_row_index else None

        # Process timetable rows (skip headers)
        for row_idx, row in enumerate(grid_data[5:], start=6):
            is_lab = row_idx >= lab_time_row_index + 1  # Labs start after detected lab row

            # Extract room number dynamically
            row_values = row.get('values', []) if isinstance(row, dict) else []
            room = row_values[0].get('formattedValue', 'Unknown').strip() if row_values else "Unknown"

            # Check all cells in row
            for col_idx, cell in enumerate(row_values):
                if not isinstance(cell, dict) or 'effectiveFormat' not in cell:
                    continue

                # Get cell color
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                cell_color = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"

                if cell_color == target_color:
                    class_entry = cell.get('formattedValue', '')
                    if class_entry and any(p in class_entry for p in [f"({user_section})", f"-{user_section}"]):
                        # Clean class name
                        clean_entry = class_entry.split('(')[0].split('-')[0].strip()

                        # Extract time slot
                        time_row = lab_time_row if is_lab else class_time_row
                        time_slot = "Unknown"
                        if time_row:
                            time_values = time_row.get('values', [])
                            if len(time_values) > col_idx:
                                time_slot = time_values[col_idx].get('formattedValue', 'Unknown')

                        # Store in dictionary (group by day)
                        if sheet_name not in timetable:
                            timetable[sheet_name] = []

                        timetable[sheet_name].append((parse_time_slot(time_slot), time_slot, room, "Lab" if is_lab else "Class", clean_entry))

    # Format output as a Markdown table
    output = []
    for day, sessions in timetable.items():
        output.append(f"### 📌 {day}\n")
        output.append("| Time | Room | Type | Course |")
        output.append("|------|------|------|--------|")

        # Sort sessions by extracted start time before displaying
        for _, time_slot, room, session_type, course in sorted(sessions, key=lambda x: x[0]):
            output.append(f"| {time_slot} | {room} | {session_type} | {course} |")
        output.append("\n")

    return "\n".join(output) if output else "⚠️ No classes found for selected criteria"
