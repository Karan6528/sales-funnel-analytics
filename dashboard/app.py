"""
Interactive sales-funnel dashboard.

Run from the project root:
    streamlit run dashboard/app.py
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))
import metrics as m  # noqa: E402

BLUE = "#2A6F97"

st.set_page_config(page_title="Solar Sales Funnel", page_icon="☀️", layout="wide")


REQUIRED_TABLES = {"leads", "sales_reps", "marketing_spend", "olist_mql", "olist_deals"}


def db_is_complete() -> bool:
    """True only if the database file exists AND has every table the app needs."""
    if not m.DB_PATH.exists():
        return False
    try:
        with sqlite3.connect(m.DB_PATH) as con:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.Error:
        return False
    return REQUIRED_TABLES <= tables


@st.cache_resource(show_spinner="Building database (first start only) ...")
def build_database() -> str:
    """Build data/funnel.db from the CSVs in the repo (fresh clone, Streamlit Cloud).

    cache_resource makes this run once per server, even if several visitors
    open the app at the same time. Returns "" on success or the error text.
    """
    if db_is_complete():
        return ""
    m.DB_PATH.unlink(missing_ok=True)          # remove a half-built database
    for script in ["load_to_sqlite.py", "load_olist.py"]:
        result = subprocess.run([sys.executable, str(m.ROOT / "src" / script)],
                                cwd=m.ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            m.DB_PATH.unlink(missing_ok=True)
            return f"{script} failed:\n{result.stderr[-1500:]}"
    return "" if db_is_complete() else "Database built but tables are missing."


@st.cache_data
def get_data():
    return m.load_data()


error = build_database()
if error:
    build_database.clear()                     # try again on the next page load
    st.error("Could not build the database. Check that the `data/processed` and "
             f"`data/real_olist` folders are in the repository.\n\n```\n{error}\n```")
    st.stop()

leads_all, reps, spend_all = get_data()

# ------------------------------------------------------------------ sidebar --
st.sidebar.header("Filters")
min_d = leads_all["created_at"].min().date()
max_d = leads_all["created_at"].max().date()
mature_only = st.sidebar.toggle(
    "Mature cohort only", value=True,
    help="Exclude leads created after 31 Jul 2026. They have not had time to sign "
         "yet and would make conversion look worse than it is.")
default_end = (m.COHORT_CUTOFF - pd.Timedelta(days=1)).date() if mature_only else max_d
date_range = st.sidebar.date_input("Lead created between", (min_d, default_end),
                                   min_value=min_d, max_value=max_d)
if len(date_range) != 2:
    st.stop()
start, end = date_range
channels = st.sidebar.multiselect("Channel", sorted(leads_all["channel"].unique()))
teams = st.sidebar.multiselect("Sales team", sorted(leads_all["team"].unique()))

leads = m.filter_leads(leads_all, start, end, channels, teams)
spend = spend_all[spend_all["week_start"].between(pd.Timestamp(start), pd.Timestamp(end))]
if channels:
    spend = spend[spend["channel"].isin(channels)]
if leads.empty:
    st.warning("No leads match these filters.")
    st.stop()

# ---------------------------------------------------------------- header --
st.title("☀️ Solar Sales Funnel Dashboard")
st.caption(f"{len(leads):,} leads · {start:%d %b %Y} – {end:%d %b %Y} · "
           "synthetic data modelled on a residential-solar sales funnel")

k = m.kpis(leads, spend["spend_eur"].sum() if not teams else float("nan"))
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Leads", f"{k['leads']:,}")
c2.metric("Appointment rate", f"{k['appointment_rate']:.1%}")
c3.metric("Lead → signed", f"{k['lead_to_signed']:.1%}")
c4.metric("Signed contract value", f"€{k['signed_value'] / 1e6:,.1f}M")
c5.metric("Cost per signed contract", "–" if pd.isna(k["cac"]) else f"€{k['cac']:,.0f}",
          help="Marketing spend / signed contracts. Hidden when filtering by team, "
               "because spend is not split by team.")

tab_funnel, tab_channels, tab_ops, tab_people, tab_weekly, tab_real = st.tabs(
    ["Funnel", "Channels", "Speed & offers", "Teams & reps", "Weekly report",
     "Real data: Olist"])

# ----------------------------------------------------------------- funnel --
with tab_funnel:
    f = m.funnel(leads)
    fig = go.Figure(go.Funnel(y=f["stage"], x=f["leads"], textinfo="value+percent previous",
                              marker={"color": BLUE}))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10),
                      title="Leads reaching each stage")
    st.plotly_chart(fig, use_container_width=True)
    worst = f.iloc[1:].assign(lost=lambda d: d["leads"].shift(1) - d["leads"]).nlargest(1, "lost")
    if not worst.empty:
        st.info(f"Biggest leak: **{worst['stage'].iloc[0]}** stage – "
                f"{worst['lost'].iloc[0]:,.0f} leads lost before reaching it.")

# --------------------------------------------------------------- channels --
with tab_channels:
    ch = m.channel_table(leads, spend)
    left, right = st.columns(2)
    fig = px.bar(ch.sort_values("cac", ascending=False), x="cac", y="channel", orientation="h",
                 text_auto=",.0f", title="Cost per signed contract (€)",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(height=380, xaxis_title=None, yaxis_title=None)
    left.plotly_chart(fig, use_container_width=True)
    fig = px.bar(ch.sort_values("lead_to_signed"), x="lead_to_signed", y="channel",
                 orientation="h", text_auto=".1%", title="Lead → signed rate",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(height=380, xaxis_title=None, yaxis_title=None, xaxis_tickformat=".0%")
    right.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        ch.style.format({"signed_value": "€{:,.0f}", "spend": "€{:,.0f}",
                         "lead_to_signed": "{:.1%}", "cost_per_lead": "€{:,.0f}",
                         "cac": "€{:,.0f}"}),
        use_container_width=True, hide_index=True)

# ------------------------------------------------------- speed and offers --
with tab_ops:
    left, right = st.columns(2)
    s = m.speed_to_lead(leads)
    fig = px.bar(s, x="speed_to_lead_bucket", y="appointment_rate", text_auto=".0%",
                 title="Appointment rate by time to first call",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(height=380, xaxis_title="Time from lead to first call",
                      yaxis_title=None, yaxis_tickformat=".0%")
    left.plotly_chart(fig, use_container_width=True)
    o = m.offer_speed(leads)
    fig = px.bar(o, x="offer_speed_bucket", y="signed_rate", text_auto=".0%",
                 title="Offer → signed by days to send the offer",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(height=380, xaxis_title="Days from appointment to offer",
                      yaxis_title=None, yaxis_tickformat=".0%")
    right.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------- teams and reps --
with tab_people:
    t = m.team_table(leads)
    st.subheader("Team performance")
    pct_cols = ["called_within_4h", "contact_to_appt", "appt_to_offer",
                "offer_to_signed", "lead_to_signed"]
    st.dataframe(
        t.style.format({**{c: "{:.1%}" for c in pct_cols}, "avg_days_to_offer": "{:.1f}"})
         .background_gradient(subset=pct_cols, cmap="RdYlGn"),
        use_container_width=True, hide_index=True)
    st.subheader("Rep leaderboard (offer → signed, min. 50 offers)")
    r = m.rep_table(leads, reps)
    st.dataframe(r.style.format({"close_rate": "{:.1%}"}).bar(subset=["close_rate"], color="#9CC3DE"),
                 use_container_width=True, hide_index=True)

# ------------------------------------------------------------------ weekly --
with tab_weekly:
    w = m.weekly(m.filter_leads(leads_all, min_d, max_d, channels, teams))
    st.caption("Events counted in the week they happened (independent of the date filter).")
    fig = px.line(w, x="week_start", y=["new_leads", "appointments", "offers", "signed"],
                  markers=True, title="Last 12 weeks")
    fig.update_layout(height=420, xaxis_title=None, yaxis_title=None, legend_title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(w, use_container_width=True, hide_index=True)

# ------------------------------------------------- real data: Olist (Kaggle) --
with tab_real:
    st.subheader("Real B2B sales funnel – Olist marketing funnel (Kaggle)")
    st.caption("8,000 real marketing qualified leads (Jun 2017 – May 2018) and the 842 that "
               "became sellers. Conversion uses leads from 2018 only, because the deals file "
               "starts in Dec 2017. Not affected by the sidebar filters.")
    try:
        olist = m.load_olist()
    except Exception:  # database built before the Olist step was added
        st.warning("Olist tables not found. Run `python run_all.py`.")
        st.stop()
    oc = m.olist_channels(olist)
    w = olist[olist["in_window"] == 1]
    a, b, c = st.columns(3)
    a.metric("Leads (2018)", f"{len(w):,}")
    b.metric("Deals", f"{int(w['is_won'].sum()):,}")
    c.metric("Lead → deal", f"{w['is_won'].mean():.1%}")
    left, right = st.columns(2)
    fig = px.bar(oc[oc["mqls"] >= 100].sort_values("conversion"), x="conversion", y="origin",
                 orientation="h", text_auto=".1%", title="Conversion by channel (≥100 leads)",
                 color_discrete_sequence=[BLUE])
    fig.update_layout(height=380, xaxis_title=None, yaxis_title=None, xaxis_tickformat=".0%")
    left.plotly_chart(fig, use_container_width=True)
    om = m.olist_monthly(olist)
    om["period"] = om["in_window"].map({1: "Analysis window", 0: "Excluded (deal data incomplete)"})
    fig = px.bar(om, x="lead_month", y="conversion", color="period", text_auto=".0%",
                 title="Conversion by lead month",
                 color_discrete_map={"Analysis window": BLUE,
                                     "Excluded (deal data incomplete)": "#C9D1D9"})
    fig.update_layout(height=380, xaxis_title=None, yaxis_title=None, yaxis_tickformat=".0%",
                      legend_title=None)
    right.plotly_chart(fig, use_container_width=True)
    st.dataframe(oc.style.format({"conversion": "{:.1%}", "share_of_mqls": "{:.1%}"}),
                 use_container_width=True, hide_index=True)
