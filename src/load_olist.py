"""
Load the REAL Olist marketing-funnel data (Kaggle) into data/funnel.db.

Source: "Marketing Funnel by Olist" – https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist
        (license CC BY-NC-SA 4.0, see data/real_olist/SOURCE.md)

Two tables:
  olist_mql    8,000 marketing qualified leads (sellers who filled in a sign-up form)
  olist_deals    842 of them that a sales rep closed (became a seller on Olist)

Cleaning done here (and logged):
  - empty `origin` -> '(missing)'
  - empty strings -> NULL
  - flags deals whose won_date is before the lead's first contact (data error)

Usage:  python src/load_olist.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "real_olist"
DB_PATH = ROOT / "data" / "funnel.db"
VIEWS_SQL = ROOT / "sql" / "olist" / "00_olist_views.sql"


def main() -> None:
    mql = pd.read_csv(SRC / "olist_marketing_qualified_leads_dataset.csv")
    deals = pd.read_csv(SRC / "olist_closed_deals_dataset.csv")

    # Basic integrity checks before loading
    assert mql["mql_id"].is_unique, "duplicate MQL ids"
    assert deals["mql_id"].is_unique, "duplicate deal ids"
    orphan = (~deals["mql_id"].isin(mql["mql_id"])).sum()
    assert orphan == 0, f"{orphan} deals without a matching lead"

    missing_origin = mql["origin"].isna().sum()
    mql["origin"] = mql["origin"].fillna("(missing)")
    mql["first_contact_date"] = pd.to_datetime(mql["first_contact_date"]).dt.strftime("%Y-%m-%d")
    deals["won_date"] = pd.to_datetime(deals["won_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as con:
        mql.to_sql("olist_mql", con, index=False, if_exists="replace")
        deals.to_sql("olist_deals", con, index=False, if_exists="replace")
        con.executescript(VIEWS_SQL.read_text())
        bad_dates = con.execute(
            "SELECT COUNT(*) FROM v_olist_leads WHERE days_to_close < 0").fetchone()[0]

    print(f"Loaded {len(mql):,} real MQLs and {len(deals):,} closed deals (Olist, Kaggle)")
    print(f"  {missing_origin} leads without origin -> '(missing)'")
    print(f"  {bad_dates} deal(s) won before first contact (kept, flagged in data-quality query)")


if __name__ == "__main__":
    main()
