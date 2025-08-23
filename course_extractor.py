from typing import List, Dict, Set, Tuple
import re


def extract_departments_and_batches(spreadsheet) -> Tuple[Set[str], Set[str]]:
    """Extract unique departments and batches from the first 4 rows of all sheets"""
    departments = set()
    batches = set()
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
                if 'formattedValue' in cell:
                    value = cell['formattedValue'].strip()
                    
                    # Extract departments (look for patterns like "CS", "EE", etc.)
                    if re.match(r'^[A-Z]{2,4}$', value) and len(value) <= 4:
                        departments.add(value)
                    
                    # Extract batches (look for patterns like "BS-CS-1", "BS-EE-2", etc.)
                    if 'BS-' in value and '-' in value:
                        batches.add(value)
    
    return departments, batches

def extract_all_courses(spreadsheet) -> List[Dict]:
    """Extract all courses from the spreadsheet with their metadata"""
    courses = []
    timetable_sheets = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # First, get batch colors mapping
    batch_colors = {}
    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue
            
        grid_data = sheet.get('data', [{}])[0].get('rowData', [])
        
        # Extract batch colors from first 4 rows
        for row_idx in range(4):
            if row_idx >= len(grid_data):
                continue
                
            row_data = grid_data[row_idx].get('values', [])
            for cell in row_data:
                if 'formattedValue' in cell and 'BS' in cell['formattedValue']:
                    color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                    color_hex = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"
                    batch_colors[color_hex] = cell['formattedValue'].strip()
    
    # Now extract courses from all sheets
    for sheet in spreadsheet.get('sheets', []):
        sheet_name = sheet['properties']['title']
        if sheet_name not in timetable_sheets:
            continue
            
        grid_data = sheet.get('data', [{}])[0].get('rowData', [])
        
        # Process timetable rows (skip header rows). Start from row index 5 (0-indexed)
        for row_idx, row in enumerate(grid_data[5:], start=6):
            row_values = row.get('values', []) if isinstance(row, dict) else []
            
            for col_idx, cell in enumerate(row_values):
                if not isinstance(cell, dict) or 'effectiveFormat' not in cell:
                    continue
                
                # Get cell color
                color = cell.get('effectiveFormat', {}).get('backgroundColor', {})
                cell_color = f"{color.get('red', 0):.2f}{color.get('green', 0):.2f}{color.get('blue', 0):.2f}"
                
                # Check if this cell has a course (has color and formatted value)
                if cell_color in batch_colors and 'formattedValue' in cell:
                    course_entry = cell.get('formattedValue', '').strip()
                    
                    if course_entry:
                        # Extract course information
                        course_info = parse_course_entry(course_entry, batch_colors[cell_color])
                        
                        if course_info:
                            # Add day information
                            course_info['day'] = sheet_name
                            course_info['color_code'] = cell_color
                            
                            # Check if this course is already in our list
                            existing_course = find_existing_course(courses, course_info)
                            if not existing_course:
                                courses.append(course_info)
    
    return courses

def parse_course_entry(course_entry: str, batch: str) -> Dict:
    """Parse a course entry to extract course name, department, and section"""
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
    
    # Extract section from course entry
    section = ""
    course_name = course_entry
    
    # Look for section patterns like "(CS-E)", "-E", "(E)", etc.
    section_patterns = [
        r'\(CS-([A-Z])\)',  # Pattern like "(CS-E)"
        r'-([A-Z])\b',      # Pattern like "-E"
        r'\(([A-Z])\)',     # Pattern like "(E)"
        r'\s([A-Z])\s'      # Pattern like " E " (with spaces)
    ]
    
    for pattern in section_patterns:
        match = re.search(pattern, course_entry)
        if match:
            section = match.group(1)
            # Remove section info from course name
            course_name = re.sub(pattern, '', course_name).strip()
            break
    
    # Clean up course name
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

def find_existing_course(courses: List[Dict], new_course: Dict) -> Dict:
    """Check if a course already exists in the list"""
    for course in courses:
        if (course['name'] == new_course['name'] and 
            course['department'] == new_course['department'] and
            course['section'] == new_course['section'] and
            course['batch'] == new_course['batch']):
            return course
    return None

def search_courses(courses: List[Dict], query: str = "", department: str = "", batch: str = "") -> List[Dict]:
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

    # Sort alphabetically by course name, then department, then section
    filtered_courses.sort(key=lambda c: (c.get('name', '').lower(), c.get('department', ''), c.get('section', '')))

    return filtered_courses
