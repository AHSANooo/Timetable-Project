#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from extract_timetable import parse_embedded_time_info

def test_embedded_time_parsing():
    test_cases = [
        "Func Eng (SE) 09:00-10:45",
        "Islamic (SE) 11:00-12:45", 
        "Data Structures (CS-A)",
        "Math Lab (EE) 14:30-16:15",
        "Operating Systems",
        "Database (CS-B) 08:00-09:30"
    ]
    
    print("Testing embedded time parsing:")
    print("=" * 50)
    
    for test_case in test_cases:
        cleaned, time_slot, has_time = parse_embedded_time_info(test_case)
        print(f"Input: '{test_case}'")
        print(f"  Cleaned: '{cleaned}'")
        print(f"  Time: '{time_slot}'")
        print(f"  Has embedded time: {has_time}")
        print()

if __name__ == "__main__":
    test_embedded_time_parsing()
