import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import re

# Import core timetable functions
try:
    import extract_timetable
    extract_batch_colors = extract_timetable.extract_batch_colors
    get_timetable = extract_timetable.get_timetable
    
    # Try to get get_custom_timetable function
    if hasattr(extract_timetable, 'get_custom_timetable'):
        get_custom_timetable = extract_timetable.get_custom_timetable
    else:
        # Fallback function if not available
        def get_custom_timetable(spreadsheet, selected_courses):
            return "⚠️ Custom timetable function not available. Please check the implementation."
        st.warning("Custom timetable function not found. Using fallback function.")
        
except ImportError as e:
    st.error(f"Failed to import timetable functions: {e}")
    st.stop()

# Import course extraction functions
try:
    # Use the fuller extractor which reliably extracts departments and batches
    from course_extractor import extract_departments_and_batches, extract_all_courses, search_courses
except ImportError as e:
    st.error(f"Failed to import course extraction functions: {e}")
    st.stop()

# Import user preferences functions
try:
    from user_preferences import (
        initialize_session_state, add_course_to_selection, remove_course_from_selection,
        clear_all_selections, get_selected_courses, update_search_filters, 
        get_search_filters, save_search_results, get_last_search_results,
        is_course_selected, get_selection_summary
    )
except ImportError as e:
    st.error(f"Failed to import user preferences functions: {e}")
    st.stop()

SHEET_URL = "https://docs.google.com/spreadsheets/d/1cmDXt7UTIKBVXBHhtZ0E4qMnJrRoexl2GmDFfTBl0Z4/edit?usp=drivesdk"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_google_sheets_data(sheet_url):
    """Fetch Google Sheets data with formatting using Sheets API v4"""
    credentials_dict = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        credentials_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )

    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = sheet_url.split('/d/')[1].split('/')[0]

    # Get spreadsheet with cell formatting
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        includeGridData=True
    ).execute()

    return spreadsheet


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_batch_colors(sheet_url):
    """Get batch colors with caching to avoid repeated API calls"""
    spreadsheet = get_google_sheets_data(sheet_url)
    return extract_batch_colors(spreadsheet)


@st.cache_data(ttl=300)  # Cache for 5 minutes  
def get_cached_all_courses(sheet_url):
    """Get all courses with caching to avoid repeated extractions"""
    spreadsheet = get_google_sheets_data(sheet_url)
    return extract_all_courses(spreadsheet)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_departments_and_years(sheet_url):
    """Get departments and years lists with caching"""
    all_courses = get_cached_all_courses(sheet_url)
    
    # Extract departments
    department_list = sorted(set(c.get('department', '') for c in all_courses if c.get('department')))
    
    # Extract years from courses
    year_list = []
    for course in all_courses:
        batch = str(course.get('batch', ''))
        m = re.search(r"(20\d{2})", batch)
        if m and m.group(1) not in year_list:
            year_list.append(m.group(1))
    
    return department_list, sorted(year_list)


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


def main():
    st.title("FAST-NUCES FCS Timetable System")
    
    # Add a version indicator to ensure we're running the latest code
    st.caption("")

    # Initialize session state
    initialize_session_state()

    # Fetch cached data - this will only make API calls once every 5 minutes
    st.info("Welcome Everyone!")
    try:
        # Use cached functions to reduce API calls
        batch_colors = get_cached_batch_colors(SHEET_URL)
        all_courses = get_cached_all_courses(SHEET_URL)
        department_list, year_list = get_cached_departments_and_years(SHEET_URL)
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        return

    # Extract batch-color mappings
    if not batch_colors:
        st.error("⚠️ No batches found. Please check the sheet format.")
        return
        st.error("⚠️ No batches found. Please check the sheet format.")
        return

    # Create tabs
    tab1, tab2 = st.tabs(["📚 Batch Timetable", "🔍 Custom Course Selection"])

    # Tab 1: Original Batch Timetable (existing functionality)
    with tab1:
        st.header("📚 Batch Timetable")
        st.write("Select your batch and section to view your timetable.")
        
        # Prepare batch data for dropdown selection
        batch_list = list(batch_colors.values())
        
        # Extract departments from batch names (e.g., "BS CS (2024)" -> "CS")
        dept_pattern = r"BS\s+([A-Z]+)"
        departments_in_batches = set()
        for batch_name in batch_list:
            match = re.search(dept_pattern, str(batch_name))
            if match:
                departments_in_batches.add(match.group(1))
        department_list_tab1 = sorted(departments_in_batches)
        
        # Extract years from batch names
        year_to_batches_tab1 = {}
        year_list_tab1 = []
        for b in batch_list:
            m = re.search(r"(20\d{2})", str(b))
            if m:
                y = m.group(1)
                year_to_batches_tab1.setdefault(y, []).append(b)
                if y not in year_list_tab1:
                    year_list_tab1.append(y)
        year_list_tab1 = sorted(year_list_tab1)

        # Dropdown selection for department and batch (no auto-refresh)
        col1, col2 = st.columns(2)
        
        with col1:
            selected_department_tab1 = st.selectbox("🏢 Department",
                                                   [""] + department_list_tab1,
                                                   key="dept_tab1")
        
        with col2:
            selected_year_tab1 = st.selectbox("👥 Batch",
                                            [""] + year_list_tab1,
                                            key="year_tab1")
        
        # Filter batches based on selections
        filtered_batches = batch_list
        if selected_department_tab1:
            filtered_batches = [b for b in filtered_batches if selected_department_tab1 in str(b)]
        if selected_year_tab1:
            filtered_batches = [b for b in filtered_batches if selected_year_tab1 in str(b)]
        
        # Auto-select batch from filtered list (take first match)
        if filtered_batches:
            batch = filtered_batches[0]  # Auto-select first matching batch
        else:
            batch = ""
            if selected_department_tab1 or selected_year_tab1:
                st.warning("No batches found for the selected filters.")

        # User input for section
        section = st.text_input("🔠 Enter your section (e.g., 'A')").strip().upper()

        # Submit button - only fetch timetable when clicked
        if st.button("Show Timetable", key="batch_timetable_btn"):
            if not batch or not section:
                st.warning("⚠️ Please enter both batch and section.")
            else:
                # Only fetch spreadsheet data when actually needed
                with st.spinner("Generating timetable..."):
                    spreadsheet = get_google_sheets_data(SHEET_URL)
                    schedule = get_timetable(spreadsheet, batch, section)

                    if schedule.startswith("⚠️"):
                        st.error(schedule)
                    else:
                        st.markdown(f"## Timetable for **{batch}, Section {section}**")
                        st.markdown(schedule)

    # Tab 2: Custom Course Selection (new functionality)
    with tab2:
        st.header("🔍 Custom Course Selection")
        st.write("Search and select individual courses to create your custom timetable.")

        # Use cached data instead of recomputing
        unique_batches = sorted(set(batch_colors.values())) if batch_colors else []
        batch_list = unique_batches

        # Filter section - moved above search for better mobile layout
        col1, col2 = st.columns(2)

        with col1:
            # Safely compute the initial index for department selectbox — avoid ValueError if session value not present
            dept_index = 0
            if st.session_state.selected_department:
                try:
                    dept_index = department_list.index(st.session_state.selected_department) + 1
                except ValueError:
                    dept_index = 0

            selected_department = st.selectbox("🏢 Department",
                                             [""] + department_list,
                                             index=dept_index)

        with col2:
            # Decide initial index based on previous selection which might be a full batch or a year
            initial_index = 0
            if st.session_state.selected_batch:
                m_prev = re.search(r"(20\d{2})", str(st.session_state.selected_batch))
                prev_year = m_prev.group(1) if m_prev else str(st.session_state.selected_batch)
                if prev_year in year_list:
                    initial_index = ([""] + year_list).index(prev_year)

            # Show only years in the dropdown; selected_year holds the year string (e.g., '2025')
            selected_year = st.selectbox("👥 Batch", [""] + year_list, index=initial_index)

            # For filtering we'll later map selected_year -> list of batches via year_to_batches
            selected_batch = selected_year or ""

        # Course search section - now appears below filters for better mobile experience
        # Get filtered courses based on current department and batch selections
        # This allows the course dropdown to update dynamically
        current_courses = all_courses  # Use cached data
        
        # Apply department filter if selected
        if selected_department:
            current_courses = [c for c in current_courses if c.get('department') == selected_department]
        
        # Apply batch/year filter if selected
        if selected_year:
            current_courses = [c for c in current_courses if selected_year in str(c.get('batch', ''))]
        
        # Create course options for dropdown with the new format: "course_name department section batch"
        course_options = [""]  # Clear option message
        course_map = {}  # Map display text to course object
        
        for course in current_courses:
            display_text = format_course_display(course)
            course_options.append(display_text)
            course_map[display_text] = course
        
        selected_course_text = st.selectbox("🔍 Search courses",
                                           course_options,
                                           index=0)

        # Update search filters (store selected_year in session state's selected_batch for persistence)
        update_search_filters("", selected_department, selected_batch)

        # Handle course selection from dropdown - automatically add to selection
        # Only auto-add when course is actually selected (not empty) and different from current
        if (selected_course_text and 
            selected_course_text != "" and 
            selected_course_text in course_map and
            selected_course_text != st.session_state.get('last_selected_course', '')):
            
            selected_course = course_map[selected_course_text]
            
            # Check if course is not already selected, then add it automatically
            if not is_course_selected(selected_course):
                add_course_to_selection(selected_course)
                st.session_state.last_selected_course = selected_course_text
                st.rerun()
            else:
                # Show a brief message that it's already selected
                st.info(f"✅ **{format_course_display(selected_course)}** is already in your selection.")
                st.session_state.last_selected_course = selected_course_text
        
        # Selected courses section
        selected_courses = get_selected_courses()
        if selected_courses:
            st.subheader("📝 Selected Courses")
            
            # Show selection summary
            summary = get_selection_summary()
            st.write(f"**Total Courses:** {summary['total_courses']}")
            st.write(f"**Departments:** {', '.join(summary['departments']) if summary['departments'] else 'None'}")
            st.write(f"**Batches:** {', '.join(summary['batches']) if summary['batches'] else 'None'}")
            
            # Display selected courses with remove buttons
            for i, course in enumerate(selected_courses):
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Use compact format for selected courses list
                    st.write(f"**{format_course_display(course)}**")
                with col2:
                    if st.button("❌ Remove", key=f"selected_remove_{i}"):
                        remove_course_from_selection(course)
                        st.rerun()
            
            # Small Clear All button on the left and a centered Show Custom Timetable button below it
            c1, c2 = st.columns([1, 3])
            with c1:
                # use a smaller button by adding a compact label and container
                if st.button("🗑️ Clear", key="clear_small"):
                    clear_all_selections()
                    st.rerun()

            # Centered Show Timetable button on its own row
            st.write("")
            center_col1, center_col2, center_col3 = st.columns([1, 2, 1])
            with center_col2:
                if st.button("📅 Show Custom Timetable", key="custom_timetable_btn"):
                    # Only fetch fresh spreadsheet data when generating custom timetable
                    with st.spinner("Generating custom timetable..."):
                        spreadsheet = get_google_sheets_data(SHEET_URL)
                        schedule = get_custom_timetable(spreadsheet, selected_courses)
                        
                        if schedule.startswith("⚠️"):
                            st.error(schedule)
                        else:
                            st.markdown("## Custom Timetable")
                            st.markdown(schedule)
        else:
            st.info("No courses selected. Search and add courses to create your custom timetable.")


if __name__ == "__main__":
    main()

    # Footer with support contact and LinkedIn profile
    st.markdown("---")
    st.markdown("📧 **For any issues or support, please contact:** [i230553@isb.nu.edu.pk](mailto:i230553@isb.nu.edu.pk)")

    st.markdown("🔗 **Connect with me on LinkedIn:** [Muhammad Ahsan](https://www.linkedin.com/in/muhammad-ahsan-7612701a7)")

