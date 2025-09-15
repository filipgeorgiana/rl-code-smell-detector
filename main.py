import ast
import os
import sys
from typing import List

from cli_utils import display_banner, save_report_csv, get_file_report
from model.heuristic import Heuristic
from model.report import Report
from pre_processing import RLScriptDetector
from project_reader import ProjectReader, read_file
from analyzer import Analyzer
import openai
#
# def analyze_with_llm(code: str) -> str:
#     prompt = f"""
#     Analyze this RL-related code for any code smells and suggest improvements.
#
#     {code}
#     """
#     print(prompt)
#
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant for detecting RL-specific code smells."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.2,
#         max_tokens=800
#     )
#     return response['choices'][0]['message']['content']

if __name__ == "__main__":
    display_banner()
    while True:
        welcome_prompt = input("Do you want to analyze a new project? (y/n) ")
        if welcome_prompt == "y":
            folder_path = input("Enter the path to the project folder: ")
            try:
                reader = ProjectReader(folder_path)
                folder_name = os.path.basename(folder_path)
                file_paths = reader.list_files()
                report = []
                rows = []
                detected_heuristics:List[Heuristic] = []
                for file_path in file_paths:
                    filename = os.path.basename(file_path)
                    rl_detector = RLScriptDetector()
                    if rl_detector.analyze(file_path):
                        tree = ast.parse(read_file(file_path))
                        analyzer = Analyzer()
                        analyzer.visit(tree)
                        print("------ Analyzing file ------ {}".format(file_path))

                        detected_heuristics = [item for sublist in analyzer.get_report() for item in sublist]
                        report.append(Report(filename, detected_heuristics))

                        # if len(detected_heuristics) != 0:
                        # if filename == "atari.py":
                        #     code = read_file(file_path)
                        #     llm_feedback = analyze_with_llm(code)
                        #     print("LLM Feedback:\n", llm_feedback)

                        for i in detected_heuristics:
                            rows.append((file_path, i.name, i.details, i.line_nr, i.is_code_smell, i.category))

                print(f"Analysis finished. The full report can be found in ./results/{folder_name}")

                save_report_csv(folder_name, rows)

                get_file_report(report)
            except ValueError as e:
                print(e)
        elif welcome_prompt == "n":
            sys.exit(0)
