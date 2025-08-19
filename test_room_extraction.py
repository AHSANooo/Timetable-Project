#!/usr/bin/env python3
"""
Test script for room extraction functionality
This script helps debug and verify that rooms are being extracted correctly from the timetable sheets.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extract_timetable import find_room_column, clean_room_data, analyze_sheet_structure

def test_room_cleaning():
    """Test the room data cleaning function"""
    print("Testing room data cleaning...")
    
    test_cases = [
        ("Room 101", "101"),
        ("room no 202", "202"),
        ("Lab 1", "Lab 1"),
        ("Class 301", "Class 301"),
        ("Unknown", "Unknown"),
        ("", "Unknown"),
        ("   ", "Unknown"),
        ("Room No. 405", "405"),
        ("CS-101", "CS-101"),  # Should not be cleaned as it's a course code
    ]
    
    for input_room, expected in test_cases:
        result = clean_room_data(input_room)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: '{input_room}' -> Output: '{result}' (Expected: '{expected}')")

def test_room_column_detection():
    """Test room column detection with sample data"""
    print("\nTesting room column detection...")
    
    # Sample grid data structure
    sample_grid_data = [
        {
            'values': [
                {'formattedValue': 'Time'},
                {'formattedValue': 'Room'},
                {'formattedValue': 'Course'},
                {'formattedValue': 'Instructor'}
            ]
        },
        {
            'values': [
                {'formattedValue': '08:30 AM'},
                {'formattedValue': '101'},
                {'formattedValue': 'CS-101'},
                {'formattedValue': 'Dr. Smith'}
            ]
        }
    ]
    
    room_column = find_room_column(sample_grid_data)
    print(f"Detected room column: {room_column}")
    
    # Test with different header patterns
    test_headers = [
        [{'formattedValue': 'Location'}],
        [{'formattedValue': 'Venue'}],
        [{'formattedValue': 'Room No'}],
        [{'formattedValue': 'Class'}],
        [{'formattedValue': '101'}],  # Direct room number
    ]
    
    for i, header in enumerate(test_headers):
        test_data = [{'values': header}]
        column = find_room_column(test_data)
        print(f"Header '{header[0]['formattedValue']}' -> Column {column}")

if __name__ == "__main__":
    print("🧪 Room Extraction Test Suite")
    print("=" * 40)
    
    test_room_cleaning()
    test_room_column_detection()
    
    print("\n✅ All tests completed!")
    print("\nTo test with actual Google Sheets data, run the main app and check the console output for debugging information.")
