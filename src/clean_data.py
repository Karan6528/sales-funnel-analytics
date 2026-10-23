"""
Clean the raw CRM export and add the helper columns the analysis needs.

Steps (each one is logged so the cleaning is auditable):
  1. Remove exact duplicate leads (double form submissions / sync errors)
  2. Standardise channel labels ("google ads", "GoogleAds" -> "Google Ads")
  3. Fill missing regions with "Unknown"
  4. Parse timestamps
  5. Add analysis columns: stage reached, status, week buckets, durations

Usage:  python src/clean_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

DATE_COLS = ["created_at", "first_contact_at", "appointment_at", "offer_sent_at",
             "contract_signed_at", "installed_at", "cancelled_at"]

CHANNEL_MAP = {
    "google ads": "Google Ads", "googleads": "Google Ads",
    "meta ads": "Meta Ads", "facebook/instagram": "Meta Ads",
    "website": "Website Organic", "seo": "Website Organic",
    "website organic": "Website Organic",
    "referral": "Referral", "empfehlung": "Referral",
    "comparison portal": "Comparison Portal",
    "partner network": "Partner Network",
    "field sales": "Field Sales",
}

STAGES = ["Lead", "Contacted", "Appointment", "Offer", "Signed", "Installed"]


def week_start(s: pd.Series) -> pd.Series:
    """Monday of the ISO week, as a date."""
    return s.dt.to_period("W-SUN").dt.start_time


def clean_leads(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    n0 = len(df)

    # 1. Duplicates
    df = df.drop_duplicates()
    print(f"  removed {n0 - len(df):,} duplicate rows")

    # 2. Channel labels
    before = df["channel"].nunique()
    key = df["channel"].str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
    df["channel"] = key.map(CHANNEL_MAP)
    unmapped = df["channel"].isna().sum()
    if unmapped:
        raise ValueError(f"{unmapped} channel labels could not be mapped")
    print(f"  channel labels: {before} variants -> {df['channel'].nunique()} channels")

    # 3. Missing regions
    missing = df["region"].isna().sum()
    df["region"] = df["region"].fillna("Unknown")
    print(f"  filled {missing} missing regions with 'Unknown'")

    # 4. Dates
    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col])

    # 5. Analysis columns
    reached = pd.DataFrame({
        "Lead": True,
        "Contacted": df["first_contact_at"].notna(),
        "Appointment": df["appointment_at"].notna(),
        "Offer": df["offer_sent_at"].notna(),
        "Signed": df["contract_signed_at"].notna(),
        "Installed": df["installed_at"].notna(),
    })
    df["stage_reached"] = reached.apply(lambda r: STAGES[int(r.values.sum()) - 1], axis=1)

    df["status"] = np.select(
        [df["cancelled_at"].notna(), df["installed_at"].notna(),
         df["contract_signed_at"].notna(), df["lost_reason"].notna()],
        ["Cancelled", "Installed", "Signed (awaiting install)", "Lost"],
        default="Open",
    )

    df["lead_week"] = week_start(df["created_at"])
    df["lead_month"] = df["created_at"].dt.to_period("M").astype(str)
    df["signed_week"] = week_start(df["contract_signed_at"])

    df["hours_to_contact"] = ((df["first_contact_at"] - df["created_at"])
                              .dt.total_seconds() / 3600).round(2)
    df["days_appt_to_offer"] = ((df["offer_sent_at"] - df["appointment_at"])
                                .dt.total_seconds() / 86400).round(2)
    df["days_lead_to_signed"] = ((df["contract_signed_at"] - df["created_at"])
                                 .dt.total_seconds() / 86400).round(2)

    df["speed_to_lead_bucket"] = pd.cut(
        df["hours_to_contact"], bins=[-0.01, 1, 4, 24, 72, np.inf],
        labels=["Under 1h", "1-4h", "4-24h", "1-3 days", "Over 3 days"]).astype(str)
    df.loc[df["hours_to_contact"].isna(), "speed_to_lead_bucket"] = "Not contacted"

    df["offer_speed_bucket"] = pd.cut(
        df["days_appt_to_offer"], bins=[-0.01, 3, 7, np.inf],
        labels=["Up to 3 days", "4-7 days", "Over 7 days"]).astype(str)
    df.loc[df["days_appt_to_offer"].isna(), "offer_speed_bucket"] = "No offer"

    df["is_signed"] = df["contract_signed_at"].notna().astype(int)
    return df.sort_values("created_at").reset_index(drop=True)


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("Cleaning leads ...")
    leads = clean_leads(pd.read_csv(RAW / "leads_raw.csv"))
    reps = pd.read_csv(RAW / "sales_reps.csv")
    spend = pd.read_csv(RAW / "marketing_spend.csv", parse_dates=["week_start"])

    leads = leads.merge(reps[["rep_id", "team"]], on="rep_id", how="left")

    leads.to_csv(PROCESSED / "leads_clean.csv", index=False)
    reps.to_csv(PROCESSED / "sales_reps.csv", index=False)
    spend.to_csv(PROCESSED / "marketing_spend.csv", index=False)
    print(f"Saved {len(leads):,} clean leads to {PROCESSED}")


if __name__ == "__main__":
    main()
