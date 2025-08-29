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
    def unpack(e):
        # Support multiple tuple shapes used in the code:
        # - (rank, parsed_dt, time_slot, room, type, course)
        # - (rank, parsed_dt, time_slot, room, type, course, section, batch)
        # - (parsed_dt, time_slot, room, type, course, section, batch)
        if not isinstance(e, (list, tuple)):
            return None
        if len(e) == 8:
            _, _, _, room, type_, course, section, batch = e
        elif len(e) == 6:
            _, _, _, room, type_, course = e
            section = ''
            batch = ''
        elif len(e) == 7:
            _, _, room, type_, course, section, batch = e
        else:
            return None
        return (room, type_, course, section, batch)

    a = unpack(existing_entry)
    b = unpack(new_entry)
    if not a or not b:
        return False

    room_e, type_e, course_e, section_e, batch_e = a
    room_n, type_n, course_n, section_n, batch_n = b

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


def build_time_col_rank(grid_data):
    """Detect the time header row and return (time_row, col_rank).

    Strategy:
    - Search the first few rows for a row where the first column contains 'room' (case-insensitive).
      If found, that row holds the room header in col0 and time headers to its right (col_idx >= 1).
    - Otherwise, fallback to row index 4 (if exists) as the time header row and consider times starting at col 0.
    - Build a mapping col_idx -> rank (0-based) for columns that contain a non-empty formattedValue in the time row.
    """
    time_row = None
    start_col = 0
    for i in range(min(10, len(grid_data))):
        row_values = grid_data[i].get('values', [])
        if row_values and isinstance(row_values, list) and len(row_values) > 0:
            first_cell = row_values[0]
            if isinstance(first_cell, dict) and 'formattedValue' in first_cell:
                if 'room' in first_cell['formattedValue'].strip().lower():
                    time_row = grid_data[i]
                    start_col = 1
                    break

    if time_row is None:
        time_row = grid_data[4] if len(grid_data) > 4 else None
        start_col = 0

    col_rank = {}
    if time_row:
        rank = 0
        for col_idx, cell in enumerate(time_row.get('values', [])):
            if col_idx < start_col:
                continue
            if isinstance(cell, dict) and 'formattedValue' in cell and cell['formattedValue'].strip():
                col_rank[col_idx] = rank
                rank += 1

    return time_row, col_rank


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


def parse_embedded_time_info(course_entry):
    """
    Parse embedded time information from course entries like:
    'Func Eng (SE) 09:00-10:45' or 'Islamic (SE) 11:00-12:45'
    
    Returns: (cleaned_course_name, time_slot, has_embedded_time)
    """
    if not course_entry:
        return course_entry, "Unknown", False
    
    # Look for time patterns in the course entry (HH:MM-HH:MM or HH:MM)
    time_pattern = r'\b(\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?)\b'
    time_match = re.search(time_pattern, course_entry)
    
    if time_match:
        # Extract the time portion
        time_slot = time_match.group(1)
        
        # Remove the time portion from the course name
        cleaned_entry = re.sub(time_pattern, '', course_entry).strip()
        
        # Clean up any double spaces or trailing characters
        cleaned_entry = re.sub(r'\s+', ' ', cleaned_entry).strip()
        if cleaned_entry.endswith('-'):
            cleaned_entry = cleaned_entry[:-1].strip()
        
        return cleaned_entry, time_slot, True
    
    return course_entry, "Unknown", False


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

        # Extract class timings (Row 5) and build column rank mapping
        class_time_row, col_rank = build_time_col_rank(grid_data)

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
                        # Check for patterns like "(DEPT-E)", "-E", "(E)", etc.
                        # Extract department from batch for pattern matching
                        dept_from_batch = ""
                        if user_batch:
                            if '-' in user_batch:
                                parts = user_batch.split('-')
                                if len(parts) >= 2:
                                    dept_from_batch = parts[1]
                        
                        section_patterns = [
                            f"({dept_from_batch}-{user_section})" if dept_from_batch else f"({user_section})",  # Pattern like "(DEPT-E)"
                            f"-{user_section}",      # Pattern like "-E"
                            f"({user_section})",     # Pattern like "(E)"
                            f" {user_section} "      # Pattern like " E " (with spaces)
                        ]
                        section_match = any(pattern in class_entry for pattern in section_patterns)

                    if class_entry and section_match:
                        # First, try to parse embedded time information from the course entry itself
                        cleaned_entry, embedded_time, has_embedded_time = parse_embedded_time_info(class_entry)
                        
                        if has_embedded_time:
                            # Use the embedded time from the course entry
                            time_slot = embedded_time
                            # Clean the course name further by removing section patterns
                            clean_entry = cleaned_entry
                            for pattern in section_patterns:
                                clean_entry = clean_entry.replace(pattern, '').strip()
                            clean_entry = clean_entry.replace('()', '').strip()
                            if clean_entry.endswith('-'):
                                clean_entry = clean_entry[:-1].strip()
                        else:
                            # Fall back to the original logic for non-embedded time entries
                            clean_entry = class_entry
                            # Remove section patterns from the course name
                            for pattern in section_patterns:
                                clean_entry = clean_entry.replace(pattern, '').strip()
                            # Also remove any remaining parentheses and clean up
                            clean_entry = clean_entry.replace('()', '').strip()
                            if clean_entry.endswith('-'):
                                clean_entry = clean_entry[:-1].strip()

                            # Extract time slot from header row
                            time_row_for_slot = lab_time_row if (is_lab and lab_time_row is not None) else class_time_row
                            time_slot = "Unknown"
                            if time_row_for_slot:
                                time_values = time_row_for_slot.get('values', [])
                                if len(time_values) > col_idx:
                                    time_slot = time_values[col_idx].get('formattedValue', 'Unknown')
                        
                        rank = col_rank.get(col_idx, 999)

                        # Store in dictionary (group by day)
                        if sheet_name not in timetable:
                            timetable[sheet_name] = []

                        # Entry includes (rank, parsed_time, time_slot, room, type, course)
                        timetable[sheet_name].append((rank, parse_time_slot(time_slot), time_slot, room, "Lab" if is_lab else "Class", clean_entry))

    # Format output as a Markdown table
    output = []
    for day, sessions in timetable.items():
        output.append(f"### 📌 {day}\n")
        output.append("| Time | Room | Type | Course |")
        output.append("|------|------|------|--------|")

        # Sort sessions by column rank then extracted start time before displaying
        for _, _, time_slot, room, session_type, course in sorted(sessions, key=lambda x: (x[0], x[1])):
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

        # Extract class timings (Row 5) and build column rank mapping
        class_time_row, col_rank = build_time_col_rank(grid_data)

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
                            # First, try to parse embedded time information from the course entry itself
                            cleaned_entry, embedded_time, has_embedded_time = parse_embedded_time_info(class_entry)
                            
                            if has_embedded_time:
                                # Use the embedded time from the course entry
                                time_slot = embedded_time
                                course_name = cleaned_entry
                            else:
                                # Fall back to extracting time from header row
                                time_row = lab_time_row if (is_lab and lab_time_row is not None) else class_time_row
                                time_slot = "Unknown"
                                if time_row:
                                    time_values = time_row.get('values', [])
                                    if len(time_values) > col_idx:
                                        time_slot = time_values[col_idx].get('formattedValue', 'Unknown')
                                course_name = selected_course['name']

                            # Store in dictionary (group by day)
                            if sheet_name not in timetable:
                                timetable[sheet_name] = []

                            rank = col_rank.get(col_idx, 999)
                            entry = (
                                rank,
                                parse_time_slot(time_slot),
                                time_slot,
                                room,
                                "Lab" if is_lab else "Class",
                                course_name,  # Use the cleaned course name (either from embedded parsing or selected course)
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

        # Sort sessions by column rank then extracted start time before displaying
        for _, _, time_slot, room, session_type, course, section, batch in sorted(sessions, key=lambda x: (x[0], x[1])):
            # Extract year from batch for compact display
            import re
            m = re.search(r"(20\d{2})", str(batch))
            display_batch = m.group(1) if m else str(batch)
            output.append(f"| {time_slot} | {room} | {session_type} | {course} | {section} | {display_batch} |")
        output.append("\n")

    return "\n".join(output) if output else "⚠️ No classes found for selected courses"

def matches_selected_course(class_entry, selected_course, cell_color, batch_colors):
    """Check if a class entry matches a selected course"""
    # Parse embedded time info if present to get clean course name for matching
    cleaned_entry, _, has_embedded_time = parse_embedded_time_info(class_entry)
    
    # Use cleaned entry for matching if it has embedded time, otherwise use original
    entry_to_match = cleaned_entry if has_embedded_time else class_entry
    
    # Extract base course name for matching (handle group patterns like "(CS, G-1)")
    selected_course_name = selected_course['name']
    
    # Check if this is a group course (contains patterns like "(CS,G-1)" - normalized format)
    import re
    group_pattern = r'\([A-Z]{2,4}(?:-[A-Z])?,\s*G-\d+\)'
    entry_has_group = re.search(group_pattern, entry_to_match)
    selected_has_group = re.search(group_pattern, selected_course_name)
    
    # For group courses, we need special matching logic
    if entry_has_group or selected_has_group:
        # Both should have group patterns for a match
        if entry_has_group and selected_has_group:
            # Extract base course names (everything before the parentheses)
            selected_base = selected_course_name.split('(')[0].strip()
            entry_base = entry_to_match.split('(')[0].strip()
            
            # Check if base course names match
            if selected_base.lower() != entry_base.lower():
                return False
        else:
            # If only one has group pattern, no match
            return False
    else:
        # For non-group courses, check if the course name is in the entry
        if selected_course_name.lower() not in entry_to_match.lower():
            return False
    
    # If the selected course doesn't contain "Lab" but the class entry does, reject it
    # This prevents fetching lab sessions when only the main course is selected
    if 'lab' not in selected_course_name.lower() and 'lab' in entry_to_match.lower():
        return False
    
    # Check if the section matches
    department = selected_course.get('department', '')
    section = selected_course.get('section', '')
    
    # Build section patterns
    section_patterns = [
        f"({department}-{section})" if department else f"({section})",
        f"-{section}",
        f"({section})",
        f" {section} "
    ]
    
    # For group courses, we need precise section matching since the format is standardized
    if entry_has_group or selected_has_group:
        # For group courses, check for the specific format in the original cell entry
        # The actual timetable format is like "Gen AI (CS-A,G-1)"
        if department and section:
            # Extract the group number from the selected course
            group_match = re.search(r'G-(\d+)', selected_course_name)
            if group_match:
                group_number = group_match.group(1)
                group_section_pattern = rf"\({department}-{section},\s*G-{group_number}\)"
                section_match = re.search(group_section_pattern, class_entry) is not None
            else:
                section_match = False
        else:
            section_match = False
    else:
        # Use the original class_entry for section matching since patterns might include time info
        section_match = any(pattern in class_entry for pattern in section_patterns)
    
    if not section_match:
        return False

    # If the class entry explicitly mentions a department token like 'DS-B' or '(DS-B)',
    # extract that department and reject if it doesn't match the selected department.
    dept_in_entry = None
    m_dept = re.search(r"\b([A-Z]{2,4})-[A-Z]\b", class_entry)
    if m_dept:
        dept_in_entry = m_dept.group(1)
    else:
        m_paren = re.search(r"\(\s*([A-Z]{2,4})\s*-\s*[A-Z]\s*\)", class_entry)
        if m_paren:
            dept_in_entry = m_paren.group(1)

    if dept_in_entry and selected_course.get('department'):
        if dept_in_entry != selected_course.get('department'):
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
