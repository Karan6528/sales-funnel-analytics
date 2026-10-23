"""
Load the cleaned CSVs into a local SQLite database (data/funnel.db) and create
the analysis views from sql/00_views.sql.

SQLite needs no server, so the project runs anywhere. The SQL itself is
standard and ports to PostgreSQL / BigQuery / Snowflake with minor changes.

Usage:  python src/load_to_sqlite.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "funnel.db"
VIEWS_SQL = ROOT / "sql" / "00_views.sql"

DATE_COLS = ["created_at", "first_contact_at", "appointment_at", "offer_sent_at",
             "contract_signed_at", "installed_at", "cancelled_at"]


def main() -> None:
    leads = pd.read_csv(PROCESSED / "leads_clean.csv", parse_dates=DATE_COLS)
    reps = pd.read_csv(PROCESSED / "sales_reps.csv")
    spend = pd.read_csv(PROCESSED / "marketing_spend.csv")

    # Store timestamps as ISO text ("YYYY-MM-DD HH:MM:SS"), which SQLite date
    # functions understand and which sorts correctly.
    for col in DATE_COLS:
        leads[col] = leads[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    for col in ["lead_week", "signed_week"]:
        leads[col] = pd.to_datetime(leads[col]).dt.strftime("%Y-%m-%d")
    spend["week_start"] = pd.to_datetime(spend["week_start"]).dt.strftime("%Y-%m-%d")

    DB_PATH.unlink(missing_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        leads.to_sql("leads", con, index=False)
        reps.to_sql("sales_reps", con, index=False)
        spend.to_sql("marketing_spend", con, index=False)
        con.execute("CREATE INDEX idx_leads_channel ON leads(channel)")
        con.execute("CREATE INDEX idx_leads_created ON leads(created_at)")
        con.execute("CREATE INDEX idx_leads_rep ON leads(rep_id)")
        con.executescript(VIEWS_SQL.read_text())

    print(f"Loaded {len(leads):,} leads, {len(reps)} reps, {len(spend):,} spend rows")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()
