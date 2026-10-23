"""
Generate a realistic (synthetic) residential-solar sales funnel dataset.

The data imitates how a German solar company tracks leads from first contact
to installation:  Lead -> Contacted -> Appointment -> Offer -> Signed -> Installed

Why synthetic?  Real sales data is confidential. The generator is built so that
the patterns an analyst would look for in real life (channel quality, speed to
lead, slow offers, team differences, seasonality) are present but NOT labelled.
The analysis has to find them.

The raw export is deliberately a bit messy (duplicates, inconsistent labels,
missing values) to mirror a real CRM export. `src/clean_data.py` fixes it.

Usage:  python src/generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
START = pd.Timestamp("2025-01-06")          # Monday
END = pd.Timestamp("2026-09-27 23:59:59")   # Sunday, "today" for the data
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

rng = np.random.default_rng(SEED)

# --------------------------------------------------------------------------
# Business assumptions
# --------------------------------------------------------------------------
CHANNELS = {
    # name: (weekly leads, cost per lead EUR, lead quality multiplier)
    "Google Ads":        (40, 55, 1.00),
    "Meta Ads":          (46, 28, 0.55),
    "Comparison Portal": (20, 72, 0.85),
    "Website Organic":   (18, 15, 1.05),
    "Referral":          (12, 40, 1.55),
    "Partner Network":   (10, 90, 1.10),
    "Field Sales":       (15, 60, 0.90),
}

REGIONS = {
    # region: (share of leads, sales team)
    "Berlin":                 (0.10, "Team East"),
    "Brandenburg":            (0.06, "Team East"),
    "Saxony":                 (0.07, "Team East"),
    "Hamburg":                (0.05, "Team North"),
    "Lower Saxony":           (0.11, "Team North"),
    "Schleswig-Holstein":     (0.05, "Team North"),
    "North Rhine-Westphalia": (0.20, "Team West"),
    "Hesse":                  (0.08, "Team West"),
    "Bavaria":                (0.16, "Team South"),
    "Baden-Wuerttemberg":     (0.12, "Team South"),
}

PRODUCTS = {
    # product: (share, mean contract value EUR, signing multiplier)
    "Solar":                        (0.30, 14_500, 0.95),
    "Solar + Battery":              (0.45, 22_000, 1.05),
    "Solar + Battery + Wallbox":    (0.13, 24_500, 1.05),
    "Solar + Battery + Heat Pump":  (0.12, 39_000, 0.85),
}

# Team behaviour: (median hours to first contact, appointment->offer rate,
#                  median days appointment->offer)
TEAMS = {
    "Team East":  (3.0, 0.78, 3.0),
    "Team North": (5.0, 0.76, 3.5),
    "Team West":  (9.0, 0.60, 6.5),   # slow + leaky: the planted problem
    "Team South": (4.0, 0.77, 3.0),
}

FIRST_NAMES = ["Lena", "Jonas", "Mia", "Felix", "Sara", "Paul", "Hannah", "Lukas",
               "Emma", "Leon", "Clara", "Noah", "Lea", "Ben", "Marie", "Elias",
               "Anna", "Tim", "Julia", "David", "Nina", "Max", "Sophie", "Ali"]
LAST_NAMES = ["Schmidt", "Weber", "Becker", "Wagner", "Hoffmann", "Koch", "Richter",
              "Klein", "Wolf", "Neumann", "Schwarz", "Braun", "Zimmermann", "Krueger",
              "Hartmann", "Lange", "Werner", "Krause", "Lehmann", "Koehler", "Maier",
              "Fuchs", "Peters", "Yilmaz"]


def seasonality(ts: pd.Timestamp) -> float:
    """Solar demand peaks in spring/summer and drops around Christmas."""
    month_factor = {1: 0.75, 2: 0.85, 3: 1.10, 4: 1.25, 5: 1.25, 6: 1.15,
                    7: 1.05, 8: 0.95, 9: 1.00, 10: 0.95, 11: 0.85, 12: 0.65}
    return month_factor[ts.month]


def speed_factor(hours: float) -> float:
    """Leads contacted quickly book far more appointments (speed to lead)."""
    if hours < 1:
        return 1.40
    if hours < 4:
        return 1.15
    if hours < 24:
        return 1.00
    if hours < 72:
        return 0.70
    return 0.45


def offer_delay_factor(days: float) -> float:
    """Offers that take long to arrive go cold."""
    if days <= 3:
        return 1.20
    if days <= 7:
        return 1.00
    return 0.60


# --------------------------------------------------------------------------
# Sales reps
# --------------------------------------------------------------------------
def make_reps() -> pd.DataFrame:
    rows, used = [], set()
    rep_no = 1
    for team in TEAMS:
        for _ in range(6):
            while True:
                name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
                if name not in used:
                    used.add(name)
                    break
            skill = float(np.clip(rng.normal(1.0, 0.12), 0.7, 1.3))
            hire = START - pd.Timedelta(days=int(rng.integers(30, 900)))
            rows.append({"rep_id": f"R{rep_no:03d}", "rep_name": name, "team": team,
                         "hire_date": hire.date(), "_skill": skill})
            rep_no += 1
    reps = pd.DataFrame(rows)
    # Two clear outliers so the rep leaderboard has a story
    reps.loc[reps["rep_id"] == "R003", "_skill"] = 1.35
    reps.loc[reps["rep_id"] == "R016", "_skill"] = 0.65
    return reps


# --------------------------------------------------------------------------
# Leads and their journey through the funnel
# --------------------------------------------------------------------------
def make_leads(reps: pd.DataFrame) -> pd.DataFrame:
    reps_by_team = {t: g for t, g in reps.groupby("team")}
    region_names = list(REGIONS)
    region_p = np.array([REGIONS[r][0] for r in region_names])
    region_p /= region_p.sum()
    product_names = list(PRODUCTS)
    product_p = np.array([PRODUCTS[p][0] for p in product_names])

    weeks = pd.date_range(START, END, freq="W-MON")
    n_weeks = len(weeks)
    records = []
    lead_no = 100_000

    for w_idx, week in enumerate(weeks):
        growth = 1.0 + 0.25 * (w_idx / n_weeks)   # business is growing
        for channel, (base, _cpl, quality) in CHANNELS.items():
            n = rng.poisson(base * growth * seasonality(week))
            for _ in range(n):
                lead_no += 1
                created = week + pd.Timedelta(minutes=int(rng.integers(0, 7 * 24 * 60)))
                if created > END:
                    continue
                region = rng.choice(region_names, p=region_p)
                team = REGIONS[region][1]
                rep = reps_by_team[team].sample(1, random_state=int(rng.integers(1e9))).iloc[0]
                product = rng.choice(product_names, p=product_p)
                financing = "Rental" if rng.random() < 0.55 else "Purchase"
                bill = round(float(np.clip(rng.normal(130, 45), 40, 400)), 0)

                rec = {
                    "lead_id": f"L{lead_no}", "created_at": created, "channel": channel,
                    "region": region, "product_interest": product,
                    "financing_type": financing, "monthly_bill_eur": bill,
                    "rep_id": rep["rep_id"], "first_contact_at": pd.NaT,
                    "appointment_at": pd.NaT, "offer_sent_at": pd.NaT,
                    "contract_signed_at": pd.NaT, "installed_at": pd.NaT,
                    "cancelled_at": pd.NaT, "lost_reason": None,
                    "contract_value_eur": np.nan,
                }

                # 1) First contact ------------------------------------------
                median_h, appt_to_offer, offer_days = TEAMS[team]
                hours = float(rng.lognormal(np.log(median_h), 1.1))
                if created.dayofweek >= 5:           # weekend leads wait longer
                    hours += rng.uniform(12, 40)
                if rng.random() > 0.90:              # never reached
                    rec["lost_reason"] = "Unreachable"
                    records.append(rec)
                    continue
                contact = created + pd.Timedelta(hours=hours)
                if contact > END:
                    records.append(rec)
                    continue
                rec["first_contact_at"] = contact

                # 2) Appointment (site visit / consultation) ----------------
                p_appt = 0.42 * quality * speed_factor(hours)
                if rng.random() > min(p_appt, 0.92):
                    rec["lost_reason"] = rng.choice(
                        ["Not interested", "Only gathering information",
                         "Rents home / not owner", "Unreachable"],
                        p=[0.40, 0.30, 0.15, 0.15])
                    records.append(rec)
                    continue
                appt = contact + pd.Timedelta(days=float(rng.uniform(1, 10)))
                if appt > END:
                    records.append(rec)
                    continue
                rec["appointment_at"] = appt

                # 3) Offer ----------------------------------------------------
                if rng.random() > appt_to_offer:
                    rec["lost_reason"] = rng.choice(
                        ["Roof not suitable", "Not interested", "Chose competitor"],
                        p=[0.45, 0.30, 0.25])
                    records.append(rec)
                    continue
                o_days = float(rng.gamma(2.0, offer_days / 2.0))
                offer = appt + pd.Timedelta(days=o_days)
                if offer > END:
                    records.append(rec)
                    continue
                rec["offer_sent_at"] = offer
                mean_value = PRODUCTS[product][1]
                rec["contract_value_eur"] = round(float(rng.normal(mean_value, mean_value * 0.15)), -1)

                # 4) Signing --------------------------------------------------
                p_sign = (0.40 * np.sqrt(quality) * offer_delay_factor(o_days)
                          * PRODUCTS[product][2] * rep["_skill"]
                          * (1.15 if financing == "Rental" else 0.88))
                if rng.random() > min(p_sign, 0.95):
                    rec["lost_reason"] = rng.choice(
                        ["Price too high", "Chose competitor", "Financing rejected",
                         "Postponed decision"],
                        p=[0.38, 0.32, 0.12, 0.18])
                    records.append(rec)
                    continue
                signed = offer + pd.Timedelta(days=float(rng.uniform(1, 21)))
                if signed > END:
                    records.append(rec)
                    continue
                rec["contract_signed_at"] = signed

                # 5) Installation or cancellation ---------------------------
                if rng.random() < 0.05:
                    cancel = signed + pd.Timedelta(days=float(rng.uniform(3, 14)))
                    if cancel <= END:
                        rec["cancelled_at"] = cancel
                        rec["lost_reason"] = "Cancelled after signing"
                    records.append(rec)
                    continue
                install = signed + pd.Timedelta(days=float(rng.uniform(28, 80)))
                if install <= END:
                    rec["installed_at"] = install
                records.append(rec)

    leads = pd.DataFrame(records)
    for col in ["created_at", "first_contact_at", "appointment_at", "offer_sent_at",
                "contract_signed_at", "installed_at", "cancelled_at"]:
        leads[col] = pd.to_datetime(leads[col]).dt.floor("min")
    return leads.sort_values("created_at").reset_index(drop=True)


def make_spend(leads: pd.DataFrame) -> pd.DataFrame:
    """Weekly marketing spend per channel, roughly leads x cost per lead."""
    tmp = leads.assign(week_start=leads["created_at"].dt.to_period("W-SUN").dt.start_time)
    counts = tmp.groupby(["week_start", "channel"]).size().rename("leads").reset_index()
    counts["spend_eur"] = [
        round(n * CHANNELS[c][1] * rng.uniform(0.85, 1.15), 2)
        for n, c in zip(counts["leads"], counts["channel"])
    ]
    return counts[["week_start", "channel", "spend_eur"]]


def make_messy(leads: pd.DataFrame) -> pd.DataFrame:
    """Introduce the kind of problems a real CRM export has."""
    messy = leads.copy()
    # Inconsistent channel labels
    variants = {"Google Ads": ["google ads", "Google ads", "GoogleAds"],
                "Meta Ads": ["Facebook/Instagram", "meta ads", "Meta Ads "],
                "Website Organic": ["website", "SEO"],
                "Referral": ["referral", "Empfehlung"]}
    for clean, alts in variants.items():
        idx = messy.index[messy["channel"] == clean]
        pick = rng.choice(idx, size=int(len(idx) * 0.06), replace=False)
        messy.loc[pick, "channel"] = rng.choice(alts, size=len(pick))
    # Missing regions
    pick = rng.choice(messy.index, size=int(len(messy) * 0.004), replace=False)
    messy.loc[pick, "region"] = np.nan
    # Duplicate rows (double sync from the web form)
    dups = messy.sample(frac=0.012, random_state=SEED)
    messy = pd.concat([messy, dups]).sort_values("created_at").reset_index(drop=True)
    return messy


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    reps = make_reps()
    leads = make_leads(reps)
    spend = make_spend(leads)
    messy = make_messy(leads)

    reps.drop(columns="_skill").to_csv(RAW_DIR / "sales_reps.csv", index=False)
    spend.to_csv(RAW_DIR / "marketing_spend.csv", index=False)
    messy.to_csv(RAW_DIR / "leads_raw.csv", index=False)

    print(f"Leads (clean)   : {len(leads):,}")
    print(f"Leads raw export: {len(messy):,} rows (with duplicates)")
    print(f"Reps            : {len(reps)}")
    print(f"Spend rows      : {len(spend):,}")
    print(f"Saved to        : {RAW_DIR}")


if __name__ == "__main__":
    main()
