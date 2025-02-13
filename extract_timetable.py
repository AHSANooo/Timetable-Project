def extract_batch_columns(spreadsheet):
    batch_entries = {}
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        merges = sheet.get('merges', [])
        grid_data = sheet.get('data', [{}])[0].get('rowData', [])

        for row_idx in range(4):  # First 4 rows (0-3)
            if row_idx >= len(grid_data):
                continue

            row = grid_data[row_idx].get('values', [])
            for col_idx, cell in enumerate(row):
                cell_value = cell.get('formattedValue', '')
                if "BS" not in cell_value:
                    continue

                # Find merged range for this cell
                merged_range = None
                for merge in merges:
                    start_row = merge['startRowIndex']
                    end_row = merge['endRowIndex'] - 1
                    start_col = merge['startColumnIndex']
                    end_col = merge['endColumnIndex'] - 1

                    if (start_row <= row_idx <= end_row and 
                        start_col <= col_idx <= end_col):
                        merged_range = (start_col, end_col)
                        break

                if merged_range:
                    start_col, end_col = merged_range
                else:
                    start_col = end_col = col_idx

                # Get background color
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})

                batch_name = cell_value.strip()
                key = (sheet_name, start_col, end_col)
                if batch_name not in batch_entries:
                    batch_entries[batch_name] = []
                batch_entries[batch_name].append({
                    'sheet': sheet_name,
                    'start_col': start_col,
                    'end_col': end_col,
                    'color': color
                })

    return batch_entries


