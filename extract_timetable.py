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


def get_timetable(spreadsheet, user_batch, user_section):
    """Generate timetable using color-based matching"""
    batch_colors = extract_batch_colors(spreadsheet)

    # Find target color for user's batch
    target_color = None
    for color, batch in batch_colors.items():
        if user_batch == batch:
            target_color = color
            break

    if not target_color:
        return f"⚠️ Batch '{user_batch}' not found!"

    output = []
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
            is_lab = row_idx >= lab_time_row_index + 1  # Lab rows start after detected lab timings row

            # Extract room number dynamically
            room = "Unknown"
            row_values = row.get('values', []) if isinstance(row, dict) else []
            if row_values:
                first_cell = row_values[0] if isinstance(row_values[0], dict) else {}
                room = first_cell.get('formattedValue', 'Unknown').strip()

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

                        # Extract time slot using the column index
                        time_slot = "Unknown"
                        time_row = lab_time_row if is_lab else class_time_row
                        if time_row:
                            time_values = time_row.get('values', [])
                            if len(time_values) > col_idx:  # Ensure valid index
                                time_slot = time_values[col_idx].get('formattedValue', 'Unknown')

                        # Dynamic label: "Room" or "Lab"
                        room_or_lab_label = "Lab" if is_lab else "Room"

                        entry = (
                            f"📌 {sheet_name}: {time_slot} | 🏫 {room_or_lab_label}: {room} | "
                            f"{'Lab' if is_lab else 'Class'}: {clean_entry} \n"
                        )
                        output.append(entry)

    return "\n".join(output) if output else "⚠️ No classes found for selected criteria"


