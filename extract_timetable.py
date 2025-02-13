def extract_batch_columns(spreadsheet):
    """Extract batches with merged ranges and colors"""
    batch_entries = {}
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        merges = sheet.get('merges', [])
        grid_data = sheet.get('data', [{}])[0].get('rowData', [])

        # Process first 4 rows (0-3)
        for row_idx in range(4):
            if row_idx >= len(grid_data):
                continue

            row_data = grid_data[row_idx].get('values', [])
            for col_idx, cell in enumerate(row_data):
                cell_value = cell.get('formattedValue', '')
                if "BS" not in cell_value:
                    continue

                # Find merged range
                merged_range = next(
                    (m for m in merges if
                     m['startRowIndex'] <= row_idx <= m['endRowIndex'] - 1 and
                     m['startColumnIndex'] <= col_idx <= m['endColumnIndex'] - 1),
                    None
                )

                if merged_range:
                    start_col = merged_range['startColumnIndex']
                    end_col = merged_range['endColumnIndex'] - 1
                else:
                    start_col = end_col = col_idx

                # Get color
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})

                batch_name = cell_value.strip()
                entry = {
                    'sheet': sheet_name,
                    'start_col': start_col,
                    'end_col': end_col,
                    'color': color
                }

                if batch_name not in batch_entries:
                    batch_entries[batch_name] = []
                batch_entries[batch_name].append(entry)

    return batch_entries


def get_timetable(spreadsheet, user_batch, user_section):
    """Generate timetable with proper room assignments and lab handling"""
    batch_entries = extract_batch_columns(spreadsheet).get(user_batch, [])
    if not batch_entries:
        return "Batch not found!"

    output = []
    for entry in batch_entries:
        sheet_name = entry['sheet']
        start_col = entry['start_col']
        end_col = entry['end_col']
        target_color = entry['color']

        sheet_data = next(
            (s for s in spreadsheet['sheets'] if s['properties']['title'] == sheet_name),
            None
        )
        if not sheet_data:
            continue

        grid_data = sheet_data.get('data', [{}])[0].get('rowData', [])
        class_timings = grid_data[4].get('values', []) if len(grid_data) > 4 else []
        lab_timings = grid_data[42].get('values', []) if len(grid_data) > 42 else []

        # Process class rows (5-41) and lab rows (42+)
        for row_idx, row in enumerate(grid_data[5:], start=5):
            row_values = row.get('values', [])
            is_lab = row_idx >= 42

            # Check all columns in the batch's merged range
            for col in range(start_col, end_col + 1):
                if col >= len(row_values):
                    continue

                cell = row_values[col]
                if cell.get('effectiveFormat', {}).get('backgroundColor', {}) != target_color:
                    continue

                class_entry = cell.get('formattedValue', '').strip()
                if not class_entry or f"({user_section})" not in class_entry:
                    continue

                # Get timing from appropriate row
                timing_col = start_col
                if is_lab:
                    time_data = lab_timings[timing_col].get('formattedValue', '') if timing_col < len(
                        lab_timings) else ''
                else:
                    time_data = class_timings[timing_col].get('formattedValue', '') if timing_col < len(
                        class_timings) else ''

                # Get room number (column before batch columns)
                room_col = start_col - 1
                room = row_values[room_col].get('formattedValue', '') if room_col >= 0 else ''

                # Format entry
                entry = (
                    f"{sheet_name}: {time_data} | Room: {room} | "
                    f"{'Lab' if is_lab else 'Class'}: {class_entry}"
                )
                output.append(entry)

    return "\n".join(output) if output else "No classes found."