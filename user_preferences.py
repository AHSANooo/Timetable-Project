import streamlit as st
from typing import List, Dict, Optional
import re

def format_course_display(course: dict) -> str:
    """Return a compact display string for a course: 'name dept section year-or-batch'
    Example: 'Data St CS A 2024' (falls back to full batch string if year not found)
    """
    name = course.get('name', '').strip()
    dept = course.get('department', '').strip()
    section = course.get('section', '').strip()
    batch = str(course.get('batch', '')).strip()
    # Prefer year (e.g., 2024) when available inside the batch string
    m = re.search(r"(20\d{2})", batch)
    year = m.group(1) if m else batch
    parts = [p for p in [name, dept, section, year] if p]
    return " ".join(parts)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'selected_courses' not in st.session_state:
        st.session_state.selected_courses = []
    
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    if 'selected_department' not in st.session_state:
        st.session_state.selected_department = ""
    
    if 'selected_batch' not in st.session_state:
        st.session_state.selected_batch = ""
    
    # Clear old search results to avoid display issues with old format
    st.session_state.last_search_results = []

def add_course_to_selection(course: Dict):
    """Add a course to the user's selection"""
    # Check if course is already selected
    course_key = f"{course['name']}_{course['department']}_{course['section']}_{course['batch']}"
    
    for selected_course in st.session_state.selected_courses:
        selected_key = f"{selected_course['name']}_{selected_course['department']}_{selected_course['section']}_{selected_course['batch']}"
        if selected_key == course_key:
            st.warning(f"Course '{format_course_display(course)}' is already selected!")
            return False
    
    # Add course to selection
    st.session_state.selected_courses.append(course)
    return True

def remove_course_from_selection(course: Dict):
    """Remove a course from the user's selection"""
    course_key = f"{course['name']}_{course['department']}_{course['section']}_{course['batch']}"
    
    for i, selected_course in enumerate(st.session_state.selected_courses):
        selected_key = f"{selected_course['name']}_{selected_course['department']}_{selected_course['section']}_{selected_course['batch']}"
        if selected_key == course_key:
            removed_course = st.session_state.selected_courses.pop(i)
            st.success(f"Removed '{format_course_display(removed_course)}' from selection")
            return True
    
    return False

def clear_all_selections():
    """Clear all selected courses"""
    st.session_state.selected_courses = []
    st.success("All course selections cleared!")

def get_selected_courses() -> List[Dict]:
    """Get list of currently selected courses"""
    return st.session_state.selected_courses

def update_search_filters(query: str = "", department: str = "", batch: str = ""):
    """Update search filters in session state"""
    st.session_state.search_query = query
    st.session_state.selected_department = department
    st.session_state.selected_batch = batch

def get_search_filters() -> Dict:
    """Get current search filters"""
    return {
        'query': st.session_state.search_query,
        'department': st.session_state.selected_department,
        'batch': st.session_state.selected_batch
    }

def save_search_results(results: List[Dict]):
    """Save search results to session state"""
    st.session_state.last_search_results = results

def get_last_search_results() -> List[Dict]:
    """Get last search results"""
    return st.session_state.last_search_results

def is_course_selected(course: Dict) -> bool:
    """Check if a course is already selected"""
    course_key = f"{course['name']}_{course['department']}_{course['section']}_{course['batch']}"
    
    for selected_course in st.session_state.selected_courses:
        selected_key = f"{selected_course['name']}_{selected_course['department']}_{selected_course['section']}_{selected_course['batch']}"
        if selected_key == course_key:
            return True
    
    return False

def get_selection_summary() -> Dict:
    """Get a summary of current selections"""
    if not st.session_state.selected_courses:
        return {
            'total_courses': 0,
            'departments': set(),
            'batches': set(),
            'sections': set()
        }
    
    departments = set(course['department'] for course in st.session_state.selected_courses)
    batches = set(course['batch'] for course in st.session_state.selected_courses)
    sections = set(course['section'] for course in st.session_state.selected_courses)
    
    return {
        'total_courses': len(st.session_state.selected_courses),
        'departments': departments,
        'batches': batches,
        'sections': sections
    }
