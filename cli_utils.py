import json
import os
import csv
from model.heuristic import Heuristic


def display_banner():
    print("""========================================================================================\nReinforcement Learning Code Analysis Tool\n========================================================================================\n""")

def serialize_heuristics(obj):
    if isinstance(obj, Heuristic):
        return {"name": obj.name, "details": obj.details, "line_nr": obj.line_nr, "is_code_smell": obj.is_code_smell}
    raise TypeError("Type not serializable")


def get_file_report(report):
    while True:
        if input("Do you want more details on a specific file? (y/n): ").strip().lower() != "y":
            break
        while True:
            filename = input("Enter the name of the file (or type 'exit' to quit): ").strip()

            if filename.lower() == "exit":
                return

            file_report = next((r for r in report if r.filename == filename), None)

            if file_report:
                print(json.dumps(file_report.heuristics, default=serialize_heuristics, indent=1))
                break
            else:
                retry = input(f"No report found for '{filename}'. Do you want to try another file? (y/n): ").strip().lower()
                if retry != "y":
                    return



def save_report_csv(project_folder_output, rows):
    subdirectory = os.path.join("./results", project_folder_output)
    os.makedirs(subdirectory, exist_ok=True)

    with open(f"./results/{project_folder_output}/report.csv", mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["File ", "Heuristic detected", "Details", "Line", "Is code smell?", "Category"])
        writer.writerows(rows)

