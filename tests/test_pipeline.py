"""
Data-quality and reconciliation tests.

Run after the pipeline:   python run_all.py   then   pytest -q
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "dashboard"))
import metrics as m  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
VALID_CHANNELS = {"Google Ads", "Meta Ads", "Comparison Portal", "Website Organic",
                  "Referral", "Partner Network", "Field Sales"}
STAGE_ORDER = ["created_at", "first_contact_at", "appointment_at", "offer_sent_at",
               "contract_signed_at", "installed_at"]


@pytest.fixture(scope="module")
def leads():
    return pd.read_csv(PROCESSED / "leads_clean.csv", parse_dates=STAGE_ORDER + ["cancelled_at"])


# ------------------------------------------------------------ data quality --
def test_no_duplicate_leads(leads):
    assert leads["lead_id"].is_unique


def test_channels_are_standardised(leads):
    assert set(leads["channel"]) == VALID_CHANNELS


def test_no_missing_required_fields(leads):
    for col in ["lead_id", "created_at", "channel", "region", "rep_id", "team"]:
        assert leads[col].notna().all(), col


def test_stage_dates_are_in_order(leads):
    for earlier, later in zip(STAGE_ORDER, STAGE_ORDER[1:]):
        both = leads[[earlier, later]].dropna()
        assert (both[later] >= both[earlier]).all(), f"{later} before {earlier}"


def test_no_stage_skipped(leads):
    # A lead can't sign without an offer, or get an offer without an appointment, ...
    for earlier, later in zip(STAGE_ORDER, STAGE_ORDER[1:]):
        assert not (leads[later].notna() & leads[earlier].isna()).any(), later


def test_signed_deals_have_value(leads):
    signed = leads[leads["contract_signed_at"].notna()]
    assert (signed["contract_value_eur"] > 0).all()


# ---------------------------------------------------------- reconciliation --
def test_dashboard_matches_sql_funnel():
    """The Python dashboard and the SQL analysis must report the same numbers."""
    leads, _, _ = m.load_data()
    mature = leads[leads["created_at"] < m.COHORT_CUTOFF]
    py = m.funnel(mature).set_index("stage")["leads"]
    sql = pd.read_csv(OUTPUTS / "01_funnel_overview.csv").set_index("stage")["volume"]
    pd.testing.assert_series_equal(py, sql, check_names=False, check_dtype=False)


def test_dashboard_matches_sql_channels():
    leads, _, spend = m.load_data()
    mature = leads[leads["created_at"] < m.COHORT_CUTOFF]
    spend = spend[spend["week_start"] < m.COHORT_CUTOFF]
    py = m.channel_table(mature, spend).set_index("channel")
    sql = pd.read_csv(OUTPUTS / "02_channel_performance.csv").set_index("channel")
    assert (py["signed"] == sql["signed"]).all()
    assert (py["cac"].round(0) - sql["cost_per_signed"]).abs().max() <= 1


def test_raw_export_had_duplicates_removed():
    raw = pd.read_csv(ROOT / "data" / "raw" / "leads_raw.csv")
    with sqlite3.connect(m.DB_PATH) as con:
        n_db = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    assert len(raw) > n_db == raw["lead_id"].nunique()


# ------------------------------------------------ real data: Olist (Kaggle) --
def test_olist_every_deal_links_to_a_lead():
    with sqlite3.connect(m.DB_PATH) as con:
        orphans = con.execute(
            "SELECT COUNT(*) FROM olist_deals WHERE mql_id NOT IN (SELECT mql_id FROM olist_mql)"
        ).fetchone()[0]
        n_mql, n_deals = con.execute(
            "SELECT (SELECT COUNT(*) FROM olist_mql), (SELECT COUNT(*) FROM olist_deals)").fetchone()
    assert orphans == 0
    assert (n_mql, n_deals) == (8000, 842)   # matches the published Kaggle dataset


def test_olist_dashboard_matches_sql_channels():
    py = m.olist_channels(m.load_olist()).set_index("origin")
    sql = pd.read_csv(OUTPUTS / "olist" / "02_olist_channels.csv").set_index("origin")
    assert (py["deals"] == sql["deals"]).all()
    assert ((py["conversion"] * 100).round(1) == sql["conversion_pct"]).all()
