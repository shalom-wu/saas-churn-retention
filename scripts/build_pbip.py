"""Generate the Power BI project (PBIP) for the churn dashboard.

Emits power-bi/saas_churn_retention.pbip + .SemanticModel (model.bim, TMSL)
+ .Report (report.json). Open the .pbip in Power BI Desktop, Refresh, and
Save As -> .pbix. All tables load from data/powerbi/ via the DataFolder
parameter; every measure is documented in power-bi/dax_measures.md.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = ROOT / "power-bi"
NAME = "saas_churn_retention"
DATA_FOLDER = str((ROOT / "data" / "powerbi").resolve())

DARK, TEAL, RED, AMBER = "#26343F", "#1F7A8C", "#D64550", "#F4A259"
PCT, NUM, USD, F1 = "0.0%", "#,0", "$#,0", "0.0"

# ===========================================================================
# semantic model (TMSL)
# ===========================================================================


def m_csv(filename, types):
    tlist = ", ".join(f'{{"{c}", {t}}}' for c, t in types)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "\\{filename}"),'
        '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    Typed = Table.TransformColumnTypes(Promoted, {{{tlist}}})",
        "in",
        "    Typed",
    ]


def col(name, dtype, fmt=None):
    c = {"name": name, "dataType": dtype, "sourceColumn": name,
         "summarizeBy": "none"}
    if fmt:
        c["formatString"] = fmt
    return c


def measure(name, expression, fmt=None):
    m = {"name": name, "expression": expression}
    if fmt:
        m["formatString"] = fmt
    return m


def table(name, m_lines, columns, measures=None):
    t = {"name": name, "columns": columns,
         "partitions": [{"name": name, "mode": "import",
                         "source": {"type": "m", "expression": m_lines}}]}
    if measures:
        t["measures"] = measures
    return t


fact_cols = [
    col("customerID", "string"), col("gender", "string"),
    col("SeniorCitizen", "string"), col("Partner", "string"),
    col("Dependents", "string"), col("tenure", "int64", NUM),
    col("tenure_band", "string"), col("Contract", "string"),
    col("PaymentMethod", "string"), col("InternetService", "string"),
    col("n_addon_services", "int64", "0"),
    col("MonthlyCharges", "double", USD), col("charge_tier", "string"),
    col("TotalCharges", "double", USD), col("Churn", "string"),
    col("churn_flag", "int64", "0"),
]
fact_measures = [
    measure("Customers", "COUNTROWS ( fact_customers )", NUM),
    measure("Churned Customers",
            "CALCULATE ( [Customers], fact_customers[churn_flag] = 1 )", NUM),
    measure("Churn Rate", "DIVIDE ( [Churned Customers], [Customers] )", PCT),
    measure("MRR", "SUM ( fact_customers[MonthlyCharges] )", USD),
    measure("MRR Lost to Churn",
            "CALCULATE ( [MRR], fact_customers[churn_flag] = 1 )", USD),
    measure("MRR Lost %", "DIVIDE ( [MRR Lost to Churn], [MRR] )", PCT),
    measure("Avg Monthly Charge", "AVERAGE ( fact_customers[MonthlyCharges] )", "$#,0.00"),
    measure("Avg Tenure (months)", "AVERAGE ( fact_customers[tenure] )", F1),
    measure("Share of Customers",
            "DIVIDE ( [Customers], CALCULATE ( [Customers], ALLSELECTED ( fact_customers ) ) )", PCT),
]

ltv_cols = [
    col("Contract", "string"), col("customers", "int64", NUM),
    col("avg_monthly_revenue", "double", USD),
    col("monthly_churn_hazard", "double", "0.00%"),
    col("expected_lifetime_months", "double", F1),
    col("avg_ltv", "double", USD), col("cost_per_churn", "double", USD),
]
ltv_measures = [
    measure("Avg Customer LTV", "AVERAGE ( ltv_by_contract[avg_ltv] )", USD),
    measure("Avg Cost per Churn", "AVERAGE ( ltv_by_contract[cost_per_churn] )", USD),
]

seg_cols = [
    col("segment", "string"), col("customers", "int64", NUM),
    col("churn_rate", "double", PCT), col("mrr", "double", USD),
    col("mrr_lost_to_churn", "double", USD),
]

cost_cols = [
    col("churned_customers", "int64", NUM), col("lost_mrr", "double", USD),
    col("annualized_lost_revenue", "double", USD),
    col("foregone_ltv", "double", USD),
    col("replacement_cac_total", "double", USD),
    col("total_cost_of_churn", "double", USD),
    col("avg_cost_per_churned_customer", "double", USD),
]
cost_measures = [
    measure("Cost of Churned Cohort",
            "MAX ( kpi_cost_of_churn[total_cost_of_churn] )", '$#,##0.0,, "M"'),
    measure("Annualized Lost Revenue",
            "MAX ( kpi_cost_of_churn[annualized_lost_revenue] )", '$#,##0.0,, "M"'),
]

int_cols = [
    col("option", "string"), col("name", "string"), col("what", "string"),
    col("year1_net_pv", "int64", USD), col("roi_multiple", "double", "0.0x"),
    col("key_risk", "string"), col("confidence", "string"),
]

addon_cols = [
    col("n_addon_services", "int64", "0"), col("customers", "int64", NUM),
    col("churn_rate", "double", PCT),
]

model = {
    "name": "SemanticModel",
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "expressions": [{
            "name": "DataFolder", "kind": "m",
            "expression": [f'"{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'],
            "annotations": [{"name": "PBI_ResultType", "value": "Text"}],
        }],
        "tables": [
            table("fact_customers", m_csv("fact_customers.csv", [
                ("customerID", "type text"), ("gender", "type text"),
                ("SeniorCitizen", "type text"), ("Partner", "type text"),
                ("Dependents", "type text"), ("tenure", "Int64.Type"),
                ("tenure_band", "type text"), ("Contract", "type text"),
                ("PaymentMethod", "type text"), ("InternetService", "type text"),
                ("n_addon_services", "Int64.Type"),
                ("MonthlyCharges", "type number"), ("charge_tier", "type text"),
                ("TotalCharges", "type number"), ("Churn", "type text"),
                ("churn_flag", "Int64.Type")]), fact_cols, fact_measures),
            table("ltv_by_contract", m_csv("ltv_by_contract.csv", [
                ("Contract", "type text"), ("customers", "Int64.Type"),
                ("avg_monthly_revenue", "type number"),
                ("monthly_churn_hazard", "type number"),
                ("expected_lifetime_months", "type number"),
                ("avg_ltv", "type number"),
                ("cost_per_churn", "type number")]), ltv_cols, ltv_measures),
            table("at_risk_segments", m_csv("at_risk_segments.csv", [
                ("segment", "type text"), ("customers", "Int64.Type"),
                ("churn_rate", "type number"), ("mrr", "type number"),
                ("mrr_lost_to_churn", "type number")]), seg_cols),
            table("kpi_cost_of_churn", m_csv("kpi_cost_of_churn.csv", [
                ("churned_customers", "Int64.Type"), ("lost_mrr", "type number"),
                ("annualized_lost_revenue", "type number"),
                ("foregone_ltv", "type number"),
                ("replacement_cac_total", "type number"),
                ("total_cost_of_churn", "type number"),
                ("avg_cost_per_churned_customer", "type number")]),
                cost_cols, cost_measures),
            table("kpi_churn_by_addons", m_csv("kpi_churn_by_addons.csv", [
                ("n_addon_services", "Int64.Type"), ("customers", "Int64.Type"),
                ("churn_rate", "type number")]), addon_cols),
            table("dim_interventions", m_csv("dim_interventions.csv", [
                ("option", "type text"), ("name", "type text"),
                ("what", "type text"), ("year1_net_pv", "Int64.Type"),
                ("roi_multiple", "type number"), ("key_risk", "type text"),
                ("confidence", "type text")]), int_cols),
        ],
        "relationships": [{
            "name": "fact_to_ltv", "fromTable": "fact_customers",
            "fromColumn": "Contract", "toTable": "ltv_by_contract",
            "toColumn": "Contract",
        }],
        "annotations": [{"name": "__PBI_TimeIntelligenceEnabled", "value": "0"}],
    },
}

# ===========================================================================
# report (classic report.json) — helpers mirror the P7/P8 projects
# ===========================================================================
_counter = [0]


def uid():
    _counter[0] += 1
    return f"vc{_counter[0]:04d}"


def lit(v):
    if isinstance(v, bool):
        return {"expr": {"Literal": {"Value": "true" if v else "false"}}}
    if isinstance(v, (int, float)):
        return {"expr": {"Literal": {"Value": f"{v}D"}}}
    return {"expr": {"Literal": {"Value": f"'{v}'"}}}


def src(entity, alias):
    return {"Name": alias, "Entity": entity, "Type": 0}


def col_expr(alias, prop):
    return {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}


def meas_expr(alias, prop):
    return {"Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}


def select_col(entity, alias, prop):
    return {**col_expr(alias, prop), "Name": f"{entity}.{prop}", "NativeReferenceName": prop}


def select_meas(entity, alias, prop):
    return {**meas_expr(alias, prop), "Name": f"{entity}.{prop}", "NativeReferenceName": prop}


def title_obj(text, size=11):
    return {"title": [{"properties": {"show": lit(True), "text": lit(text),
                                      "fontColor": {"solid": {"color": lit(DARK)}},
                                      "fontSize": lit(size)}}]}


def background(color):
    return {"background": [{"properties": {"show": lit(True),
                                           "color": {"solid": {"color": lit(color)}},
                                           "transparency": lit(0)}}]}


def data_color(color):
    return {"dataPoint": [{"properties": {"defaultColor": {"solid": {"color": lit(color)}}}}]}


def visual(vtype, x, y, w, h, z, projections, froms, selects, order_by=None,
           objects=None, vc_objects=None):
    sv = {"visualType": vtype, "projections": projections,
          "prototypeQuery": {"Version": 2, "From": froms, "Select": selects,
                             **({"OrderBy": order_by} if order_by else {})},
          "drillFilterOtherVisuals": True}
    if objects:
        sv["objects"] = objects
    if vc_objects:
        sv["vcObjects"] = vc_objects
    cfg = {"name": uid(),
           "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                                              "width": w, "height": h}}],
           "singleVisual": sv}
    return {"x": x, "y": y, "z": z, "width": w, "height": h,
            "config": json.dumps(cfg)}


def textbox(x, y, w, h, z, runs, bg=None):
    paragraphs = []
    for line in runs:
        paragraphs.append({"textRuns": [
            {"value": text, "textStyle": style} for text, style in line]})
    sv = {"visualType": "textbox",
          "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
          "drillFilterOtherVisuals": True}
    if bg:
        sv["vcObjects"] = background(bg)
    cfg = {"name": uid(),
           "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                                              "width": w, "height": h}}],
           "singleVisual": sv}
    return {"x": x, "y": y, "z": z, "width": w, "height": h,
            "config": json.dumps(cfg)}


def header(title_text, subtitle):
    return [
        textbox(0, 0, 1280, 68, 0,
                [[(title_text, {"fontSize": "20pt", "fontWeight": "bold", "color": "#FFFFFF"})],
                 [(subtitle, {"fontSize": "10pt", "color": "#9FB3BE"})]], bg=DARK),
        textbox(0, 696, 1280, 24, 0,
                [[("Source: IBM Telco Customer Churn sample dataset (via Kaggle) · reframed as a subscription business · "
                   "LTV and intervention figures use documented assumptions (src/config.py)",
                   {"fontSize": "8pt", "color": "#8896A0"})]]),
    ]


def card(entity, m, x, y, w=196, h=92, z=100):
    a = entity[0]
    return visual("card", x, y, w, h, z,
                  {"Values": [{"queryRef": f"{entity}.{m}"}]},
                  [src(entity, a)], [select_meas(entity, a, m)],
                  vc_objects=title_obj(m))


def slicer(entity, column, x, y, w=170, h=90, z=100, title=None):
    a = entity[0]
    return visual("slicer", x, y, w, h, z,
                  {"Values": [{"queryRef": f"{entity}.{column}"}]},
                  [src(entity, a)], [select_col(entity, a, column)],
                  objects={"data": [{"properties": {"mode": lit("Dropdown")}}]},
                  vc_objects=title_obj(title or column))


def bar(cat_entity, cat, m_entity, m, x, y, w, h, z, title,
        vtype="clusteredBarChart", color=TEAL, sort_desc=True):
    froms, aliases = [], {}
    for e in dict.fromkeys([cat_entity, m_entity]):
        aliases[e] = f"t{len(froms)}"
        froms.append(src(e, aliases[e]))
    selects = [select_col(cat_entity, aliases[cat_entity], cat),
               select_meas(m_entity, aliases[m_entity], m)]
    order = ([{"Direction": 2, "Expression": meas_expr(aliases[m_entity], m)}]
             if sort_desc else
             [{"Direction": 1, "Expression": col_expr(aliases[cat_entity], cat)}])
    return visual(vtype, x, y, w, h, z,
                  {"Category": [{"queryRef": f"{cat_entity}.{cat}", "active": True}],
                   "Y": [{"queryRef": f"{m_entity}.{m}"}]},
                  froms, selects, order_by=order,
                  objects=data_color(color), vc_objects=title_obj(title))


def table_vis(fields, x, y, w, h, z, title, order_by=None):
    froms, aliases = [], {}
    for _, e, _ in fields:
        if e not in aliases:
            aliases[e] = f"t{len(froms)}"
            froms.append(src(e, aliases[e]))
    selects, refs = [], []
    for kind, e, nm in fields:
        selects.append(select_col(e, aliases[e], nm) if kind == "col"
                       else select_meas(e, aliases[e], nm))
        refs.append({"queryRef": f"{e}.{nm}"})
    return visual("tableEx", x, y, w, h, z, {"Values": refs}, froms, selects,
                  order_by=order_by, vc_objects=title_obj(title))


F = "fact_customers"

# --- page 1: executive overview -------------------------------------------
p1 = header("SaaS Customer Churn — Retention Overview",
            "Executive view · 7,043 customers · IBM Telco sample reframed as a subscription business")
for i, m in enumerate(["Customers", "Churn Rate", "MRR", "MRR Lost to Churn"]):
    p1.append(card(F, m, 16 + i * 208, 84, z=10 + i))
p1.append(card("kpi_cost_of_churn", "Cost of Churned Cohort", 848, 84, w=200, z=14))
p1.append(slicer(F, "Contract", 1076, 84, 188, 92, 15))
p1.append(bar(F, "Contract", F, "Churn Rate", 16, 200, 500, 260, 20,
              "Churn rate by contract type — the fault line", color=RED))
p1.append(bar(F, "tenure_band", F, "Churn Rate", 540, 200, 500, 260, 21,
              "Churn by tenure — risk is front-loaded", sort_desc=False))
p1.append(textbox(16, 480, 1248, 200, 30, [
    [("What this says", {"fontSize": "12pt", "fontWeight": "bold", "color": DARK})],
    [("26.5% of the book churned, taking 31% of MRR with it — churners skew premium ($74 vs $61/month). "
      "The problem concentrates where contracts are loose and tenure is short: month-to-month customers churn at 43% "
      "vs 3% on two-year deals, and over half of first-half-year customers leave. Priced with the LTV model "
      "(70% margin, $400 replacement CAC, 10% discount — all documented assumptions), the churned cohort cost ~$4.5M. "
      "Pages 2-3 break down where it leaks and what to do about it.",
      {"fontSize": "11pt", "color": "#41505B"})]], bg="#FDF6EC"))

# --- page 2: diagnostics ----------------------------------------------------
p2 = header("Churn Diagnostics",
            "Where churn concentrates: payment method, price tier, add-on depth")
p2.append(bar(F, "PaymentMethod", F, "Churn Rate", 16, 84, 610, 280, 10,
              "Churn by payment method — the electronic-check red flag", color=RED))
p2.append(bar(F, "charge_tier", F, "Churn Rate", 650, 84, 400, 280, 11,
              "Churn by monthly-charge tier", sort_desc=False, color=AMBER))
p2.append(slicer(F, "InternetService", 1076, 84, 188, 92, 12))
p2.append(slicer(F, "SeniorCitizen", 1076, 190, 188, 92, 13))
p2.append(bar("kpi_churn_by_addons", "n_addon_services", F, "Churn Rate",
              16, 390, 610, 280, 20,
              "Churn by add-on count (internet customers) — add-ons anchor",
              vtype="clusteredColumnChart", sort_desc=False))
p2.append(bar(F, "InternetService", F, "Churn Rate", 650, 390, 400, 280, 21,
              "Churn by internet service — fiber's price/value problem"))
p2.append(textbox(1076, 390, 188, 280, 22, [
    [("Reading tip", {"fontSize": "10pt", "fontWeight": "bold", "color": DARK})],
    [("Rates are cohort shares of the snapshot, not monthly rates. "
      "The add-on chart uses the SQL aggregate (internet customers only).",
      {"fontSize": "9pt", "color": "#41505B"})]], bg="#F2F6F8"))

# --- page 3: value & action -------------------------------------------------
p3 = header("Customer Value & Retention Actions",
            "What a lost customer costs, who is at risk, and the three costed interventions")
p3.append(bar("ltv_by_contract", "Contract", "ltv_by_contract", "Avg Customer LTV",
              16, 84, 490, 250, 10, "Discounted LTV by contract (src/ltv.py)"))
p3.append(bar("ltv_by_contract", "Contract", "ltv_by_contract", "Avg Cost per Churn",
              16, 350, 490, 250, 11, "All-in cost of losing one customer (LTV + $400 CAC)",
              color=RED))
p3.append(table_vis([("col", "at_risk_segments", "segment"),
                     ("col", "at_risk_segments", "customers"),
                     ("col", "at_risk_segments", "churn_rate"),
                     ("col", "at_risk_segments", "mrr"),
                     ("col", "at_risk_segments", "mrr_lost_to_churn")],
                    530, 84, 734, 220, 20, "At-risk segments (overlapping, targetable)"))
p3.append(table_vis([("col", "dim_interventions", "option"),
                     ("col", "dim_interventions", "name"),
                     ("col", "dim_interventions", "year1_net_pv"),
                     ("col", "dim_interventions", "roi_multiple"),
                     ("col", "dim_interventions", "confidence"),
                     ("col", "dim_interventions", "key_risk")],
                    530, 320, 734, 200, 21,
                    "Interventions — year-1 net PV under conservative, documented assumptions"))
p3.append(textbox(530, 536, 734, 148, 30, [
    [("Recommendation", {"fontSize": "11pt", "fontWeight": "bold", "color": DARK})],
    [("Run A + B together (one campaign: contract-shift offers, prioritized by model score); pilot C as a 500-customer "
      "A/B test. Expected year-1 net impact ~$0.4M against a $4.5M/year problem. These are decision-support estimates "
      "with stated take-up and save-rate assumptions — not guaranteed outcomes.",
      {"fontSize": "10pt", "color": "#41505B"})]], bg="#FDF6EC"))

report = {
    "config": json.dumps({"version": "5.43", "themeCollection": {}}),
    "layoutOptimization": 0,
    "sections": [
        {"name": "page1", "displayName": "Retention Overview", "displayOption": 1,
         "width": 1280, "height": 720, "config": "{}", "visualContainers": p1, "ordinal": 0},
        {"name": "page2", "displayName": "Churn Diagnostics", "displayOption": 1,
         "width": 1280, "height": 720, "config": "{}", "visualContainers": p2, "ordinal": 1},
        {"name": "page3", "displayName": "Value & Action", "displayOption": 1,
         "width": 1280, "height": 720, "config": "{}", "visualContainers": p3, "ordinal": 2},
    ],
}


def write_project():
    sm = PBI_DIR / f"{NAME}.SemanticModel"
    rp = PBI_DIR / f"{NAME}.Report"
    sm.mkdir(parents=True, exist_ok=True)
    rp.mkdir(parents=True, exist_ok=True)
    (PBI_DIR / f"{NAME}.pbip").write_text(json.dumps({
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}}, indent=2))
    (sm / "definition.pbism").write_text(json.dumps({"version": "1.0", "settings": {}}, indent=2))
    (sm / "model.bim").write_text(json.dumps(model, indent=2))
    (sm / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": "31111111-1111-1111-1111-111111111111"}}, indent=2))
    (rp / "definition.pbir").write_text(json.dumps({
        "version": "1.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
    (rp / "report.json").write_text(json.dumps(report, indent=2))
    (rp / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": "32222222-2222-2222-2222-222222222222"}}, indent=2))
    print(f"PBIP written to {PBI_DIR} "
          f"({sum(len(s['visualContainers']) for s in report['sections'])} visuals)")


if __name__ == "__main__":
    write_project()
