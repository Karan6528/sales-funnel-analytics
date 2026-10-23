"""
Run the whole project end to end:

    1. generate the raw CRM export          (src/generate_data.py)
    2. clean it                              (src/clean_data.py)
    3. load it into SQLite                   (src/load_to_sqlite.py)
       + load the REAL Olist Kaggle data       (src/load_olist.py)
    4. run the SQL analysis                  (src/run_analysis.py)
    5. draw the report charts                (src/make_figures.py)
    6. build the Excel reports               (src/build_excel_report.py,
                                              src/build_olist_excel.py)

Usage:  python run_all.py            (all steps)
        python run_all.py --skip-data (reuse the existing raw data)
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "src/generate_data.py",
    "src/clean_data.py",
    "src/load_to_sqlite.py",
    "src/load_olist.py",
    "src/run_analysis.py",
    "src/make_figures.py",
    "src/build_excel_report.py",
    "src/build_olist_excel.py",
]


def main() -> None:
    steps = STEPS[1:] if "--skip-data" in sys.argv else STEPS
    t0 = time.time()
    for step in steps:
        print(f"\n▶ {step}")
        result = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT,
                                stdout=None if step != "src/run_analysis.py" else subprocess.DEVNULL)
        if result.returncode != 0:
            sys.exit(f"✖ {step} failed")
    print(f"\n✔ Done in {time.time() - t0:.0f}s")
    print("  Excel reports: excel/Olist_Real_Funnel_Report.xlsx, excel/Solar_Funnel_KPI_Report.xlsx")
    print("  SQL results  : outputs/*.csv")
    print("  Dashboard    : streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
