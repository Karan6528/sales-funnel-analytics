"""
Build the Excel KPI report: excel/Solar_Funnel_KPI_Report.xlsx

Every number on the report sheets is a live Excel formula (COUNTIFS, SUMIFS,
AVERAGEIFS, INDEX/MATCH, RANK) on the raw data sheets, so the workbook updates
when you paste in new data or change the inputs on the Settings sheet.

Usage:  python src/build_excel_report.py
"""

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "excel" / "Solar_Funnel_KPI_Report.xlsx"

# ---------------------------------------------------------------- styling --
FONT = "Arial"
NAVY = "0B2545"
TEAL = "13807A"
SUN = "F4B400"
LIGHT = "EEF3F8"
GREY = "6B7785"

F_TITLE = Font(name=FONT, size=18, bold=True, color=NAVY)
F_SUB = Font(name=FONT, size=10, italic=True, color=GREY)
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_BODY = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_INPUT = Font(name=FONT, size=10, color="0000FF", bold=True)
F_NOTE = Font(name=FONT, size=9, italic=True, color=GREY)
FILL_HEAD = PatternFill("solid", fgColor=NAVY)
FILL_LIGHT = PatternFill("solid", fgColor=LIGHT)
FILL_INPUT = PatternFill("solid", fgColor="FFF4C2")
THIN = Side(style="thin", color="D0D7DE")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

PCT = "0.0%"
EUR = '#,##0" €";-#,##0" €";"-"'
INT = "#,##0"
DATE = "yyyy-mm-dd"

CHANNELS = ["Google Ads", "Meta Ads", "Comparison Portal", "Website Organic",
            "Referral", "Partner Network", "Field Sales"]
TEAMS = ["Team East", "Team North", "Team South", "Team West"]
SPEED = ["Under 1h", "1-4h", "4-24h", "1-3 days", "Over 3 days"]
OFFER_SPEED = ["Up to 3 days", "4-7 days", "Over 7 days"]


def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = F_TITLE
    ws["A2"] = sub
    ws["A2"].font = F_SUB
    ws.sheet_view.showGridLines = False


def header(ws, row, labels, col=1):
    for i, label in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=label)
        c.font, c.fill, c.border = F_HEAD, FILL_HEAD, BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32


def body(cell, fmt=None, bold=False):
    cell.font = F_BOLD if bold else F_BODY
    cell.border = BOX
    if fmt:
        cell.number_format = fmt


def finish_chart(ch, labels=True):
    """Explicit settings so charts look the same in Excel and LibreOffice."""
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    if labels:
        ch.dataLabels = DataLabelList()
        ch.dataLabels.showVal = True
        ch.dataLabels.showSerName = False
        ch.dataLabels.showCatName = False
        ch.dataLabels.showLegendKey = False
        ch.dataLabels.showPercent = False
    return ch


def widths(ws, w):
    for i, width in enumerate(w, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width


# ------------------------------------------------------------ data sheets --
LEAD_COLS = [
    # (output header, source column)
    ("lead_id", "lead_id"), ("created_at", "created_at"), ("lead_week", "lead_week"),
    ("lead_month", "lead_month"), ("channel", "channel"), ("region", "region"),
    ("team", "team"), ("rep_id", "rep_id"), ("product_interest", "product_interest"),
    ("financing_type", "financing_type"), ("hours_to_contact", "hours_to_contact"),
    ("speed_bucket", "speed_to_lead_bucket"), ("days_appt_to_offer", "days_appt_to_offer"),
    ("offer_speed_bucket", "offer_speed_bucket"), ("is_contacted", None),
    ("is_appointment", None), ("is_offer", None), ("is_signed", None),
    ("is_installed", None), ("contract_value_eur", "contract_value_eur"),
    ("appointment_week", None), ("offer_week", None), ("signed_week", "signed_week"),
    ("status", "status"), ("lost_reason", "lost_reason"), ("is_mature", None),
]


def prepare_leads() -> pd.DataFrame:
    dates = ["created_at", "first_contact_at", "appointment_at", "offer_sent_at",
             "contract_signed_at", "installed_at", "lead_week", "signed_week"]
    df = pd.read_csv(PROCESSED / "leads_clean.csv", parse_dates=dates)
    week = lambda s: s.dt.to_period("W-SUN").dt.start_time
    df["is_contacted"] = df["first_contact_at"].notna().astype(int)
    df["is_appointment"] = df["appointment_at"].notna().astype(int)
    df["is_offer"] = df["offer_sent_at"].notna().astype(int)
    df["is_signed"] = df["contract_signed_at"].notna().astype(int)
    df["is_installed"] = df["installed_at"].notna().astype(int)
    df["appointment_week"] = week(df["appointment_at"])
    df["offer_week"] = week(df["offer_sent_at"])
    return df


def write_leads(wb, df):
    ws = wb.create_sheet("Leads")
    headers = [h for h, _ in LEAD_COLS]
    ws.append(headers)
    src_cols = [src if src else h for h, src in LEAD_COLS]
    n = len(df)
    mature_col = get_column_letter(headers.index("is_mature") + 1)
    for i, row in enumerate(df[[c for c in src_cols if c != "is_mature"]].itertuples(index=False), start=2):
        values = []
        for v in row:
            if pd.isna(v):
                values.append(None)
            elif isinstance(v, pd.Timestamp):
                values.append(v.to_pydatetime())
            else:
                values.append(v)
        # is_mature is a formula driven by the cohort cut-off on Settings
        values.append(f"=IF(B{i}<Settings!$C$5,1,0)")
        ws.append(values)

    for col_name, fmt in [("created_at", "yyyy-mm-dd hh:mm"), ("lead_week", DATE),
                          ("appointment_week", DATE), ("offer_week", DATE),
                          ("signed_week", DATE), ("contract_value_eur", EUR)]:
        col = get_column_letter(headers.index(col_name) + 1)
        for r in range(2, n + 2):
            ws[f"{col}{r}"].number_format = fmt
    for c in ws[1]:
        c.font, c.fill = F_HEAD, FILL_HEAD
    ws.freeze_panes = "A2"
    for i, h in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(12, len(h) + 2)
    ws.column_dimensions["B"].width = 17
    table = Table(displayName="tblLeads", ref=f"A1:{get_column_letter(len(headers))}{n + 1}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    ws.add_table(table)
    ws.sheet_properties.tabColor = GREY
    return {h: f"Leads!${get_column_letter(i)}$2:${get_column_letter(i)}${n + 1}"
            for i, h in enumerate(headers, start=1)}


def write_simple_sheet(wb, name, df, fmts=None, table_name=None):
    ws = wb.create_sheet(name)
    ws.append(list(df.columns))
    for row in df.itertuples(index=False):
        ws.append([v.to_pydatetime() if isinstance(v, pd.Timestamp) else v for v in row])
    for c in ws[1]:
        c.font, c.fill = F_HEAD, FILL_HEAD
    for col, fmt in (fmts or {}).items():
        letter = get_column_letter(list(df.columns).index(col) + 1)
        for r in range(2, len(df) + 2):
            ws[f"{letter}{r}"].number_format = fmt
    for i in range(1, len(df.columns) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 18
    ws.freeze_panes = "A2"
    if table_name:
        t = Table(displayName=table_name,
                  ref=f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}")
        t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        ws.add_table(t)
    ws.sheet_properties.tabColor = GREY
    n = len(df)
    return {c: f"'{name}'!${get_column_letter(i)}$2:${get_column_letter(i)}${n + 1}"
            if " " in name else f"{name}!${get_column_letter(i)}$2:${get_column_letter(i)}${n + 1}"
            for i, c in enumerate(df.columns, start=1)}


# ----------------------------------------------------------- report sheets --
def start_here(wb):
    ws = wb.active
    ws.title = "Start Here"
    title(ws, "Solar Sales Funnel – KPI Report",
          "Portfolio project by Karan Lodha · synthetic data modelled on a German residential-solar sales funnel")
    rows = [
        ("Sheet", "What it answers"),
        ("Settings", "Inputs: cohort cut-off date and report week. Change the yellow cells only."),
        ("Funnel", "How many leads reach each stage, and where do we lose the most?"),
        ("Channels", "Which marketing channels produce signed contracts, and at what cost (CAC)?"),
        ("Speed to Lead", "Does calling a new lead quickly increase appointments and contracts?"),
        ("Offer Speed", "Do customers sign less often when the offer arrives late?"),
        ("Teams", "Where in the funnel does each regional sales team win or lose?"),
        ("Reps", "Which reps close best once an offer is out? (min. 50 offers)"),
        ("Weekly Report", "Management view: last 12 weeks of leads, appointments, offers, contracts."),
        ("Leads / Reps List / Spend", "Raw data (cleaned CRM export). All report numbers are formulas on these."),
    ]
    for i, (a, b) in enumerate(rows, start=4):
        ws.cell(row=i, column=1, value=a)
        ws.cell(row=i, column=2, value=b)
        if i == 4:
            header(ws, 4, [a, b])
        else:
            body(ws.cell(row=i, column=1), bold=True)
            body(ws.cell(row=i, column=2))
    r = 4 + len(rows) + 1
    ws.cell(row=r, column=1, value="Legend").font = F_BOLD
    ws.cell(row=r + 1, column=1, value="Blue on yellow").font = F_INPUT
    ws.cell(row=r + 1, column=1).fill = FILL_INPUT
    ws.cell(row=r + 1, column=2, value="Input you can change (Settings sheet)").font = F_BODY
    ws.cell(row=r + 2, column=1, value="Black").font = F_BODY
    ws.cell(row=r + 2, column=2, value="Formula – do not overwrite").font = F_BODY
    ws.cell(row=r + 4, column=1,
            value="Conversion analysis uses the 'mature cohort' (leads created before the cut-off), "
                  "because recent leads have not had time to sign yet.").font = F_NOTE
    widths(ws, [26, 95])


def settings(wb, L):
    ws = wb.create_sheet("Settings")
    title(ws, "Settings", "Change the yellow input cells; every report sheet recalculates.")
    header(ws, 4, ["Setting", "", "Value", "Note"])
    ws.merge_cells("A4:B4")
    items = [
        (5, "Cohort cut-off (leads created before)", pd.Timestamp("2026-08-01").to_pydatetime(),
         DATE, "Leads newer than ~8 weeks are excluded from conversion rates."),
        (6, "Report week (Monday of latest week)", pd.Timestamp("2026-09-21").to_pydatetime(),
         DATE, "Weekly Report shows the 12 weeks ending with this week."),
        (7, "Min. offers for rep ranking", 50, INT, "Avoids ranking reps on tiny samples."),
    ]
    for r, label, value, fmt, note in items:
        ws.cell(row=r, column=1, value=label).font = F_BODY
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        c = ws.cell(row=r, column=3, value=value)
        c.font, c.fill, c.border, c.number_format = F_INPUT, FILL_INPUT, BOX, fmt
        ws.cell(row=r, column=4, value=note).font = F_NOTE
    ws.cell(row=9, column=1, value="Data range check").font = F_BOLD
    ws.cell(row=10, column=1, value="First lead").font = F_BODY
    ws.cell(row=10, column=3, value=f"=MIN({L['created_at']})").number_format = DATE
    ws.cell(row=11, column=1, value="Last lead").font = F_BODY
    ws.cell(row=11, column=3, value=f"=MAX({L['created_at']})").number_format = DATE
    ws.cell(row=12, column=1, value="Leads in mature cohort").font = F_BODY
    ws.cell(row=12, column=3, value=f"=SUM({L['is_mature']})").number_format = INT
    widths(ws, [30, 10, 16, 60])


def funnel(wb, L):
    ws = wb.create_sheet("Funnel")
    title(ws, "Sales Funnel – Mature Cohort",
          "Leads created before the cut-off on Settings · counts = leads that reached each stage")
    header(ws, 4, ["Stage", "Leads reaching stage", "Step conversion", "Overall conversion",
                   "Lost at this step"])
    stages = [("Lead", None), ("Contacted", "is_contacted"), ("Appointment", "is_appointment"),
              ("Offer", "is_offer"), ("Signed", "is_signed"), ("Installed", "is_installed")]
    for i, (stage, flag) in enumerate(stages):
        r = 5 + i
        ws.cell(row=r, column=1, value=stage)
        body(ws.cell(row=r, column=1), bold=True)
        if flag is None:
            f = f"=SUM({L['is_mature']})"
        else:
            f = f"=COUNTIFS({L[flag]},1,{L['is_mature']},1)"
        ws.cell(row=r, column=2, value=f)
        ws.cell(row=r, column=3, value="=1" if i == 0 else f"=IFERROR(B{r}/B{r - 1},0)")
        ws.cell(row=r, column=4, value=f"=IFERROR(B{r}/$B$5,0)")
        ws.cell(row=r, column=5, value=0 if i == 0 else f"=B{r - 1}-B{r}")
        body(ws.cell(row=r, column=2), INT)
        body(ws.cell(row=r, column=3), PCT)
        body(ws.cell(row=r, column=4), PCT)
        body(ws.cell(row=r, column=5), INT)
    ws.conditional_formatting.add(
        "E6:E10", DataBarRule(start_type="min", end_type="max", color="E57373"))

    ws["A12"] = "Biggest leak"
    ws["A12"].font = F_BOLD
    ws["B12"] = "=INDEX(A6:A10,MATCH(MAX(E6:E10),E6:E10,0))"
    ws["B12"].font = Font(name=FONT, size=12, bold=True, color="C62828")
    ws["C12"] = "=\"lost \"&TEXT(MAX(E6:E10),\"#,##0\")&\" leads at this step\""
    ws["C12"].font = F_BODY

    ch = BarChart()
    ch.type = "bar"
    ch.style = 10
    ch.title = "Leads reaching each stage"
    ch.y_axis.title = None
    ch.x_axis.scaling.orientation = "maxMin"
    ch.add_data(Reference(ws, min_col=2, min_row=4, max_row=10), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=10))
    ch.legend = None
    finish_chart(ch)
    ch.series[0].graphicalProperties.solidFill = TEAL
    ch.height, ch.width = 8, 16
    ws.add_chart(ch, "G4")
    widths(ws, [16, 18, 15, 16, 15])


def channels(wb, L, S):
    ws = wb.create_sheet("Channels")
    title(ws, "Channel Performance – Mature Cohort",
          "Spend counted for weeks before the cut-off · CAC = spend / signed contracts")
    cols = ["Channel", "Leads", "Appointments", "Signed", "Lead → Appt", "Lead → Signed",
            "Spend", "Cost per lead", "Cost per signed (CAC)", "Signed value",
            "Revenue per € spent"]
    header(ws, 4, cols)
    m = L["is_mature"]
    for i, ch_name in enumerate(CHANNELS):
        r = 5 + i
        ws.cell(row=r, column=1, value=ch_name)
        body(ws.cell(row=r, column=1), bold=True)
        f = {
            2: f"=COUNTIFS({L['channel']},$A{r},{m},1)",
            3: f"=COUNTIFS({L['channel']},$A{r},{m},1,{L['is_appointment']},1)",
            4: f"=COUNTIFS({L['channel']},$A{r},{m},1,{L['is_signed']},1)",
            5: f"=IFERROR(C{r}/B{r},0)",
            6: f"=IFERROR(D{r}/B{r},0)",
            7: f"=SUMIFS({S['spend_eur']},{S['channel']},$A{r},{S['week_start']},\"<\"&Settings!$C$5)",
            8: f"=IFERROR(G{r}/B{r},0)",
            9: f"=IFERROR(G{r}/D{r},0)",
            10: f"=SUMIFS({L['contract_value_eur']},{L['channel']},$A{r},{m},1,{L['is_signed']},1)",
            11: f"=IFERROR(J{r}/G{r},0)",
        }
        fmts = {2: INT, 3: INT, 4: INT, 5: PCT, 6: PCT, 7: EUR, 8: EUR, 9: EUR, 10: EUR, 11: '0.0"x"'}
        for c, formula in f.items():
            ws.cell(row=r, column=c, value=formula)
            body(ws.cell(row=r, column=c), fmts[c])
    tr = 5 + len(CHANNELS)
    ws.cell(row=tr, column=1, value="Total")
    body(ws.cell(row=tr, column=1), bold=True)
    for c, fmt in [(2, INT), (3, INT), (4, INT), (7, EUR), (10, EUR)]:
        L_ = get_column_letter(c)
        ws.cell(row=tr, column=c, value=f"=SUM({L_}5:{L_}{tr - 1})")
        body(ws.cell(row=tr, column=c), fmt, bold=True)
    for c, f, fmt in [(5, f"=IFERROR(C{tr}/B{tr},0)", PCT), (6, f"=IFERROR(D{tr}/B{tr},0)", PCT),
                      (8, f"=IFERROR(G{tr}/B{tr},0)", EUR), (9, f"=IFERROR(G{tr}/D{tr},0)", EUR),
                      (11, f"=IFERROR(J{tr}/G{tr},0)", '0.0"x"')]:
        ws.cell(row=tr, column=c, value=f)
        body(ws.cell(row=tr, column=c), fmt, bold=True)
    for c in range(1, 12):
        ws.cell(row=tr, column=c).fill = FILL_LIGHT

    last = tr - 1
    ws.conditional_formatting.add(f"I5:I{last}", ColorScaleRule(
        start_type="min", start_color="63BE7B", mid_type="percentile", mid_value=50,
        mid_color="FFEB84", end_type="max", end_color="F8696B"))
    ws.conditional_formatting.add(f"F5:F{last}", ColorScaleRule(
        start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50,
        mid_color="FFEB84", end_type="max", end_color="63BE7B"))
    ws.cell(row=tr + 2, column=1,
            value="Read: Meta Ads has the cheapest leads but one of the highest costs per "
                  "contract, because few of its leads sign. Judge channels on CAC, not CPL."
            ).font = F_NOTE

    ch = BarChart()
    ch.type = "bar"
    ch.style = 10
    ch.title = "Cost per signed contract (CAC) by channel"
    ch.add_data(Reference(ws, min_col=9, min_row=4, max_row=last), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=last))
    ch.legend = None
    finish_chart(ch)
    ch.series[0].graphicalProperties.solidFill = SUN
    ch.height, ch.width = 9, 18
    ws.add_chart(ch, f"A{tr + 4}")
    widths(ws, [20, 10, 13, 10, 12, 13, 13, 12, 14, 15, 13])


def speed_to_lead(wb, L):
    ws = wb.create_sheet("Speed to Lead")
    title(ws, "Speed to Lead", "Contacted leads in the mature cohort, by hours until first call")
    header(ws, 4, ["Time to first contact", "Contacted leads", "Share", "Appointment rate",
                   "Signed rate", "Avg hours"])
    m = L["is_mature"]
    for i, b in enumerate(SPEED):
        r = 5 + i
        ws.cell(row=r, column=1, value=b)
        body(ws.cell(row=r, column=1), bold=True)
        f = {
            2: f"=COUNTIFS({L['speed_bucket']},$A{r},{m},1)",
            3: f"=IFERROR(B{r}/SUM($B$5:$B$9),0)",
            4: f"=IFERROR(COUNTIFS({L['speed_bucket']},$A{r},{m},1,{L['is_appointment']},1)/B{r},0)",
            5: f"=IFERROR(COUNTIFS({L['speed_bucket']},$A{r},{m},1,{L['is_signed']},1)/B{r},0)",
            6: f"=IFERROR(AVERAGEIFS({L['hours_to_contact']},{L['speed_bucket']},$A{r},{m},1),0)",
        }
        fmts = {2: INT, 3: PCT, 4: PCT, 5: PCT, 6: "0.0"}
        for c, formula in f.items():
            ws.cell(row=r, column=c, value=formula)
            body(ws.cell(row=r, column=c), fmts[c])
    ws["A11"] = "Uplift: < 1h vs 1-3 days (appointment rate)"
    ws["A11"].font = F_BOLD
    ws["D11"] = "=IFERROR(D5/D8,0)"
    ws["D11"].number_format = '0.0"x"'
    ws["D11"].font = Font(name=FONT, size=12, bold=True, color=TEAL)

    ch = BarChart()
    ch.style = 10
    ch.title = "Appointment rate by time to first contact"
    ch.add_data(Reference(ws, min_col=4, min_row=4, max_row=9), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=9))
    ch.legend = None
    ch.y_axis.number_format = "0%"
    finish_chart(ch)
    ch.series[0].graphicalProperties.solidFill = TEAL
    ch.height, ch.width = 8, 16
    ws.add_chart(ch, "H4")
    widths(ws, [24, 15, 10, 16, 12, 11])


def offer_speed(wb, L):
    ws = wb.create_sheet("Offer Speed")
    title(ws, "Offer Speed", "Offers in the mature cohort, by days from appointment to offer")
    header(ws, 4, ["Appointment → offer", "Offers", "Share", "Signed", "Offer → signed"])
    m = L["is_mature"]
    for i, b in enumerate(OFFER_SPEED):
        r = 5 + i
        ws.cell(row=r, column=1, value=b)
        body(ws.cell(row=r, column=1), bold=True)
        f = {
            2: f"=COUNTIFS({L['offer_speed_bucket']},$A{r},{m},1)",
            3: f"=IFERROR(B{r}/SUM($B$5:$B$7),0)",
            4: f"=COUNTIFS({L['offer_speed_bucket']},$A{r},{m},1,{L['is_signed']},1)",
            5: f"=IFERROR(D{r}/B{r},0)",
        }
        fmts = {2: INT, 3: PCT, 4: INT, 5: PCT}
        for c, formula in f.items():
            ws.cell(row=r, column=c, value=formula)
            body(ws.cell(row=r, column=c), fmts[c])
    ch = BarChart()
    ch.style = 10
    ch.title = "Offer → signed rate by offer speed"
    ch.add_data(Reference(ws, min_col=5, min_row=4, max_row=7), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=7))
    ch.legend = None
    ch.y_axis.number_format = "0%"
    finish_chart(ch)
    ch.series[0].graphicalProperties.solidFill = NAVY
    ch.height, ch.width = 8, 14
    ws.add_chart(ch, "G4")
    widths(ws, [22, 10, 10, 10, 15])


def teams(wb, L):
    ws = wb.create_sheet("Teams")
    title(ws, "Team Performance – Mature Cohort", "Where in the funnel each regional team wins or loses")
    cols = ["Team", "Leads", "Called < 4h", "Avg hours to call", "Contact → Appt",
            "Appt → Offer", "Avg days to offer", "Offer → Signed", "Signed", "Lead → Signed"]
    header(ws, 4, cols)
    m = L["is_mature"]
    for i, t in enumerate(TEAMS):
        r = 5 + i
        ws.cell(row=r, column=1, value=t)
        body(ws.cell(row=r, column=1), bold=True)
        T = f"{L['team']},$A{r},{m},1"
        f = {
            2: f"=COUNTIFS({T})",
            3: f"=IFERROR(COUNTIFS({T},{L['hours_to_contact']},\"<4\")/COUNTIFS({T},{L['is_contacted']},1),0)",
            4: f"=IFERROR(AVERAGEIFS({L['hours_to_contact']},{L['team']},$A{r},{m},1),0)",
            5: f"=IFERROR(COUNTIFS({T},{L['is_appointment']},1)/COUNTIFS({T},{L['is_contacted']},1),0)",
            6: f"=IFERROR(COUNTIFS({T},{L['is_offer']},1)/COUNTIFS({T},{L['is_appointment']},1),0)",
            7: f"=IFERROR(AVERAGEIFS({L['days_appt_to_offer']},{L['team']},$A{r},{m},1),0)",
            8: f"=IFERROR(COUNTIFS({T},{L['is_signed']},1)/COUNTIFS({T},{L['is_offer']},1),0)",
            9: f"=COUNTIFS({T},{L['is_signed']},1)",
            10: f"=IFERROR(I{r}/B{r},0)",
        }
        fmts = {2: INT, 3: PCT, 4: "0.0", 5: PCT, 6: PCT, 7: "0.0", 8: PCT, 9: INT, 10: PCT}
        for c, formula in f.items():
            ws.cell(row=r, column=c, value=formula)
            body(ws.cell(row=r, column=c), fmts[c])
    for col in ["C", "E", "F", "H", "J"]:
        ws.conditional_formatting.add(f"{col}5:{col}8", ColorScaleRule(
            start_type="min", start_color="F8696B", end_type="max", end_color="63BE7B"))
    for col in ["D", "G"]:
        ws.conditional_formatting.add(f"{col}5:{col}8", ColorScaleRule(
            start_type="min", start_color="63BE7B", end_type="max", end_color="F8696B"))
    ws["A10"] = ("Green = better, red = worse within each column. Look for the team whose "
                 "column is red at several stages.")
    ws["A10"].font = F_NOTE

    ch = BarChart()
    ch.style = 10
    ch.title = "Lead → signed by team"
    ch.add_data(Reference(ws, min_col=10, min_row=4, max_row=8), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=8))
    ch.legend = None
    ch.y_axis.number_format = "0%"
    finish_chart(ch)
    ch.series[0].graphicalProperties.solidFill = NAVY
    ch.height, ch.width = 8, 14
    ws.add_chart(ch, "A12")
    widths(ws, [14, 9, 12, 13, 14, 12, 13, 14, 9, 13])


def reps(wb, L, R, rep_ids):
    ws = wb.create_sheet("Reps")
    title(ws, "Rep Leaderboard – Mature Cohort",
          "Closing rate = offers that became signed contracts · ranked only with enough offers")
    cols = ["Rep ID", "Name", "Team", "Leads", "Offers", "Signed", "Offer → Signed",
            "Rank", "vs team avg (pp)", "Signed value"]
    header(ws, 4, cols)
    m = L["is_mature"]
    first, last = 5, 5 + len(rep_ids) - 1
    for i, rid in enumerate(rep_ids):
        r = 5 + i
        ws.cell(row=r, column=1, value=rid)
        body(ws.cell(row=r, column=1), bold=True)
        f = {
            2: f"=INDEX({R['rep_name']},MATCH($A{r},{R['rep_id']},0))",
            3: f"=INDEX({R['team']},MATCH($A{r},{R['rep_id']},0))",
            4: f"=COUNTIFS({L['rep_id']},$A{r},{m},1)",
            5: f"=COUNTIFS({L['rep_id']},$A{r},{m},1,{L['is_offer']},1)",
            6: f"=COUNTIFS({L['rep_id']},$A{r},{m},1,{L['is_signed']},1)",
            7: f"=IFERROR(F{r}/E{r},0)",
            8: f"=IF(E{r}>=Settings!$C$7,COUNTIFS($E${first}:$E${last},\">=\"&Settings!$C$7,"
               f"$G${first}:$G${last},\">\"&G{r})+1,\"n/a\")",
            9: f"=(G{r}-AVERAGEIFS($G${first}:$G${last},$C${first}:$C${last},C{r}))*100",
            10: f"=SUMIFS({L['contract_value_eur']},{L['rep_id']},$A{r},{m},1,{L['is_signed']},1)",
        }
        fmts = {2: None, 3: None, 4: INT, 5: INT, 6: INT, 7: PCT, 8: "0", 9: '+0.0;-0.0;0.0', 10: EUR}
        for c, formula in f.items():
            ws.cell(row=r, column=c, value=formula)
            body(ws.cell(row=r, column=c), fmts[c])
    ws.conditional_formatting.add(f"G{first}:G{last}", DataBarRule(
        start_type="num", start_value=0, end_type="max", color="5B9BD5"))
    ws.conditional_formatting.add(f"I{first}:I{last}", ColorScaleRule(
        start_type="min", start_color="F8696B", mid_type="num", mid_value=0,
        mid_color="FFFFFF", end_type="max", end_color="63BE7B"))
    ws.cell(row=last + 2, column=1,
            value="Tip: sort by the Rank column (Data → Sort) to see the leaderboard. "
                  "Rank uses COUNTIFS so ties share a rank.").font = F_NOTE
    ws.freeze_panes = "B5"
    widths(ws, [9, 20, 13, 9, 9, 9, 14, 8, 15, 15])


def weekly(wb, L):
    ws = wb.create_sheet("Weekly Report")
    title(ws, "Weekly Management Report",
          "Events in the week they happened · 12 weeks ending with the report week on Settings")
    cols = ["Week starting", "New leads", "Appointments", "Offers sent", "Contracts signed",
            "Signed value", "Signed WoW", "Signed 4-wk avg", "Appt rate*"]
    header(ws, 4, cols)
    for i in range(12):
        r = 5 + i
        ws.cell(row=r, column=1, value=f"=Settings!$C$6-7*{11 - i}")
        f = {
            2: f"=COUNTIFS({L['lead_week']},$A{r})",
            3: f"=COUNTIFS({L['appointment_week']},$A{r})",
            4: f"=COUNTIFS({L['offer_week']},$A{r})",
            5: f"=COUNTIFS({L['signed_week']},$A{r})",
            6: f"=SUMIFS({L['contract_value_eur']},{L['signed_week']},$A{r})",
            7: "" if i == 0 else f"=IFERROR(E{r}/E{r - 1}-1,0)",
            8: f"=AVERAGE(E{max(5, r - 3)}:E{r})",
            9: f"=IFERROR(C{r}/B{r},0)",
        }
        fmts = {2: INT, 3: INT, 4: INT, 5: INT, 6: EUR, 7: '+0.0%;-0.0%;0.0%', 8: "0.0", 9: PCT}
        body(ws.cell(row=r, column=1), DATE, bold=True)
        for c, formula in f.items():
            ws.cell(row=r, column=c, value=formula if formula else None)
            body(ws.cell(row=r, column=c), fmts[c])
    tr = 17
    ws.cell(row=tr, column=1, value="12-week total")
    body(ws.cell(row=tr, column=1), bold=True)
    for c, fmt in [(2, INT), (3, INT), (4, INT), (5, INT), (6, EUR)]:
        col = get_column_letter(c)
        ws.cell(row=tr, column=c, value=f"=SUM({col}5:{col}16)")
        body(ws.cell(row=tr, column=c), fmt, bold=True)
    for c in range(1, 10):
        ws.cell(row=tr, column=c).fill = FILL_LIGHT
    ws["A19"] = "Latest week vs 12-week average"
    ws["A19"].font = F_BOLD
    for c, label in [(2, "New leads"), (5, "Contracts")]:
        col = get_column_letter(c)
        ws.cell(row=20, column=c, value=label).font = F_BODY
        cell = ws.cell(row=21, column=c, value=f"=IFERROR({col}16/AVERAGE({col}5:{col}16)-1,0)")
        cell.number_format = '+0.0%;-0.0%;0.0%'
        cell.font = Font(name=FONT, size=12, bold=True, color=TEAL)
    ws["A23"] = ("* Appt rate = appointments held this week / new leads this week "
                 "(a quick health check, not a cohort conversion).")
    ws["A23"].font = F_NOTE
    ws.conditional_formatting.add("G6:G16", ColorScaleRule(
        start_type="min", start_color="F8696B", mid_type="num", mid_value=0,
        mid_color="FFFFFF", end_type="max", end_color="63BE7B"))

    lc = LineChart()
    lc.title = "Contracts signed per week"
    lc.style = 12
    lc.add_data(Reference(ws, min_col=5, min_row=4, max_row=16), titles_from_data=True)
    lc.add_data(Reference(ws, min_col=8, min_row=4, max_row=16), titles_from_data=True)
    lc.set_categories(Reference(ws, min_col=1, min_row=5, max_row=16))
    lc.x_axis.number_format = "dd mmm"
    lc.series[0].graphicalProperties.line.solidFill = TEAL
    lc.series[0].graphicalProperties.line.width = 28000
    lc.series[1].graphicalProperties.line.solidFill = SUN
    lc.series[1].graphicalProperties.line.dashStyle = "dash"
    for s in lc.series:
        s.smooth = False
    finish_chart(lc, labels=False)
    lc.height, lc.width = 8, 18
    ws.add_chart(lc, "K4")

    bc = LineChart()
    bc.title = "New leads and appointments per week"
    bc.style = 12
    bc.add_data(Reference(ws, min_col=2, min_row=4, max_row=16), titles_from_data=True)
    bc.add_data(Reference(ws, min_col=3, min_row=4, max_row=16), titles_from_data=True)
    bc.set_categories(Reference(ws, min_col=1, min_row=5, max_row=16))
    bc.x_axis.number_format = "dd mmm"
    bc.series[0].graphicalProperties.line.solidFill = NAVY
    bc.series[1].graphicalProperties.line.solidFill = TEAL
    for s in bc.series:
        s.smooth = False
    finish_chart(bc, labels=False)
    bc.height, bc.width = 8, 18
    ws.add_chart(bc, "K21")
    widths(ws, [15, 11, 13, 11, 15, 14, 12, 14, 11])


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    leads = prepare_leads()
    reps_df = pd.read_csv(PROCESSED / "sales_reps.csv")
    spend = pd.read_csv(PROCESSED / "marketing_spend.csv", parse_dates=["week_start"])

    wb = Workbook()
    start_here(wb)
    # Report sheets are created first (tab order), data sheets after.
    placeholders = ["Settings", "Funnel", "Channels", "Speed to Lead", "Offer Speed",
                    "Teams", "Reps", "Weekly Report"]
    L = write_leads(wb, leads)
    R = write_simple_sheet(wb, "Reps List", reps_df, table_name="tblReps")
    S = write_simple_sheet(wb, "Spend", spend, fmts={"week_start": DATE, "spend_eur": EUR},
                           table_name="tblSpend")

    settings(wb, L)
    funnel(wb, L)
    channels(wb, L, S)
    speed_to_lead(wb, L)
    offer_speed(wb, L)
    teams(wb, L)
    reps(wb, L, R, list(reps_df["rep_id"]))
    weekly(wb, L)

    # Put report tabs before data tabs
    order = ["Start Here"] + placeholders + ["Leads", "Reps List", "Spend"]
    wb._sheets = [wb[name] for name in order]
    wb.active = 0
    for ws in wb.worksheets:
        if ws.title in placeholders:
            ws.sheet_properties.tabColor = TEAL
    wb["Start Here"].sheet_properties.tabColor = SUN

    wb.calculation.fullCalcOnLoad = True   # Excel computes every formula on open
    wb.save(OUT)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
