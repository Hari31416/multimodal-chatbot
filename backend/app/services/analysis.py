"""Data analysis helpers with a very small safe surface area for MVP."""

import pandas as pd
from typing import Tuple, Any, Dict


def simple_question_answer(
    df: pd.DataFrame, question: str
) -> Tuple[str, Dict[str, Any]]:
    q = question.lower().strip()
    artifacts: Dict[str, Any] = {}

    if any(k in q for k in ["column", "columns", "cols"]):
        answer = ", ".join(list(df.columns)) or "No columns"
    elif "row count" in q or "rows" in q or "count" in q:
        answer = f"Rows: {len(df)}"
    elif any(k in q for k in ["describe", "summary", "stats"]):
        desc = df.describe(include="all", datetime_is_numeric=True).fillna(0)
        artifacts["describe"] = desc.reset_index().values.tolist()
        answer = "Generated summary statistics (see artifacts.describe)."
    elif "head" in q or "preview" in q:
        head = df.head(5)
        artifacts["head"] = head.values.tolist()
        answer = "Returned first 5 rows (see artifacts.head)."
    elif any(k in q for k in ["chart", "plot", "histogram"]):
        numeric = df.select_dtypes("number")
        if numeric.empty:
            answer = "No numeric columns available for chart."
        else:
            if plt is None:
                answer = "Chart library not available."
            else:
                col = numeric.columns[0]
                fig, ax = plt.subplots()
                numeric[col].plot(kind="hist", ax=ax, title=f"Histogram of {col}")
                buf = io.BytesIO()
                fig.tight_layout()
                fig.savefig(buf, format="png")
                plt.close(fig)
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode("utf-8")
                artifacts["chart"] = f"data:image/png;base64,{b64}"
                answer = (
                    f"Generated histogram for column '{col}' (see artifacts.chart)."
                )
    else:
        # Fallback: very naive pattern - attempt mean of numeric columns
        numeric = df.select_dtypes("number")
        if not numeric.empty:
            means = numeric.mean().to_dict()
            artifacts["means"] = means
            answer = "Computed means for numeric columns (see artifacts.means)."
        else:
            answer = "Question not recognized in MVP; try asking for columns, row count, describe, or head."
    return answer, artifacts


import io, base64

try:  # Force headless backend before importing pyplot
    import matplotlib

    matplotlib.use("Agg")  # type: ignore
except Exception:  # pragma: no cover
    pass

try:
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover
    plt = None
