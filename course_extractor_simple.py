from typing import List, Dict, Set, Tuple
import re

def extract_departments_and_batches_simple(spreadsheet) -> Tuple[Set[str], Set[str]]:
    """Extract departments and batches using the same logic as the working original code"""
    departments = set()
    batches = set()
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Use the same logic as extract_batch_colors from the original working code
    batch_colors = {}
    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        grid_data = sheet.get('data', [{}])[0].get('rowData', [])

        # Check first 4 rows (0-indexed) - same as original
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
                    batch_value = cell['formattedValue'].strip()
                    batch_colors[color_hex] = batch_value
                    
                    # Extract batch and department from the batch value
                    if 'BS-' in batch_value:
                        batches.add(batch_value)
                        # Extract department (e.g., "BS-CS-1" -> "CS")
                        parts = batch_value.split('-')
                        if len(parts) >= 2:
                            departments.add(parts[1])
    
    return departments, batches

def extract_all_courses_simple(spreadsheet) -> List[Dict]:
    """Extract all courses using the same logic as the working original code"""
    courses = []
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # First, get batch colors mapping using the same logic as original
    batch_colors = {}
    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        grid_data = sheet.get('data', [{}])[0].get('rowData', [])

        # Check first 4 rows (0-indexed) - same as original
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
    
    # Now extract courses using the same logic as the original get_timetable function
    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue

        grid_data = sheet.get('data', [{}])[0].get('rowData', [])
        if len(grid_data) < 6:
            continue

    # Process timetable rows (skip header rows)
    for row_idx, row in enumerate(grid_data[5:], start=6):
            row_values = row.get('values', []) if isinstance(row, dict) else []

            # Check all cells in row - same as original
            for col_idx, cell in enumerate(row_values):
                if not isinstance(cell, dict) or 'effectiveFormat' not in cell:
                    continue

                # Get cell color - same as original
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                cell_color = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"

                # Check if this cell has a course (has color and formatted value) - same as original
                if cell_color in batch_colors and 'formattedValue' in cell:
                    class_entry = cell.get('formattedValue', '').strip()
                    
                    if class_entry:
                        # Extract course information using the same logic as original
                        course_info = parse_course_entry_simple(class_entry, batch_colors[cell_color])
                        
                        if course_info:
                            # Add day information
                            course_info['day'] = sheet_name
                            course_info['color_code'] = cell_color
                            
                            # Check if this course is already in our list
                            existing_course = find_existing_course_simple(courses, course_info)
                            if not existing_course:
                                courses.append(course_info)
    
    return courses

def parse_course_entry_simple(course_entry: str, batch: str) -> Dict:
    """Parse a course entry using the same logic as the original working code"""
    if not course_entry:
        return None
    
    # Extract department from batch (e.g., "BS-CS-1" -> "CS")
    department = ""
    if '-' in batch:
        parts = batch.split('-')
        if len(parts) >= 2:
            department = parts[1]
    else:
        # Handle space-separated formats like 'BS CS (2025)'
        tokens = re.findall(r"\b[A-Z]{2,4}\b", batch)
        for t in tokens:
            if t != 'BS':
                department = t
                break
    
    # Extract section from course entry using the same patterns as original
    section = ""
    course_name = course_entry
    
    # Look for section patterns like "(CS-E)", "-E", "(E)", etc. - same as original
    
    # Check for all possible sections (A-Z)
    for i in range(26):
        section_letter = chr(65 + i)  # A, B, C, ..., Z
        patterns = [
            f"(CS-{section_letter})",
            f"-{section_letter}",
            f"({section_letter})",
            f" {section_letter} "
        ]
        
        for pattern in patterns:
            if pattern in course_entry:
                section = section_letter
                # Remove section info from course name
                course_name = course_entry.replace(pattern, '').strip()
                break
        if section:
            break
    
    # Clean up course name - same as original
    course_name = course_name.replace('()', '').strip()
    if course_name.endswith('-'):
        course_name = course_name[:-1].strip()
    
    return {
        'name': course_name,
        'department': department,
        'section': section,
        'batch': batch,
        'full_entry': course_entry
    }

def find_existing_course_simple(courses: List[Dict], new_course: Dict) -> Dict:
    """Check if a course already exists in the list"""
    for course in courses:
        if (course['name'] == new_course['name'] and 
            course['department'] == new_course['department'] and
            course['section'] == new_course['section'] and
            course['batch'] == new_course['batch']):
            return course
    return None

def search_courses_simple(courses: List[Dict], query: str = "", department: str = "", batch: str = "") -> List[Dict]:
    """Search courses based on query, department, and batch filters"""
    filtered_courses = courses.copy()
    
    # Filter by department
    if department:
        filtered_courses = [c for c in filtered_courses if c['department'] == department]
    
    # Filter by batch
    if batch:
        filtered_courses = [c for c in filtered_courses if c['batch'] == batch]
    
    # Filter by search query
    if query:
        query_lower = query.lower()
        filtered_courses = [c for c in filtered_courses if 
                          query_lower in c['name'].lower() or
                          query_lower in c['department'].lower() or
                          query_lower in c['section'].lower()]
    
    return filtered_courses
