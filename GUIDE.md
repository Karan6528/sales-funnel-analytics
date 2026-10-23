# Guide: run it in VS Code, publish on GitHub, and prepare for the interview

This file is for you (Karan). Delete it before publishing, or keep it as a "how to run" file.

---

## Part 1 – Open and run in VS Code (≈15 min)

**Install once:** [Python 3.11+](https://www.python.org/downloads/) (Windows: tick *"Add Python to PATH"*), [VS Code](https://code.visualstudio.com/), [Git](https://git-scm.com/downloads).

1. Unzip `sales-funnel-analytics.zip`, e.g. to `Documents/projects/`.
2. VS Code → **File → Open Folder…** → select `sales-funnel-analytics`.
   VS Code will suggest the recommended extensions (Python, SQLite Viewer, SQLTools, Rainbow CSV). Click **Install**.
3. Open a terminal: **Terminal → New Terminal**, then run:

   ```bash
   python -m venv .venv
   # Mac/Linux:
   source .venv/bin/activate
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   (Mac: use `python3` if `python` is not found. Windows: if activation is blocked, run
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.)
4. Select the interpreter: `Ctrl/Cmd + Shift + P` → **Python: Select Interpreter** → pick `.venv`.
5. Run everything:
   ```bash
   python run_all.py
   pytest -q
   streamlit run dashboard/app.py
   ```
   The dashboard opens at http://localhost:8501. Stop it with `Ctrl + C`.
6. **Explore the SQL in VS Code:** open any file in `sql/`, then use SQLTools (database icon in the sidebar → connection *funnel.db*) and run the query.
   Or click `data/funnel.db` to browse tables with SQLite Viewer.

## Part 2 – Publish on GitHub (≈10 min)

1. On github.com → **New repository** → name `sales-funnel-analytics`, **Public**, *don't* add a README → **Create**.
2. In the VS Code terminal (inside the project folder):
   ```bash
   git init
   git add .
   git commit -m "Sales funnel analytics: real Olist data + solar funnel, SQL, Excel, dashboard"
   git branch -M main
   git remote add origin https://github.com/Karan6528/sales-funnel-analytics.git
   git push -u origin main
   ```
3. On the repo page: click ⚙️ next to **About** → add a description
   (*"End-to-end sales funnel analysis: SQL, Excel KPI report, Streamlit dashboard"*) and topics:
   `sql`, `excel`, `data-analysis`, `sales-analytics`, `streamlit`, `business-intelligence`.
4. Go to the **Actions** tab. The pipeline runs automatically, and when it turns green the badge in the README turns green too.
5. **Pin it:** your GitHub profile → *Customize your pins* → select this repo first.
6. Optional, recommended: deploy the dashboard for free on [share.streamlit.io](https://share.streamlit.io)
   (sign in with GitHub → New app → this repo → main file `dashboard/app.py`).
   The app builds `data/funnel.db` itself from the committed CSVs on first start.
   Put the live link at the top of the README and on your CV.

## Part 3 – Make it yours before the interview (most important)

Interviewers will ask about the Excel work, because Excel is the main tool in this job. Do these yourself in Excel.

**Real data (`Olist_Real_Funnel_Report.xlsx`):**

1. Look at the teal columns on the `MQLs` sheet. Click F2, G2 and H2 and make sure you can explain how MATCH finds the deal row and INDEX pulls the won date. This is a SQL `LEFT JOIN` done in Excel, which makes a great interview answer.
2. **Pivot table** on `Deals`: Rows = `business_segment`, Values = Count of `mql_id`. Which segments bring the most sellers?
3. Change the analysis window on **Settings** to `2018-03-01` and watch every sheet update.

**Solar report (`Solar_Funnel_KPI_Report.xlsx`):**


4. **Pivot table:** on the `Leads` sheet → Insert → PivotTable. Rows = `channel`, Columns = `team`, Values = Count of `lead_id` and Average of `is_signed` (formatted as %, this is the conversion rate). Add a **slicer** for `lead_month`.
5. **XLOOKUP:** in `Reps`, replace the INDEX/MATCH in column B with
   `=XLOOKUP(A5,'Reps List'!A:A,'Reps List'!B:B)`. (The file uses INDEX/MATCH because it works in every Excel version.)
6. **Change Settings:** set the report week to `2026-08-31` and watch the Weekly Report update.
7. **One new analysis:** e.g. conversion by `financing_type` (Rental vs Purchase) with COUNTIFS. Add it as a new sheet. It's your own contribution, and you can talk about it.

Also re-read `sql/olist/04_olist_page_within_channel.sql`, `sql/04_team_performance.sql` and `sql/06_weekly_kpis.sql` until you can explain every line.

## Part 4 – CV and interview

**CV project entry (put it first under Projects):**

> **Sales Funnel Analytics** (SQL, Excel, Python, Streamlit) · github.com/Karan6528/sales-funnel-analytics
> - Analysed a real B2B sales funnel (Olist, Kaggle: 8,000 leads, 842 deals) in SQL and Excel; found that two landing pages convert at 2× the rest within the same channel, and that 5 of 21 reps close 51% of deals
> - Built formula-driven Excel reports (COUNTIFS/SUMIFS, INDEX/MATCH joins, weekly management view, 60k+ formulas) that reconcile exactly with the SQL results
> - Modelled a 6-stage solar sales funnel (16k leads); identified slow follow-up as the main leak (53% vs 25% appointment rate) and sized the fix at ≈140–250 contracts

**60-second pitch:**
"I built a sales funnel project in two parts. First, real data from Olist on Kaggle: 8,000 leads and 842 closed deals. I joined the tables, checked the data quality first (the deals file only starts in December 2017, so earlier leads would have looked like a failure), and found that two landing pages convert at twice the rate of the others, even within the same channel. So the page itself is worth an A/B test. Second, because real data on call times and offers is confidential, I modelled a solar funnel like Enpal's from lead to installation and built a weekly Excel report for management. There, the biggest leak was between the first call and the appointment: leads called within an hour book twice as many appointments."

**Questions to prepare for:**
- *Why is the solar data simulated?* Real data with call times, appointments and offers is confidential, so I used real data (Olist) where it exists and a simulation for the operational part. The simulation has effects built in without labels, so the analysis had to find them. The same SQL and Excel would run on a real CRM export.
- *What was the hardest part of the real data?* Noticing that the deals file starts in Dec 2017. Without that check, the trend would show sales "tripling" in 2018, which is a false headline.
- *Why is "unknown" the best channel?* Probably leads whose source wasn't tracked, e.g. direct sign-ups by already-interested sellers. That's a tracking issue to fix before moving budget.
- *What is cohort maturity and why did you exclude recent leads?* Recent leads haven't had time to sign, so including them would understate conversion.
- *Is Team West's problem the leads or the team?* Same channel mix, but it's behind at the steps it controls (call speed, offers, offer speed). Next step would be to check per-rep and per-region data.
- *Correlation vs causation on speed to lead?* It could partly be selection (hot leads get called first). The right test is an A/B test: route some leads to an instant-call queue.
- *How would you automate the weekly report?* Connect Excel to the database via Power Query (or Power BI) and refresh. The formulas already update when the data changes.

**Questions to ask them:** Which funnel KPIs does management look at weekly? Which tools does the team use besides Excel (SQL, Looker, Power BI)? What does a typical ad-hoc request look like?
