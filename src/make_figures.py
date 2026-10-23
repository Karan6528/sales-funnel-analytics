"""
Create the static charts used in the README and the management summary
(reports/figures/*.png) from the SQL outputs in outputs/.

Usage:  python src/make_figures.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "reports" / "figures"

BASE = "#2A6F97"      # one hue for "normal" bars
HIGHLIGHT = "#D1495B"  # the bar the chart is about
INK = "#1F2933"
MUTED = "#6B7785"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#C9D1D9",
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
    "axes.titlesize": 12, "axes.titlecolor": INK, "axes.titlelocation": "left",
})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)
    print(f"  saved reports/figures/{name}")


def hbar(ax, labels, values, colors, fmt):
    bars = ax.barh(labels, values, color=colors, height=0.6)
    ax.invert_yaxis()
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    for b, v in zip(bars, values):
        ax.text(b.get_width() + max(values) * 0.01, b.get_y() + b.get_height() / 2,
                fmt(v), va="center", color=INK, fontsize=9)


def funnel():
    df = pd.read_csv(OUT / "01_funnel_overview.csv")
    worst = df.loc[1:, "lost_at_this_step"].idxmax()
    colors = [HIGHLIGHT if i == worst else BASE for i in df.index]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    step = dict(zip(df["volume"], df["step_conversion_pct"]))
    hbar(ax, df["stage"], df["volume"], colors,
         lambda v: f"{v:,.0f}" if step[v] == 100 else f"{v:,.0f}  ({step[v]:.0f}% of previous stage)")
    ax.set_title("Most leads are lost between first call and appointment")
    save(fig, "01_funnel.png")


def channels():
    df = pd.read_csv(OUT / "02_channel_performance.csv").sort_values("cost_per_signed")
    colors = [HIGHLIGHT if c == "Meta Ads" else BASE for c in df["channel"]]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    hbar(ax, df["channel"], df["cost_per_signed"], colors, lambda v: f"€{v:,.0f}")
    ax.set_title("Cost per signed contract: Meta has cheap leads but costly contracts")
    save(fig, "02_cac_by_channel.png")


def speed():
    df = pd.read_csv(OUT / "03_speed_to_lead.csv")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    bars = ax.bar(df["speed_to_lead_bucket"], df["appointment_rate_pct"], color=BASE, width=0.6)
    bars[0].set_color(HIGHLIGHT)
    for b, v in zip(bars, df["appointment_rate_pct"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}%", ha="center", color=INK, fontsize=9)
    ax.set_ylabel("Appointment rate")
    ax.set_xlabel("Time from lead to first call")
    ax.set_ylim(0, df["appointment_rate_pct"].max() * 1.2)
    ax.set_title("Leads called within 1 hour book 2x more appointments than next-day calls")
    save(fig, "03_speed_to_lead.png")


def offer_speed():
    df = pd.read_csv(OUT / "07_offer_speed.csv")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    bars = ax.bar(df["offer_speed_bucket"], df["offer_to_signed_pct"], color=BASE, width=0.55)
    bars[-1].set_color(HIGHLIGHT)
    for b, v in zip(bars, df["offer_to_signed_pct"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}%", ha="center", color=INK, fontsize=9)
    ax.set_ylabel("Offer → signed")
    ax.set_xlabel("Days from appointment to offer")
    ax.set_ylim(0, df["offer_to_signed_pct"].max() * 1.2)
    ax.set_title("Offers sent after 7+ days close at less than half the rate")
    save(fig, "04_offer_speed.png")


def teams():
    df = pd.read_csv(OUT / "04_team_performance.csv")
    metrics = [("contacted_within_4h_pct", "Called < 4h"), ("appt_to_offer_pct", "Appt → offer"),
               ("offer_to_signed_pct", "Offer → signed"), ("lead_to_signed_pct", "Lead → signed")]
    fig, axes = plt.subplots(1, 4, figsize=(10, 3.2), sharey=True)
    for ax, (col, label) in zip(axes, metrics):
        colors = [HIGHLIGHT if t == "Team West" else BASE for t in df["team"]]
        bars = ax.barh(df["team"], df[col], color=colors, height=0.6)
        ax.invert_yaxis()
        ax.set_title(label, fontsize=10)
        ax.xaxis.set_visible(False)
        ax.spines["bottom"].set_visible(False)
        for b, v in zip(bars, df[col]):
            ax.text(b.get_width() + df[col].max() * 0.03, b.get_y() + b.get_height() / 2,
                    f"{v:.0f}%", va="center", fontsize=8.5, color=INK)
        ax.set_xlim(0, df[col].max() * 1.35)
    fig.suptitle("Team West is behind at every stage it controls", x=0.01, ha="left",
                 fontweight="bold", color=INK)
    save(fig, "05_teams.png")


def weekly():
    df = pd.read_csv(OUT / "06_weekly_kpis.csv", parse_dates=["week_start"])
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.plot(df["week_start"], df["contracts_signed"], color=BASE, lw=2, marker="o", ms=4,
            label="Contracts signed")
    ax.plot(df["week_start"], df["signed_4wk_avg"], color=MUTED, lw=2, ls="--", label="4-week average")
    ax.set_ylim(0, df["contracts_signed"].max() * 1.25)
    ax.grid(axis="y", color="#EEF1F4")
    ax.legend(frameon=False, loc="lower right")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax.set_title("Contracts signed per week – last 12 weeks")
    save(fig, "06_weekly_signed.png")


# ------------------------------------------------ real data: Olist (Kaggle) --
OLIST = OUT / "olist"


def olist_monthly():
    df = pd.read_csv(OLIST / "01_olist_monthly.csv")
    colors = [BASE if n == "in window" else "#C9D1D9" for n in df["note"]]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    bars = ax.bar(df["lead_month"], df["conversion_pct"], color=colors, width=0.65)
    for b, v in zip(bars, df["conversion_pct"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.0f}%", ha="center", fontsize=8, color=INK)
    ax.set_ylabel("Lead → deal")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.text(2.5, df["conversion_pct"].max() * 0.75, "grey: deal data starts Dec 2017,\n"
            "so 2017 leads are excluded", fontsize=8.5, color=MUTED, ha="center")
    ax.set_title("Real data: conversion by lead month")
    save(fig, "olist_01_monthly.png")


def olist_channels():
    df = pd.read_csv(OLIST / "02_olist_channels.csv")
    df = df[df["mqls"] >= 100].sort_values("conversion_pct", ascending=False)
    colors = [HIGHLIGHT if o in ("social", "email") else BASE for o in df["origin"]]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    hbar(ax, [f"{o}  ({n:,} leads)" for o, n in zip(df["origin"], df["mqls"])],
         df["conversion_pct"], colors, lambda v: f"{v:.1f}%")
    ax.set_title("Real data: social and email leads rarely become sellers")
    save(fig, "olist_02_channels.png")


def olist_pages():
    df = pd.read_csv(OLIST / "04_olist_page_within_channel.csv")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = range(len(df))
    ax.barh([i - 0.2 for i in y], df["conv_top_pages_pct"], height=0.38, color=BASE,
            label="Top-2 landing pages")
    ax.barh([i + 0.2 for i in y], df["conv_other_pages_pct"], height=0.38, color="#B8C4CE",
            label="All other pages")
    for i, (a, b) in enumerate(zip(df["conv_top_pages_pct"], df["conv_other_pages_pct"])):
        ax.text(a + 0.4, i - 0.2, f"{a:.0f}%", va="center", fontsize=8.5, color=INK)
        ax.text(b + 0.4, i + 0.2, f"{b:.0f}%", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(list(y), df["origin"])
    ax.invert_yaxis()
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xlim(0, df["conv_top_pages_pct"].max() * 1.5)
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    ax.set_title("Real data: the top-2 pages win inside the same channel (except paid)")
    save(fig, "olist_03_pages_within_channel.png")


def olist_closers():
    df = pd.read_csv(OLIST / "06_olist_closer_concentration.csv")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    colors = [BASE if c <= 50.6 else "#B8C4CE" for c in df["cumulative_share_pct"]]
    ax.bar(df["rank"], df["deals"], color=colors, width=0.7)
    ax.set_xlabel("Sales reps, ranked by deals closed")
    ax.set_ylabel("Deals")
    ax.set_xticks(df["rank"])
    ax.tick_params(axis="x", labelsize=7.5)
    ax.text(len(df) * 0.55, df["deals"].max() * 0.7,
            f"Top 5 of {len(df)} reps close {df['cumulative_share_pct'].iloc[4]:.0f}% of deals",
            fontsize=10, color=INK, fontweight="bold")
    ax.set_title("Real data: deal volume depends on a few closers")
    save(fig, "olist_04_closers.png")


def main():
    for f in [funnel, channels, speed, offer_speed, teams, weekly,
              olist_monthly, olist_channels, olist_pages, olist_closers]:
        f()


if __name__ == "__main__":
    main()
