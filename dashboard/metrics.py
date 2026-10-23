"""
Pure-pandas KPI calculations used by the Streamlit dashboard.

Kept separate from the UI so the logic is testable (see tests/) and the same
numbers can be reused elsewhere.
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "funnel.db"
COHORT_CUTOFF = pd.Timestamp("2026-08-01")

STAGES = [
    ("Lead", None),
    ("Contacted", "first_contact_at"),
    ("Appointment", "appointment_at"),
    ("Offer", "offer_sent_at"),
    ("Signed", "contract_signed_at"),
    ("Installed", "installed_at"),
]
SPEED_ORDER = ["Under 1h", "1-4h", "4-24h", "1-3 days", "Over 3 days"]
OFFER_ORDER = ["Up to 3 days", "4-7 days", "Over 7 days"]
DATE_COLS = ["created_at", "first_contact_at", "appointment_at", "offer_sent_at",
             "contract_signed_at", "installed_at", "cancelled_at"]


def load_data(db_path: Path = DB_PATH) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with sqlite3.connect(db_path) as con:
        leads = pd.read_sql_query("SELECT * FROM leads", con, parse_dates=DATE_COLS)
        reps = pd.read_sql_query("SELECT * FROM sales_reps", con)
        spend = pd.read_sql_query("SELECT * FROM marketing_spend", con,
                                  parse_dates=["week_start"])
    return leads, reps, spend


def filter_leads(leads: pd.DataFrame, start, end, channels=None, teams=None) -> pd.DataFrame:
    mask = leads["created_at"].between(pd.Timestamp(start),
                                       pd.Timestamp(end) + pd.Timedelta(days=1))
    if channels:
        mask &= leads["channel"].isin(channels)
    if teams:
        mask &= leads["team"].isin(teams)
    return leads[mask]


def funnel(leads: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for stage, col in STAGES:
        n = len(leads) if col is None else int(leads[col].notna().sum())
        rows.append({"stage": stage, "leads": n})
    df = pd.DataFrame(rows)
    df["step_conversion"] = df["leads"] / df["leads"].shift(1)
    df["overall_conversion"] = df["leads"] / df["leads"].iloc[0] if len(leads) else 0.0
    return df


def kpis(leads: pd.DataFrame, spend_total: float) -> dict:
    n = len(leads)
    signed = int(leads["contract_signed_at"].notna().sum())
    appts = int(leads["appointment_at"].notna().sum())
    value = float(leads.loc[leads["contract_signed_at"].notna(), "contract_value_eur"].sum())
    return {
        "leads": n,
        "appointment_rate": appts / n if n else 0.0,
        "lead_to_signed": signed / n if n else 0.0,
        "signed": signed,
        "signed_value": value,
        "cac": spend_total / signed if signed else float("nan"),
    }


def channel_table(leads: pd.DataFrame, spend: pd.DataFrame) -> pd.DataFrame:
    g = leads.groupby("channel").agg(
        leads=("lead_id", "count"),
        appointments=("appointment_at", "count"),
        signed=("contract_signed_at", "count"),
    )
    signed_value = (leads[leads["contract_signed_at"].notna()]
                    .groupby("channel")["contract_value_eur"].sum())
    g["signed_value"] = signed_value.reindex(g.index).fillna(0)
    g["spend"] = spend.groupby("channel")["spend_eur"].sum().reindex(g.index).fillna(0)
    g["lead_to_signed"] = g["signed"] / g["leads"]
    g["cost_per_lead"] = g["spend"] / g["leads"]
    g["cac"] = g["spend"] / g["signed"].where(g["signed"] > 0)
    return g.reset_index().sort_values("cac")


def speed_to_lead(leads: pd.DataFrame) -> pd.DataFrame:
    contacted = leads[leads["first_contact_at"].notna()]
    g = contacted.groupby("speed_to_lead_bucket").agg(
        leads=("lead_id", "count"),
        appointment_rate=("appointment_at", lambda s: s.notna().mean()),
        signed_rate=("contract_signed_at", lambda s: s.notna().mean()),
    )
    return g.reindex(SPEED_ORDER).dropna(how="all").reset_index()


def offer_speed(leads: pd.DataFrame) -> pd.DataFrame:
    offers = leads[leads["offer_sent_at"].notna()]
    g = offers.groupby("offer_speed_bucket").agg(
        offers=("lead_id", "count"),
        signed_rate=("contract_signed_at", lambda s: s.notna().mean()),
    )
    return g.reindex(OFFER_ORDER).dropna(how="all").reset_index()


def team_table(leads: pd.DataFrame) -> pd.DataFrame:
    def rate(num, den):
        return num / den if den else float("nan")

    rows = []
    for team, d in leads.groupby("team"):
        contacted = d["first_contact_at"].notna().sum()
        appts = d["appointment_at"].notna().sum()
        offers = d["offer_sent_at"].notna().sum()
        signed = d["contract_signed_at"].notna().sum()
        rows.append({
            "team": team,
            "leads": len(d),
            "called_within_4h": rate((d["hours_to_contact"] < 4).sum(), contacted),
            "contact_to_appt": rate(appts, contacted),
            "appt_to_offer": rate(offers, appts),
            "avg_days_to_offer": d["days_appt_to_offer"].mean(),
            "offer_to_signed": rate(signed, offers),
            "lead_to_signed": rate(signed, len(d)),
        })
    return pd.DataFrame(rows).sort_values("lead_to_signed", ascending=False)


def rep_table(leads: pd.DataFrame, reps: pd.DataFrame, min_offers: int = 50) -> pd.DataFrame:
    g = leads.groupby("rep_id").agg(
        leads=("lead_id", "count"),
        offers=("offer_sent_at", "count"),
        signed=("contract_signed_at", "count"),
    ).reset_index()
    g = g.merge(reps[["rep_id", "rep_name", "team"]], on="rep_id", how="left")
    g = g[g["offers"] >= min_offers].copy()
    g["close_rate"] = g["signed"] / g["offers"]
    g = g.sort_values("close_rate", ascending=False)
    g.insert(0, "rank", range(1, len(g) + 1))
    return g[["rank", "rep_id", "rep_name", "team", "leads", "offers", "signed", "close_rate"]]


def weekly(leads: pd.DataFrame, weeks: int = 12) -> pd.DataFrame:
    def per_week(col):
        s = leads[col].dropna().dt.to_period("W-SUN").dt.start_time
        return s.value_counts()

    out = pd.DataFrame({
        "new_leads": per_week("created_at"),
        "appointments": per_week("appointment_at"),
        "offers": per_week("offer_sent_at"),
        "signed": per_week("contract_signed_at"),
    }).fillna(0).astype(int).sort_index()
    out.index.name = "week_start"
    return out.tail(weeks).reset_index()


# ------------------------------------------------ real data: Olist (Kaggle) --
OLIST_WINDOW_START = "2018-01-01"


def load_olist(db_path: Path = DB_PATH) -> pd.DataFrame:
    """One row per real Olist lead (MQL), joined to its deal (view v_olist_leads)."""
    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query("SELECT * FROM v_olist_leads", con,
                                 parse_dates=["first_contact_date", "won_date"])


def olist_channels(olist: pd.DataFrame) -> pd.DataFrame:
    w = olist[olist["in_window"] == 1]
    g = w.groupby("origin").agg(mqls=("mql_id", "count"), deals=("is_won", "sum"))
    g["conversion"] = g["deals"] / g["mqls"]
    g["share_of_mqls"] = g["mqls"] / g["mqls"].sum()
    return g.reset_index().sort_values("mqls", ascending=False)


def olist_monthly(olist: pd.DataFrame) -> pd.DataFrame:
    g = olist.groupby("lead_month").agg(mqls=("mql_id", "count"), deals=("is_won", "sum"),
                                        in_window=("in_window", "max"))
    g["conversion"] = g["deals"] / g["mqls"]
    return g.reset_index()
