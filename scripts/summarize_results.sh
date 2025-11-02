#!/usr/bin/env bash
# Usage: ./summarize_code_smells.sh /path/to/folder_with_csvs_results_files

folder="$1"

if [ -z "$folder" ]; then
  echo "Usage: $0 <folder_with_csvs_results_files>"
  exit 1
fi

combined="combined_code_smells.csv"
head -n 1 "$(ls "$folder"/*.csv | head -n 1)" > "$combined"
tail -q -n +2 "$folder"/*.csv >> "$combined"

# Run Python for summarization
python3 <<'EOF'
import pandas as pd
from pathlib import Path

# Read combined CSV
df = pd.read_csv("combined_code_smells.csv")

# Clean up the "Repository" column (remove "https://github.com/")
df['Repository'] = df['Repository'].str.replace(r'https://github\.com/', '', regex=True)

# Remove duplicates if any
df = df.drop_duplicates()

# Convert Age to numeric, forcing non-numeric (e.g. 'N/A') to NaN
df['Repository Age (days)'] = pd.to_numeric(df['Repository Age (days)'], errors='coerce')

# Group by repository and sum counts
summary = df.groupby(['Repository', 'Repository Age (days)'], dropna=False)['Count'].sum().reset_index()

# Rename column
summary = summary.rename(columns={'Count': 'Total Code Smells'})

# Sort by total smells (descending)
summary = summary.sort_values('Total Code Smells', ascending=False)

# Save summary CSV
summary.to_csv("repo_smell_summary.csv", index=False)

print("\n Summary written to repo_smell_summary.csv\n")
print(summary.to_string(index=False))
EOF
