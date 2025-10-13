from typing import List

import pandas as pd
from model.report import Report


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

