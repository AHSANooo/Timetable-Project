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


def analyze_sheet_structure(grid_data, sheet_name):
    """Analyze sheet structure to help with debugging room extraction"""
    print(f"\n=== Analyzing {sheet_name} sheet structure ===")
    
    # Analyze first 10 rows to understand the layout
    for row_idx in range(min(10, len(grid_data))):
        row_values = grid_data[row_idx].get('values', [])
        print(f"Row {row_idx}: ", end="")
        for col_idx, cell in enumerate(row_values):
            if 'formattedValue' in cell and cell['formattedValue'].strip():
                print(f"[{col_idx}:'{cell['formattedValue']}'] ", end="")
        print()
    
    print("=" * 50)


def clean_room_data(room_text):
    """Clean and validate room data to ensure consistent format"""
    if not room_text or room_text == "Unknown":
        return "Unknown"
    
    # Remove extra whitespace and normalize
    room_text = room_text.strip()
    
    # Remove common prefixes/suffixes that might be added accidentally
    prefixes_to_remove = ['room', 'room no', 'room number', 'location', 'venue']
    for prefix in prefixes_to_remove:
        if room_text.lower().startswith(prefix):
            room_text = room_text[len(prefix):].strip()
    
    # Handle special cases like "Room No. 405" -> "405"
    if room_text.lower().startswith('no.'):
        room_text = room_text[3:].strip()
    elif room_text.lower().startswith('no '):
        room_text = room_text[3:].strip()
    
    # Remove extra punctuation
    room_text = room_text.strip('.,;:')
    
    # If the result is empty or just whitespace, return Unknown
    if not room_text or room_text.isspace():
        return "Unknown"
    
    return room_text


def find_room_column(grid_data):
    """Find the column index that contains room information by looking for room-related headers"""
    room_keywords = ['room', 'rooms', 'room no', 'room number', 'location', 'venue']
    
    # Search through the first few rows to find room headers
    for row_idx in range(min(10, len(grid_data))):
        row_values = grid_data[row_idx].get('values', [])
        for col_idx, cell in enumerate(row_values):
            if 'formattedValue' in cell:
                cell_value = cell['formattedValue'].strip().lower()
                if any(keyword in cell_value for keyword in room_keywords):
                    return col_idx
    
    # If no room header found, try to find by pattern (looking for room-like values)
    for row_idx in range(min(10, len(grid_data))):
        row_values = grid_data[row_idx].get('values', [])
        for col_idx, cell in enumerate(row_values):
            if 'formattedValue' in cell:
                cell_value = cell['formattedValue'].strip()
                # Look for patterns like "Room 101", "101", "Lab 1", etc.
                if (cell_value and 
                    (cell_value.isdigit() or 
                     'room' in cell_value.lower() or 
                     'lab' in cell_value.lower() or
                     any(char.isdigit() for char in cell_value))):
                    return col_idx
    
    # Default to first column if no room column found
    # Default to first column if no room column found
    return 0


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

        # Analyze sheet structure for debugging (uncomment for debugging)
        # analyze_sheet_structure(grid_data, sheet_name)

        # Find the room column dynamically
        room_column = find_room_column(grid_data)

        # Extract class timings (Row 5)
        class_time_row = grid_data[4] if len(grid_data) > 4 else None

        # Detect the correct lab row dynamically by searching for 'Lab' in first column
        lab_time_row_index = None
        lab_time_row = None
        
        # Search through all rows to find the one containing 'Lab' in the first column
        for i in range(len(grid_data)):
            row_values = grid_data[i].get('values', [])
            if row_values:
                first_cell_value = row_values[0].get('formattedValue', '').strip()
                if 'Lab' in first_cell_value:
                    lab_time_row_index = i
                    lab_time_row = grid_data[i]
                    break

        # Process timetable rows (skip headers)
        for row_idx, row in enumerate(grid_data[5:], start=6):
            # Determine if this is a lab row based on whether we found a lab timing row
            # and if the current row is after the lab timing row
            is_lab = lab_time_row_index is not None and row_idx >= lab_time_row_index + 1

            # Extract room number from the correct column
            row_values = row.get('values', []) if isinstance(row, dict) else []
            room = "Unknown"
            
            # First try the detected room column
            if row_values and len(row_values) > room_column:
                room_cell = row_values[room_column]
                if 'formattedValue' in room_cell:
                    room = room_cell['formattedValue'].strip()
            
            # If room is still unknown or empty, search for room info in other columns
            if not room or room == "Unknown":
                for col_idx, cell in enumerate(row_values):
                    if col_idx != room_column and 'formattedValue' in cell:
                        cell_value = cell['formattedValue'].strip()
                        # Look for room-like patterns
                        if (cell_value and 
                            (cell_value.isdigit() or 
                             'room' in cell_value.lower() or 
                             'lab' in cell_value.lower() or
                             'class' in cell_value.lower() or
                             any(char.isdigit() for char in cell_value))):
                            room = cell_value
                            break
            
            # If still no room found, try to extract from the first non-empty cell
            if not room or room == "Unknown":
                for cell in row_values:
                    if 'formattedValue' in cell and cell['formattedValue'].strip():
                        potential_room = cell['formattedValue'].strip()
                        # Skip if it looks like a course name or time
                        if (not any(keyword in potential_room.lower() for keyword in ['am', 'pm', ':', '-']) and
                            not any(keyword in potential_room.lower() for keyword in ['cs-', 'bs-', 'semester', 'batch'])):
                            room = potential_room
                            break
            
            # Clean the room data
            room = clean_room_data(room)

            # Check all cells in row
            for col_idx, cell in enumerate(row_values):
                if not isinstance(cell, dict) or 'effectiveFormat' not in cell:
                    continue

                # Get cell color
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                cell_color = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"

                if cell_color == target_color:
                    class_entry = cell.get('formattedValue', '')
                    # More strict section filtering - check for exact section matches
                    section_match = False
                    if class_entry:
                        # Check for patterns like "(CS-E)", "-E", "(E)", etc.
                        section_patterns = [
                            f"(CS-{user_section})",  # Pattern like "(CS-E)"
                            f"-{user_section}",      # Pattern like "-E"
                            f"({user_section})",     # Pattern like "(E)"
                            f" {user_section} "      # Pattern like " E " (with spaces)
                        ]
                        section_match = any(pattern in class_entry for pattern in section_patterns)
                    
                    if class_entry and section_match:
                        # Clean class name - remove section info
                        clean_entry = class_entry
                        # Remove section patterns from the course name
                        for pattern in section_patterns:
                            clean_entry = clean_entry.replace(pattern, '').strip()
                        # Also remove any remaining parentheses and clean up
                        clean_entry = clean_entry.replace('()', '').strip()
                        if clean_entry.endswith('-'):
                            clean_entry = clean_entry[:-1].strip()

                        # Extract time slot
                        time_row = lab_time_row if (is_lab and lab_time_row is not None) else class_time_row
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
