import ast
import os
import subprocess
import tempfile
from typing import List

import pandas as pd
import streamlit as st
import plotly.express as px

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
                # Display just the enum name
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
                    df = reports_to_dataframe(reports)
                    st.subheader("Analysis Results")
                    st.dataframe(df, width="stretch")

                    # CSV download
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Full Report as CSV",
                        data=csv,
                        file_name="rl_code_smell_report.csv",
                        mime="text/csv",
                    )

                    st.subheader("Distribution of Code Smells by Category")
                    category_counts = (
                        df[df["Is Code Smell"] == True]["Category"]
                        .value_counts()
                        .reset_index()
                    )
                    category_counts.columns = ["Category", "Count"]

                    fig = px.pie(
                        category_counts,
                        names="Category",
                        values="Count",
                        title="Distribution of RL Code Smells by Category",
                        color="Category"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.success("✅ No RL-specific code smells detected!")

            except subprocess.CalledProcessError as e:
                st.error(f"Failed to clone repository: {e}")
