from datetime import datetime
import re

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


def normalize_course_name(name: str) -> str:
    """Normalize course name for comparison: lower-case, remove punctuation and common suffixes like 'lab'."""
    if not name:
        return ""
    s = name.lower().strip()
    # Remove common enclosing punctuation
    s = re.sub(r'[\(\)\[\]\.,;:\-]', ' ', s)
    # Remove common lab/practical words
    s = re.sub(r'\b(lab|lab session|practical|pract)\b', ' ', s)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def is_similar_entry(existing_entry, new_entry) -> bool:
    """Return True if two timetable entries are effectively duplicates.

    Compares time, room, type, section and batch for equality and then compares
    normalized course names to allow skipping rows like "Comp Net" vs "Comp Net Lab".
    """
    # existing_entry/new_entry: tuples (parse_time, time_slot, room, session_type, course, section, batch)
    try:
        _, _, room_e, type_e, course_e, section_e, batch_e = existing_entry
        _, _, room_n, type_n, course_n, section_n, batch_n = new_entry
    except Exception:
        return False

    if room_e != room_n or type_e != type_n or section_e != section_n or batch_e != batch_n:
        return False

    # If normalized names are equal, treat as duplicate
    if normalize_course_name(course_e) == normalize_course_name(course_n):
        return True

    return False


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

    # Try to extract the first HH:MM token
    try:
        m = re.search(r"(\d{1,2}:\d{2})", str(time_slot))
        if not m:
            return datetime.max

        first_time_str = m.group(1)

        # Detect if AM/PM appears anywhere in the slot
        ampm_match = re.search(r"\b(am|pm|AM|PM)\b", str(time_slot))
        if ampm_match:
            # If AM/PM is present, parse using 12-hour format
            ampm = ampm_match.group(1).upper()
            try:
                return datetime.strptime(f"{first_time_str} {ampm}", "%I:%M %p")
            except ValueError:
                pass

        # Otherwise, try 24-hour format first, then 12-hour without AM/PM
        try:
            return datetime.strptime(first_time_str, "%H:%M")
        except ValueError:
            try:
                return datetime.strptime(first_time_str, "%I:%M")
            except ValueError:
                return datetime.max
    except Exception:
        return datetime.max


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


def get_custom_timetable(spreadsheet, selected_courses):
    """Generate timetable for custom selected courses"""
    if not selected_courses:
        return "⚠️ No courses selected. Please select courses first."
    
    timetable = {}
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Create a set of course identifiers for faster lookup
    selected_course_ids = set()
    for course in selected_courses:
        course_id = f"{course['name']}_{course['department']}_{course['section']}_{course['batch']}"
        selected_course_ids.add(course_id)
    
    # Precompute batch color mapping so we can validate the batch for each cell
    batch_colors = extract_batch_colors(spreadsheet)

    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        grid_data = sheet.get('data', [{}])[0].get('rowData', [])
        if len(grid_data) < 6:
            continue

        # Find the room column dynamically
        room_column = find_room_column(grid_data)

        # Extract class timings (Row 5)
        class_time_row = grid_data[4] if len(grid_data) > 4 else None

        # Detect the correct lab row dynamically
        lab_time_row_index = None
        lab_time_row = None
        
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
            is_lab = lab_time_row_index is not None and row_idx >= lab_time_row_index + 1

            # Extract room number
            row_values = row.get('values', []) if isinstance(row, dict) else []
            room = "Unknown"
            
            if row_values and len(row_values) > room_column:
                room_cell = row_values[room_column]
                if 'formattedValue' in room_cell:
                    room = room_cell['formattedValue'].strip()
            
            # Clean the room data
            room = clean_room_data(room)

            # Check all cells in row
            for col_idx, cell in enumerate(row_values):
                if not isinstance(cell, dict) or 'effectiveFormat' not in cell:
                    continue

                # Get cell color
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                cell_color = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"

                class_entry = cell.get('formattedValue', '')
                if class_entry:
                    # Try to match this course with selected courses
                    for selected_course in selected_courses:
                        # Check if this cell matches the selected course (including batch validation)
                        if matches_selected_course(class_entry, selected_course, cell_color, batch_colors):
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

                            entry = (
                                parse_time_slot(time_slot),
                                time_slot,
                                room,
                                "Lab" if is_lab else "Class",
                                selected_course['name'],
                                selected_course['section'],
                                selected_course['batch']
                            )

                            # Avoid adding exact or near-duplicate entries (same time, room, type, section, batch
                            # and similar course name like "Comp Net" vs "Comp Net Lab")
                            already = False
                            for existing in timetable[sheet_name]:
                                if is_similar_entry(existing, entry):
                                    already = True
                                    break
                            if not already:
                                timetable[sheet_name].append(entry)

    # Format output as a Markdown table
    output = []
    for day, sessions in timetable.items():
        output.append(f"### 📌 {day}\n")
        output.append("| Time | Room | Type | Course | Section | Batch |")
        output.append("|------|------|------|--------|---------|-------|")

        # Sort sessions by extracted start time before displaying
        for _, time_slot, room, session_type, course, section, batch in sorted(sessions, key=lambda x: x[0]):
            output.append(f"| {time_slot} | {room} | {session_type} | {course} | {section} | {batch} |")
        output.append("\n")

    return "\n".join(output) if output else "⚠️ No classes found for selected courses"

def matches_selected_course(class_entry, selected_course, cell_color, batch_colors):
    """Check if a class entry matches a selected course"""
    # First check if the course name is in the entry
    if selected_course['name'].lower() not in class_entry.lower():
        return False
    
    # Check if the section matches
    section_patterns = [
        f"(CS-{selected_course['section']})",
        f"-{selected_course['section']}",
        f"({selected_course['section']})",
        f" {selected_course['section']} "
    ]
    
    section_match = any(pattern in class_entry for pattern in section_patterns)
    if not section_match:
        return False

    # Validate batch and department: map cell_color to a batch string (if available)
    # and ensure it corresponds to the selected course's batch (exact match).
    # If exact batch doesn't match, allow same-year only if department also matches.
    batch_from_color = batch_colors.get(cell_color, "") if batch_colors else ""
    selected_batch = selected_course.get('batch', '')
    selected_dept = selected_course.get('department', '')

    def extract_dept_from_batch(batch_str: str) -> str:
        """Extract department token from batch strings like 'BS-CS-1' or 'BS CS (2023)'."""
        if not batch_str:
            return ""
        # Handle dash-separated e.g., BS-CS-1
        if '-' in batch_str:
            parts = batch_str.split('-')
            if len(parts) >= 2:
                return parts[1]
        # Otherwise look for 2-4 uppercase tokens
        tokens = re.findall(r"\b[A-Z]{2,4}\b", batch_str)
        for t in tokens:
            if t != 'BS':
                return t
        return ""

    # If we have a batch/color mapping, use it to validate department and batch
    if batch_from_color:
        dept_from_color = extract_dept_from_batch(batch_from_color)
        # If department is known from color and doesn't match selected, reject
        if dept_from_color and selected_dept and dept_from_color != selected_dept:
            return False

        # If exact batch matches, accept
        if selected_batch and batch_from_color == selected_batch:
            return True

        # Fallback: allow same-year matching only if department matches (or not provided)
        y1 = re.search(r"(20\d{2})", batch_from_color)
        y2 = re.search(r"(20\d{2})", selected_batch)
        if y1 and y2 and y1.group(1) == y2.group(1):
            # ensure department alignment if we can
            if dept_from_color:
                if selected_dept and dept_from_color != selected_dept:
                    return False
                return True
            else:
                # No dept info from color; require department token to be present in class entry
                if selected_dept and selected_dept.lower() not in class_entry.lower():
                    return False
                return True

        return False

    # If no batch/color info is available for the cell, require department to appear in the cell entry
    # to avoid cross-batch matches. This is a conservative fallback.
    if selected_dept:
        if selected_dept.lower() not in class_entry.lower():
            return False

    # If department can't be validated, fall back to name+section match (already checked)
    return True
