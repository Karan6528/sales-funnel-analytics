# 📈 Sales Funnel Analytics: SQL · Excel · Python

![pipeline](https://github.com/Karan6528/sales-funnel-analytics/actions/workflows/pipeline.yml/badge.svg)

Two end-to-end sales-funnel analyses, built the way a BI / operations analyst works: messy data → SQL → **formula-driven Excel reports** → dashboard → **findings with recommendations for management**.

| | Case study | Data | Deliverables |
|---|---|---|---|
| 1 | **Olist B2B sales funnel** | **Real data** from Kaggle: 8,000 leads, 842 closed deals | [Findings](reports/real_data_findings.md) · [Excel report](excel/Olist_Real_Funnel_Report.xlsx) · `sql/olist/` |
| 2 | **Residential solar funnel**: Lead → Appointment → Offer → Signed → Installed | Simulated CRM export (16k leads, 24 reps, 4 teams, marketing spend) | [Management summary](reports/management_summary.md) · [Excel KPI report](excel/Solar_Funnel_KPI_Report.xlsx) · `sql/` |

**Tools:** Excel (COUNTIFS, SUMIFS, AVERAGEIFS, INDEX/MATCH joins, array formulas, conditional formatting, charts) · SQL (SQLite: CTEs, window functions `RANK`/`LAG`/running totals, views) · Python (pandas, matplotlib) · Streamlit + Plotly · pytest · GitHub Actions

---

## Case study 1: real data, Olist marketing funnel

[Olist](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist), a Brazilian marketplace, recruits sellers: a seller fills in a sign-up form on a landing page (**marketing qualified lead**), and the sales team then tries to sign them (**closed deal**). 5,998 leads from 2018 → 781 sellers (**13.0%**), median **12 days** to close.

### Key findings
| | Finding | Action |
|---|---|---|
| 1 | **Social and email are 23% of leads but only 10% of deals** (6.3% and 4.0% conversion vs ~15% for search). | Lower priority in the sales queue; add a qualifying question to those forms |
| 2 | **Two landing pages convert at 22–23% vs ~10% for all others**, and the gap holds *within* the same channel (organic search 25% vs 10%), so it's the page, not the traffic. | A/B test routing organic traffic to the best page |
| 3 | **5 of 21 sales reps close 51% of deals**; the top rep closes 16%. | Key-person risk: document the top closers' approach, balance lead routing |
| 4 | **The best-converting source is "unknown"** (14.5% of leads, 21% conversion): a tracking gap. | Fix source tracking before moving marketing budget |

<p>
<img src="reports/figures/olist_02_channels.png" width="49%">
<img src="reports/figures/olist_03_pages_within_channel.png" width="49%">
</p>

### Handling real-data problems
- **Incomplete extract:** deals only exist from Dec 2017, so 2017 leads look like they never convert. Analysis is limited to 2018 leads. Without this check, the trend chart would wrongly suggest that "sales tripled".
- 1 deal is dated *before* its lead (excluded from timing). 95% of deals have revenue = 0, so no revenue analysis.
- The sales rep is only recorded on won deals, so per-rep **win rate** can't be calculated, only volume.
- Details: [`sql/olist/07_olist_data_quality.sql`](sql/olist/07_olist_data_quality.sql) and the *Data Quality* sheet.

### Excel report (`excel/Olist_Real_Funnel_Report.xlsx`)
The two raw Kaggle tables are pasted in unchanged, and **the join happens in Excel** (`MATCH` / `INDEX` on `mql_id`). Every number on the report sheets is a formula (48,000+): Monthly, Channels, Landing Pages, Page x Channel, Time to Close (incl. a `MEDIAN(IF())` array formula), Closers (Pareto), and Data Quality. The analysis window is an input on the Settings sheet.

---

## Case study 2: residential solar funnel (simulated)

A solar company generates ~200 leads a week from seven channels. Leads go through **Lead → Contacted → Appointment → Offer → Signed → Installed**, handled by four regional sales teams. 14,634 mature leads → **10.0%** signed, CAC €465.

### Key findings
| | Finding | Impact if fixed |
|---|---|---|
| 1 | **First call → appointment is the biggest leak** (37%). Leads called within 1 hour book **53%** appointments vs **25%** after 1–3 days, and 27% of leads wait more than a day. | ≈ +140 contracts |
| 2 | **Team West converts 5.6% vs 11.8%** for the other teams: slow calls, fewer offers, offers take 6.4 vs ~3 days, lower close rate. | ≈ +250 contracts |
| 3 | **Meta Ads: cheapest leads (€28) but costly contracts (€616 CAC)**. Referral (€166) and organic (€121) are most efficient. | Lower blended CAC |
| 4 | **Offers sent after 7+ days close at 22% vs 50%** within 3 days. | ≈ +80 contracts |

<p>
<img src="reports/figures/03_speed_to_lead.png" width="49%">
<img src="reports/figures/05_teams.png" width="49%">
</p>

### What the simulation adds
Real sales data with appointments, offers, call times and marketing spend is confidential, so this case study uses a **simulated CRM export** (`src/generate_data.py`, fixed seed). It is modelled on a German residential-solar business: regions, rental vs purchase, seasonality, lost reasons. It is deliberately messy: **195 duplicates, 17 spellings of 7 channel names, missing regions**. The generator builds in effects without labelling them, so the analysis has to find them.

**Excel KPI report (`excel/Solar_Funnel_KPI_Report.xlsx`):** 16,700+ formulas, a **Settings** sheet (cohort cut-off and report week drive every sheet), and a **Weekly Report** with week-over-week change and a 4-week rolling average, ready as a management update. The numbers reconcile exactly with the SQL.

**Cohort maturity:** recent leads haven't had time to sign, so conversion uses leads that are 8+ weeks old.

---

## Project structure

```
sales-funnel-analytics/
├── data/
│   ├── real_olist/          # REAL Kaggle data + SOURCE.md (license, re-download)
│   ├── raw/                 # simulated messy CRM export (solar)
│   └── processed/           # cleaned solar data
├── sql/
│   ├── olist/               # 7 queries on the real data + views
│   └── 00–09_*.sql          # 9 queries on the solar funnel + views
├── src/
│   ├── load_olist.py        # loads the real data (integrity checks)
│   ├── generate_data.py     # simulated solar CRM export
│   ├── clean_data.py        # de-duplication, label standardisation, derived columns
│   ├── load_to_sqlite.py    # builds data/funnel.db
│   ├── run_analysis.py      # runs all SQL → outputs/
│   ├── make_figures.py      # charts
│   ├── build_olist_excel.py # Excel report, real data
│   └── build_excel_report.py# Excel report, solar
├── excel/                   # the two Excel reports
├── dashboard/               # Streamlit app (app.py) + KPI logic (metrics.py)
├── reports/                 # findings, management summary, figures
├── outputs/                 # SQL results as CSV
├── tests/                   # data-quality + SQL-vs-Python reconciliation tests
└── run_all.py               # runs everything
```

## Run it yourself

```bash
git clone https://github.com/Karan6528/sales-funnel-analytics.git
cd sales-funnel-analytics
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_all.py                 # everything, ~25 s
pytest -q                         # 11 tests
streamlit run dashboard/app.py    # dashboard incl. a "Real data: Olist" tab
```

## Data and license
- **Olist data:** © Olist, [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), redistributed unchanged for non-commercial use. See [`data/real_olist/SOURCE.md`](data/real_olist/SOURCE.md).
- **Solar data:** simulated, generated by this project.
- **Code:** MIT (see `LICENSE`).

---

**Karan Lodha** · MSc Data Science, AI & Digital Business (Berlin) · [LinkedIn](https://www.linkedin.com/in/karanlodha/) · [GitHub](https://github.com/Karan6528)
