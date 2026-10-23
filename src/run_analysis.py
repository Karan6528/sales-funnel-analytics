"""
Run every analysis query in sql/ against data/funnel.db, save each result to
outputs/<query_name>.csv and print a short preview.

Also writes outputs/key_metrics.json with the headline numbers used in the
management summary.

Usage:  python src/run_analysis.py
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "funnel.db"
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "outputs"

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)


def run_query(con: sqlite3.Connection, path: Path) -> pd.DataFrame:
    return pd.read_sql_query(path.read_text(), con)


def key_metrics(results: dict[str, pd.DataFrame]) -> dict:
    funnel = results["01_funnel_overview"].set_index("stage")
    channels = results["02_channel_performance"].set_index("channel")
    speed = results["03_speed_to_lead"].set_index("speed_to_lead_bucket")
    teams = results["04_team_performance"].set_index("team")
    offer = results["07_offer_speed"].set_index("offer_speed_bucket")

    best_cac = channels["cost_per_signed"].idxmin()
    worst_cac = channels["cost_per_signed"].idxmax()
    return {
        "mature_cohort_leads": int(funnel.loc["Lead", "volume"]),
        "signed_contracts": int(funnel.loc["Signed", "volume"]),
        "lead_to_signed_pct": float(funnel.loc["Signed", "overall_conversion_pct"]),
        "biggest_drop_step": funnel.iloc[1:]["lost_at_this_step"].idxmax(),
        "best_channel_by_cac": best_cac,
        "best_channel_cac_eur": float(channels.loc[best_cac, "cost_per_signed"]),
        "worst_channel_by_cac": worst_cac,
        "worst_channel_cac_eur": float(channels.loc[worst_cac, "cost_per_signed"]),
        "appt_rate_contacted_under_1h_pct": float(speed.loc["Under 1h", "appointment_rate_pct"]),
        "appt_rate_contacted_over_3d_pct": float(speed.loc["Over 3 days", "appointment_rate_pct"]),
        "signed_rate_offer_within_3d_pct": float(offer.loc["Up to 3 days", "offer_to_signed_pct"]),
        "signed_rate_offer_over_7d_pct": float(offer.loc["Over 7 days", "offer_to_signed_pct"]),
        "weakest_team": teams["lead_to_signed_pct"].idxmin(),
        "weakest_team_lead_to_signed_pct": float(teams["lead_to_signed_pct"].min()),
        "best_team_lead_to_signed_pct": float(teams["lead_to_signed_pct"].max()),
    }


def run_folder(con, sql_dir: Path, out_dir: Path) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for path in sorted(sql_dir.glob("[0-9][0-9]_*.sql")):
        if path.name.startswith("00_"):
            continue
        df = run_query(con, path)
        results[path.stem] = df
        df.to_csv(out_dir / f"{path.stem}.csv", index=False)
        print(f"\n=== {path.stem} ({len(df)} rows) ===")
        print(df.head(12).to_string(index=False))
    return results


def main() -> None:
    with sqlite3.connect(DB_PATH) as con:
        print("######## Case study 1: solar funnel (simulated) ########")
        results = run_folder(con, SQL_DIR, OUT_DIR)
        print("\n######## Case study 2: Olist marketing funnel (real data) ########")
        run_folder(con, SQL_DIR / "olist", OUT_DIR / "olist")

    metrics = key_metrics(results)
    (OUT_DIR / "key_metrics.json").write_text(json.dumps(metrics, indent=2))
    print("\n=== Key metrics ===")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
