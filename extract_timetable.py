def extract_batch_details(sheet):
    batch_details = {}

    for worksheet in sheet.worksheets():
        data = worksheet.get_all_values()  # Get all data as a list of lists
        for row in data[:5]:  # Checking first 5 rows for batch info
            for cell in row:
                if "BS" in cell:  # Example: "BS CS (2023) - A"
                    parts = cell.split(" ")
                    if len(parts) >= 4:
                        batch = parts[2].strip("()")  # Extracts 2023
                        department = parts[1]  # Extracts CS
                        section = parts[3]  # Extracts A

                        if batch not in batch_details:
                            batch_details[batch] = {}
                        if department not in batch_details[batch]:
                            batch_details[batch][department] = set()
                        batch_details[batch][department].add(section)

    return batch_details

def get_timetable(sheet, batch, department, section):
    output = [f"Timetable for {department} ({batch}), Section {section}:"]

    for worksheet in sheet.worksheets():
        data = worksheet.get_all_values()
        day_schedule = [f"\n{worksheet.title}:"]

        for row in data[5:]:  # Start from row 6 (assuming row 1-5 contain headers)
            time_slot = row[0]
            for cell in row:
                if f"({section})" in cell:
                    subject = cell.strip()
                    day_schedule.append(f"{time_slot} | {subject}")

        if len(day_schedule) > 1:
            output.append("\n".join(day_schedule))

    return "\n".join(output)
