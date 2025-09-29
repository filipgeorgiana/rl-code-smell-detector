import ast
import os
import subprocess
import tempfile
from typing import List

import pandas as pd
import streamlit as st
import plotly.express as px
from pandas import DataFrame

from analyzer import Analyzer
from model.report import Report
from model.heuristic import Heuristic
from pre_processing import RLScriptDetector
from project_reader import ProjectReader, read_file

st.set_page_config(page_title="RL Code Smell Detector", layout="wide")
st.title("RL Code Smell Detector")
st.write("Analyze a GitHub repository for RL-specific code smells.")

def reports_to_dataframe(reports: List[Report]) -> pd.DataFrame:
    rows = []
    for report in reports:
        for h in report.heuristics:
            rows.append({
                "File": report.filename,
                "Smell": h.name,
                "Details": h.details,
                "Line": h.line_nr,
                "Category": h.category.name if h.category is not None else "",
                "Is Code Smell": h.is_code_smell,
            })
    return pd.DataFrame(rows)


# ------------------------
# GitHub Repo Input
# ------------------------
repo_url = st.text_input(
    "Enter GitHub repository URL (HTTPS)",
    placeholder="https://github.com/username/repo"
)

df = DataFrame

def display_results_dataframe():
    global df
    df = reports_to_dataframe(reports)
    st.subheader("Analysis Results")
    st.dataframe(df, width="stretch")


def display_csv_download_button():
    # CSV download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Full Report as CSV",
        data=csv,
        file_name="rl_code_smell_report.csv",
        mime="text/csv",
    )


if st.button("Analyze Repository"):
    if not repo_url.strip():
        st.error("Please enter a GitHub repository URL")
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                st.info("Cloning repository... this may take a moment ⏳")
                subprocess.run(["git", "clone", repo_url, tmpdir], check=True)

                reader = ProjectReader(tmpdir)
                files = reader.list_files()

                st.info("Running static analysis... 🔍")
                reports: List[Report] = []

                for fpath in files:
                    try:
                        filename = os.path.basename(fpath)
                        rl_detector = RLScriptDetector()
                        if rl_detector.analyze(fpath):
                            tree = ast.parse(read_file(fpath))
                            analyzer = Analyzer()
                            analyzer.visit(tree)

                            detected_heuristics: List[Heuristic] = [
                                item for sublist in analyzer.get_report() for item in sublist
                            ]

                            if detected_heuristics:
                                reports.append(Report(filename, detected_heuristics))
                    except Exception as e:
                        st.error(f"Error analyzing {fpath}: {e}")


                if reports:
                    display_results_dataframe()

                    display_csv_download_button()

                    st.subheader("Distribution of Code Smells by Category")
                    category_counts = (
                        df[df["Is Code Smell"] == True]["Category"]
                        .value_counts()
                        .reset_index()
                    )
                    category_counts.columns = ["Category", "Count"]

                    fig = px.bar(
                        category_counts,
                        x="Category",
                        y="Count",
                        title="Distribution of RL Code Smells by Category",
                        color="Category"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    total_smells = category_counts["Count"].sum()
                    category_counts["Percentage"] = (category_counts["Count"] / total_smells * 100).round(2)

                    # Display table with categories and percentages
                    st.subheader("Code Smell Category Breakdown")
                    category_table = category_counts[["Category", "Count", "Percentage"]].copy()
                    category_table.columns = ["Code Smell Category", "Nr of Occurrences", "Percentage"]
                    category_table["Percentage"] = category_table["Percentage"].astype(str) + " %"
                    category_table["Nr of Occurrences"] = category_table["Nr of Occurrences"].astype(str)

                    st.table(category_table)
                else:
                    st.success("✅ No RL-specific code smells detected!")

            except subprocess.CalledProcessError as e:
                st.error(f"Failed to clone repository: {e}")
