import ast
import os
import subprocess
import tempfile
import streamlit as st
import plotly.express as px

from typing import List
from analyzer import Analyzer
from model.report import Report
from model.heuristic import Heuristic
from pre_processing import RLScriptDetector
from project_reader import ProjectReader, read_file
from github_utils import get_repo_last_update
from ui_utils import reports_to_dataframe

st.set_page_config(page_title="RL Code Smell Detector", layout="wide")
st.title("RL Code Smell Detector")
st.write("Analyze a GitHub repository for RL-specific code smells.")

if "df" not in st.session_state:
    st.session_state.df = None
if "repo_age_days" not in st.session_state:
    st.session_state.repo_age_days = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "repo_url" not in st.session_state:
    st.session_state.repo_url = ""

repo_url = st.text_input(
    "Enter GitHub repository URL (HTTPS)",
    placeholder="https://github.com/username/repo"
)

analyze_button, clear_button = st.columns([.15, 1])

with analyze_button:
    analyze_clicked = st.button("Analyze Repository", type="secondary", use_container_width=False)
with clear_button:
    clear_clicked = st.button("🔄 Clear Results", type="primary", use_container_width=False)

if clear_clicked:
    st.session_state.df = None
    st.session_state.repo_age_days = None
    st.session_state.selected_category = None
    st.rerun()


def clone_repo():
    st.info("⏳ Cloning repository... this may take a moment ⏳")
    subprocess.run(["git", "clone", repo_url, tmpdir], check=True)


def run_static_analysis():
    global filename, analyzer, e
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


if analyze_clicked:
    if not repo_url.strip():
        st.error("Please enter a GitHub repository URL")
    else:
        st.session_state.df = None
        st.session_state.repo_age_days = None

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                clone_repo()

                st.info("📊 Fetching repository metadata... 📊")
                repo_age = get_repo_last_update(repo_url)
                if repo_age is not None:
                    st.session_state.repo_age_days = repo_age

                reader = ProjectReader(tmpdir)
                files = reader.list_files()

                st.info("🔍 Running static analysis... 🔍")
                reports: List[Report] = []

                for fpath in files:
                    run_static_analysis()


                if reports:
                    st.session_state.df = reports_to_dataframe(reports)
                else:
                    st.success("✅ No RL-specific code smells detected!")

            except subprocess.CalledProcessError as e:
                st.error(f"Failed to clone repository: {e}")

if st.session_state.df is not None:
    if st.session_state.repo_age_days is not None:
        st.info(f"📅 The repository has not been updated for: {st.session_state.repo_age_days} days 📅")

    st.subheader("Analysis Results")
    st.dataframe(st.session_state.df, width="stretch")

    csv = st.session_state.df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Full Report as CSV",
        data=csv,
        file_name="rl_code_smell_report.csv",
        mime="text/csv",
    )

    st.subheader("Distribution of Code Smells by Category")
    category_counts = (
        st.session_state.df[st.session_state.df["Is Code Smell"] == True]["Category"]
        .value_counts()
        .reset_index()
    )
    category_counts.columns = ["Category", "Count"]

    fig = px.bar(
        category_counts,
        x="Category",
        y="Count",
        title="Distribution of RL Code Smells by Category (Click on a bar to see details)",
        color="Category",
        custom_data=["Category"]
    )

    # Handle click events on the chart
    category_barchart = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points", key="category_chart")

    # Update selected category based on click
    if category_barchart and category_barchart.selection and category_barchart.selection.points:
        points = category_barchart.selection.points
        if points:
            # Get the category from the x-axis value of the clicked point
            clicked_category = points[0]["x"]
            st.session_state.selected_category = clicked_category

    if st.session_state.selected_category is not None:
        st.subheader(f"Code Smells in Category: {st.session_state.selected_category}")
        filtered_df = st.session_state.df[
            (st.session_state.df["Is Code Smell"] == True) &
            (st.session_state.df["Category"] == st.session_state.selected_category)
        ]

        if not filtered_df.empty:
                display_columns = ["File", "Smell", "Details", "Line"]
                st.dataframe(filtered_df[display_columns], width="stretch")

    total_smells = category_counts["Count"].sum()
    category_counts["Percentage"] = (category_counts["Count"] / total_smells * 100).round(2)

    # Display table with categories and percentages
    st.subheader("Code Smell Category Breakdown")
    category_table = category_counts[["Category", "Count", "Percentage"]].copy()
    category_table.columns = ["Code Smell Category", "Nr of Occurrences", "Percentage"]
    category_table["Percentage"] = category_table["Percentage"].astype(str) + " %"
    category_table["Nr of Occurrences"] = category_table["Nr of Occurrences"].astype(str)

    st.table(category_table)

    # Prepare CSV data with repository info
    category_csv_data = category_counts.copy()
    category_csv_data["Repository"] = repo_url
    category_csv_data["Repository Age (days)"] = st.session_state.repo_age_days if st.session_state.repo_age_days is not None else "N/A"
    # Reorder columns to put repo info first
    category_csv_data = category_csv_data[["Repository", "Repository Age (days)", "Category", "Count", "Percentage"]]

    category_csv = category_csv_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Category Breakdown as CSV",
        data=category_csv,
        file_name="rl_code_smell_category_breakdown.csv",
        mime="text/csv",
    )
