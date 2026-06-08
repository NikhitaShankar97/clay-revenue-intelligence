
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Clay Revenue Intelligence",
    page_icon="🧱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Public Streamlit deployment version.
# This uses Streamlit secrets instead of Snowflake's internal get_active_session().
# Add credentials in Streamlit Community Cloud under App settings → Secrets.
DB_NAME = "CLAY_REVENUE_INTELLIGENCE"
MART_SCHEMA = "DBT_NSHANKAR"
MART_PREFIX = f"{DB_NAME}.{MART_SCHEMA}"


@st.cache_data(ttl=600, show_spinner=False)
def run_query(query: str) -> pd.DataFrame:
    conn = st.connection("snowflake")
    return conn.query(query, ttl=600)

def money(value):
    if value is None or pd.isna(value):
        return "$0"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value/1_000:.0f}K"
    return f"${value:,.0f}"

def safe_divide(a, b):
    if a is None or b is None or pd.isna(a) or pd.isna(b) or b == 0:
        return None
    return a / b

def format_multiplier(value):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value}x"

def multiplier_sentence(value):
    if value is None or pd.isna(value):
        return "not enough data for a reliable multiplier"
    return f"{value}x more pipeline"

def section_label(text):
    st.markdown(f'<div class="section-lbl">{text}</div>', unsafe_allow_html=True)

def purpose_card(title, text):
    st.markdown(
        f'''
        <div class="purpose-card">
          <div class="purpose-title">{title}</div>
          <div class="purpose-text">{text}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

def business_table(df: pd.DataFrame, money_cols=None, bool_cols=None):
    if df is None or df.empty:
        return df

    money_cols = money_cols or []
    bool_cols = bool_cols or []

    out = df.copy()
    out.columns = [c.replace("_", " ").title() for c in out.columns]

    for col in money_cols:
        nice_col = col.replace("_", " ").title()
        if nice_col in out.columns:
            out[nice_col] = out[nice_col].apply(money)

    for col in bool_cols:
        nice_col = col.replace("_", " ").title()
        if nice_col in out.columns:
            out[nice_col] = out[nice_col].apply(lambda x: "Yes" if x == 1 or x is True else "No")

    return out

def html_bar_chart(
    df,
    label_col,
    value_col,
    title,
    subtitle,
    color="#E8632A",
    decimal_places=0,
    max_rows=None,
    **kwargs
):
    """Render a safe HTML bar chart.

    Supports older calls that pass max_rows or format strings like 'number'/'money'.
    Handles nulls, zeroes, Decimal values, strings, and empty data safely.
    """
    import html

    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">{html.escape(str(title))}</div>
          <div class="card-sub">{html.escape(str(subtitle))}</div>
        """,
        unsafe_allow_html=True
    )

    if df is None or df.empty or value_col not in df.columns or label_col not in df.columns:
        st.markdown(
            "<div class='card-sub'>No data available for the selected filters.</div></div>",
            unsafe_allow_html=True
        )
        return

    chart_df = df[[label_col, value_col]].copy()
    chart_df[value_col] = pd.to_numeric(chart_df[value_col], errors="coerce").fillna(0)

    # Limit rows if requested by existing chart calls.
    if max_rows is not None:
        try:
            max_rows_int = int(max_rows)
            if max_rows_int > 0:
                chart_df = chart_df.head(max_rows_int)
        except Exception:
            pass

    try:
        max_value = float(chart_df[value_col].max())
    except Exception:
        max_value = 0.0

    if pd.isna(max_value) or max_value <= 0:
        st.markdown(
            "<div class='card-sub'>No positive values available for this chart.</div></div>",
            unsafe_allow_html=True
        )
        return

    format_mode = None
    if isinstance(decimal_places, str):
        format_mode = decimal_places.lower().strip()
        decimal_places_num = 0 if format_mode in {"money", "currency", "number", "integer", "count"} else 2
    else:
        try:
            decimal_places_num = int(decimal_places)
        except Exception:
            decimal_places_num = 0

    for _, row in chart_df.iterrows():
        label = html.escape(str(row[label_col]))

        try:
            value = float(row[value_col])
        except Exception:
            value = 0.0

        if pd.isna(value) or value < 0:
            value = 0.0

        width = max(4, min(100, (value / max_value) * 100))

        if format_mode in {"money", "currency"}:
            display_value = money(value)
        elif format_mode in {"number", "integer", "count"}:
            display_value = f"{value:,.0f}"
        else:
            display_value = f"{value:,.{decimal_places_num}f}"

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin:12px 0;">
              <div style="width:180px; font-size:13px;">{label}</div>
              <div style="flex:1; background:#EEEAE4; border-radius:999px; height:10px;">
                <div style="width:{width}%; background:{color}; height:10px; border-radius:999px;"></div>
              </div>
              <div style="width:90px; text-align:right; font-size:13px;">{display_value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


def signal_card(title, hypothesis, action, severity="P1", color="#E8632A"):
    st.markdown(
        f"""
        <div class="signal">
          <div class="signal-title">
            {title}
            <span class="pill" style="background:#FDF0E8;color:{color};border-color:#F4C4A0;">{severity}</span>
          </div>
          <div class="signal-desc">
            <strong>Hypothesis:</strong> {hypothesis}<br/>
            <strong>Recommended action:</strong> {action}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def why_how_card(title, likely_driver, evidence, action, impact, confidence, color="#E8632A"):
    st.markdown(
        f"""
        <div class="why-card" style="border-left-color:{color};">
          <div class="card-title">{title}</div>
          <div class="why-grid">
            <div><span class="why-label">Likely driver</span><br>{likely_driver}</div>
            <div><span class="why-label">How we know</span><br>{evidence}</div>
            <div><span class="why-label">Recommended action</span><br>{action}</div>
            <div><span class="why-label">Expected impact</span><br>{impact}</div>
            <div><span class="why-label">Confidence</span><br>{confidence}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Cortex LLM calls are intentionally not used in this trial-safe version.
# The AI Analyst tab uses a grounded fallback based on Snowflake/dbt metrics.

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Geist', sans-serif; }
.stApp { background: #F5F2ED; color: #1A1916; }
.block-container { padding-top: 0.8rem; padding-left: 1.8rem; padding-right: 1.8rem; max-width: 1500px; }
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
[data-testid="stMetric"] { background: #FDFCFA; border: 1px solid #E2DDD6; border-radius: 13px; padding: 16px 18px; box-shadow: none; }
[data-testid="stMetricLabel"] { color: #7A756E; font-family: 'Geist Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stMetricValue"] { color: #1A1916; font-weight: 300; letter-spacing: -1.2px; }
.topbar { background: #FDFCFA; border: 1px solid #E2DDD6; border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.brand { display: flex; align-items: center; gap: 10px; }
.brand-mark { width: 30px; height: 30px; background: #E8632A; border-radius: 8px; display: flex; align-items: center; justify-content: center; color:white; font-weight:700; }
.brand-name { font-size: 16px; font-weight: 600; letter-spacing: -0.3px; }
.brand-sub { font-size: 13px; color: #7A756E; border-left: 1px solid #D4CFC7; padding-left: 10px; }
.live-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 500; color: #3D7A1C; background: #EBF4E3; border: 1px solid #C5E0AA; padding: 5px 10px; border-radius: 999px; font-family: 'Geist Mono', monospace; }
.data-badge { display: inline-flex; font-size: 11px; color: #7A756E; background: #F0EDE8; border: 1px solid #E2DDD6; padding: 5px 10px; border-radius: 999px; font-family: 'Geist Mono', monospace; margin-right: 8px; }
.live-dot { width: 6px; height: 6px; border-radius: 999px; background: #3D7A1C; }
.section-lbl { font-size: 10px; font-weight: 600; letter-spacing: 1px; color: #B5B0A8; text-transform: uppercase; font-family: 'Geist Mono', monospace; margin-top: 8px; margin-bottom: 12px; }
.card { background: #FDFCFA; border: 1px solid #E2DDD6; border-radius: 13px; padding: 18px 20px; margin-bottom: 14px; }
.card-title { font-size: 15px; font-weight: 600; letter-spacing: -0.2px; color: #1A1916; margin-bottom: 4px; }
.card-sub { font-size: 12px; color: #7A756E; margin-bottom: 14px; }
.filter-card { background: #FDFCFA; border: 1px solid #E2DDD6; border-radius: 13px; padding: 12px 16px 4px 16px; margin: 14px 0; }
.finding-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.finding { border-radius: 11px; padding: 14px 16px; border: 1px solid; font-size: 13px; line-height: 1.55; }
.finding .label { font-size: 10px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; font-family: 'Geist Mono', monospace; margin-bottom: 6px; }
.pill { font-size: 10px; font-weight: 600; padding: 3px 8px; border-radius: 999px; border: 1px solid; font-family: 'Geist Mono', monospace; display: inline-flex; align-items: center; gap: 3px; margin-left: 6px; }
.signal { background: #FDFCFA; border: 1px solid #E2DDD6; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
.signal-title { font-size: 14px; font-weight: 600; color: #1A1916; margin-bottom: 4px; }
.signal-desc { font-size: 12px; color: #7A756E; line-height: 1.55; }
.small-note { font-size: 12px; color: #7A756E; line-height: 1.55; }
.bar-chart { display: flex; flex-direction: column; gap: 11px; }
.bar-row { display: flex; align-items: center; gap: 12px; }
.bar-label { width: 175px; flex-shrink: 0; font-size: 12px; color: #2C2A27; font-family: 'Geist Mono', monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { flex: 1; height: 9px; background: #F0EDE8; border-radius: 999px; overflow: hidden; border: 1px solid #E2DDD6; }
.bar-fill { height: 100%; border-radius: 999px; }
.bar-value { width: 90px; flex-shrink: 0; text-align: right; font-size: 12px; color: #1A1916; font-family: 'Geist Mono', monospace; }
.why-card { background: #FDFCFA; border: 1px solid #E2DDD6; border-left: 5px solid #E8632A; border-radius: 13px; padding: 18px 20px; margin-bottom: 14px; }
.why-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; font-size: 13px; color:#2C2A27; line-height:1.55; margin-top:10px; }
.why-label { font-size:10px; text-transform:uppercase; letter-spacing:.8px; color:#B5B0A8; font-family:'Geist Mono',monospace; font-weight:600; }
.stTabs [data-baseweb="tab-list"] { gap: 22px; border-bottom: 1px solid #E2DDD6; padding-left: 2px; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px 8px 0 0; color: #7A756E; font-weight: 500; padding: 13px 2px 12px 2px; margin-right: 8px; white-space: nowrap; }
.stTabs [data-baseweb="tab"] p { font-size: 15px; }
.stTabs [aria-selected="true"] { color: #E8632A !important; border-bottom: 3px solid #E8632A; }
.stDataFrame { border: 1px solid #E2DDD6; border-radius: 12px; overflow: hidden; }

.purpose-card {
    background: #FDFCFA;
    border: 1px solid #E2DDD6;
    border-radius: 13px;
    padding: 14px 18px;
    margin-bottom: 14px;
}

.purpose-title {
    font-size: 14px;
    font-weight: 600;
    color: #1A1916;
    margin-bottom: 5px;
}

.purpose-text {
    font-size: 12px;
    color: #7A756E;
    line-height: 1.55;
}

.workbench-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap: 10px;
    margin-bottom: 12px;
}

.workbench-mini {
    background: #FDFCFA;
    border: 1px solid #E2DDD6;
    border-radius: 11px;
    padding: 12px 14px;
    font-size: 12px;
    color: #2C2A27;
    line-height: 1.45;
}

.workbench-mini span {
    display: block;
    font-family: 'Geist Mono', monospace;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: #B5B0A8;
    font-size: 9px;
    font-weight: 600;
    margin-bottom: 4px;
}



/* Public Streamlit Cloud header spacing fix */
.block-container {
    padding-top: 1.25rem !important;
}

/* Keep Clay header visible below the Streamlit Cloud toolbar */
.clay-top-header, .app-header, .hero, .top-card {
    margin-top: 0rem !important;
}

/* Make selected multiselect/filter pills Clay orange */
[data-testid="stMultiSelect"] [data-baseweb="tag"],
.stMultiSelect [data-baseweb="tag"],
div[data-baseweb="select"] [data-baseweb="tag"],
span[data-baseweb="tag"] {
    background-color: #E8632A !important;
    border-color: #E8632A !important;
    color: #FFFFFF !important;
}

[data-testid="stMultiSelect"] [data-baseweb="tag"] *,
.stMultiSelect [data-baseweb="tag"] *,
div[data-baseweb="select"] [data-baseweb="tag"] *,
span[data-baseweb="tag"] * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

/* Risk helper note */
.risk-helper {
    margin-top: -0.45rem;
    margin-bottom: 1.1rem;
    color: #6E6963;
    font-size: 0.86rem;
    line-height: 1.35;
}

/* Compact risk band helper below the Risk Band filter */
.risk-mini-guide {
    margin-top: -0.35rem;
    display: flex;
    gap: 0.55rem;
    flex-wrap: wrap;
    color: #6E6963;
    font-size: 0.78rem;
    font-style: italic;
    line-height: 1.25;
}
.risk-mini-guide span {
    white-space: nowrap;
}


/* Compact filters and forecast controls */
[data-testid="stMultiSelect"] {
    margin-bottom: 0.25rem !important;
}

[data-testid="stSlider"] {
    padding-top: 0.15rem !important;
    padding-bottom: 0.15rem !important;
    margin-bottom: -0.4rem !important;
}

/* Best-effort Clay orange slider accent */
[data-testid="stSlider"] [role="slider"] {
    background-color: #E8632A !important;
    border-color: #E8632A !important;
}

[data-testid="stSlider"] [data-baseweb="slider"] div {
    accent-color: #E8632A !important;
}

.forecast-control-card {
    background: #FDFCFA;
    border: 1px solid #E2DDD6;
    border-radius: 13px;
    padding: 14px 18px 4px 18px;
    margin-bottom: 14px;
}

.forecast-control-title {
    font-size: 14px;
    font-weight: 600;
    color: #1A1916;
    margin-bottom: 2px;
}

.forecast-control-sub {
    font-size: 12px;
    color: #7A756E;
    margin-bottom: 8px;
}


/* Compact label rows so help icons sit beside the label instead of far right */
.compact-label {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.98rem;
    color: #31333F;
    margin-bottom: -0.35rem;
    line-height: 1.2;
}
.help-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px;
    height: 15px;
    border: 1.4px solid #858A93;
    border-radius: 50%;
    color: #858A93;
    font-size: 10px;
    font-weight: 700;
    cursor: help;
}
.help-dot:hover {
    border-color: #E8632A;
    color: #E8632A;
}

</style>
""", unsafe_allow_html=True)


base = run_query(f"SELECT * FROM {MART_PREFIX}.CHURN_RISK_SCORES")
activation = run_query(f"SELECT * FROM {MART_PREFIX}.ACTIVATION_VELOCITY")
global_signals = run_query(f"SELECT * FROM {MART_PREFIX}.SIGNAL_FEED")

st.markdown("""
<div class="topbar">
  <div class="brand"><div class="brand-mark">C</div><span class="brand-name">Clay</span><span class="brand-sub">Revenue Intelligence</span></div>
  <div><span class="data-badge">Snowflake · dbt marts · synthetic data</span><span class="live-badge"><span class="live-dot"></span>Live</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="small-note">Dynamic analytics app using public Clay product concepts and synthetic data. All KPIs, diagnostics, risk scores, and recommendations recalculate from dbt-built Snowflake models and respond to filters.</div>', unsafe_allow_html=True)

st.markdown('<div class="filter-card"><div class="card-title">Segment Filters</div><div class="card-sub">Use these filters to analyze GTM health by plan, industry, and risk band.</div></div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)
with f1:
    plan_options = sorted(base["PLAN_TIER"].dropna().unique())
    selected_plans = st.multiselect("Plan Tier", plan_options, default=plan_options)
with f2:
    industry_options = sorted(base["INDUSTRY"].dropna().unique())
    selected_industries = st.multiselect("Industry", industry_options, default=industry_options)
with f3:
    risk_options = sorted(base["RISK_BAND"].dropna().astype(str).unique())
    st.markdown(
        """
        <div class="compact-label">
            <span>Risk Band</span>
            <span class="help-dot" title="Risk Band is a customer-health label based on churn-risk signals such as usage depth, pipeline efficiency, support friction, credit usage, and product adoption.">?</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    selected_risk = st.multiselect(
        "Risk Band",
        risk_options,
        default=risk_options,
        label_visibility="collapsed"
    )
    st.markdown(
        """
        <div class="risk-mini-guide">
            <span><b>HIGH</b> · CS attention</span>
            <span><b>MEDIUM</b> · monitor</span>
            <span><b>LOW</b> · healthier</span>
        </div>
        """,
        unsafe_allow_html=True
    )

filtered = base[
    (base["PLAN_TIER"].isin(selected_plans))
    & (base["INDUSTRY"].isin(selected_industries))
    & (base["RISK_BAND"].astype(str).isin(selected_risk))
].copy()

filtered_ids = filtered["CUSTOMER_ID"].unique().tolist()
if filtered.empty:
    st.warning(
        "The selected filter combination has no matching accounts. Try adding more plan tiers, industries, or risk bands to broaden the segment."
    )

activation_filtered = activation[activation["CUSTOMER_ID"].isin(filtered_ids)].copy()

def compute_activation_multiplier(act_df):
    if act_df.empty:
        return None, 0, 0
    activated_series = act_df[act_df["WORKFLOWS_FIRST_14D"] >= 3]["PIPELINE_GENERATED"]
    not_activated_series = act_df[act_df["WORKFLOWS_FIRST_14D"] < 3]["PIPELINE_GENERATED"]
    if activated_series.empty or not_activated_series.empty:
        return None, activated_series.mean() if not activated_series.empty else 0, not_activated_series.mean() if not not_activated_series.empty else 0
    activated = activated_series.mean()
    not_activated = not_activated_series.mean()
    ratio = safe_divide(activated, not_activated)
    return round(ratio, 2) if ratio is not None else None, activated, not_activated

def compute_claygent_multiplier(act_df):
    if act_df.empty:
        return None, 0, 0
    adopted_series = act_df[act_df["CLAYGENT_ADOPTED"] == 1]["PIPELINE_GENERATED"]
    not_adopted_series = act_df[act_df["CLAYGENT_ADOPTED"] == 0]["PIPELINE_GENERATED"]
    if adopted_series.empty or not_adopted_series.empty:
        return None, adopted_series.mean() if not adopted_series.empty else 0, not_adopted_series.mean() if not not_adopted_series.empty else 0
    adopted = adopted_series.mean()
    not_adopted = not_adopted_series.mean()
    ratio = safe_divide(adopted, not_adopted)
    return round(ratio, 2) if ratio is not None else None, adopted, not_adopted

activation_multiplier, activated_pipeline, not_activated_pipeline = compute_activation_multiplier(activation_filtered)
claygent_multiplier, claygent_pipeline, no_claygent_pipeline = compute_claygent_multiplier(activation_filtered)

expansion_candidates = filtered[
    (filtered["PLAN_TIER"].isin(["Starter", "Explorer", "Pro"]))
    & (filtered["EXPANSION_SCORE"] >= 70)
].copy()

high_risk = filtered[filtered["RISK_BAND"].astype(str) == "HIGH"].copy()

current_mrr = filtered["ARR"].sum() / 12 if len(filtered) else 0
expansion_arr_opportunity = expansion_candidates.apply(lambda r: max(48000 - r["ARR"], 0) if r["PLAN_TIER"] != "Enterprise" else 0, axis=1).sum() if len(expansion_candidates) else 0
churn_arr_at_risk = high_risk["ARR"].sum() if len(high_risk) else 0
avg_pipeline_per_credit = filtered["PIPELINE_PER_CREDIT"].mean() if len(filtered) else 0
avg_workflows = filtered["WORKFLOW_RUNS"].mean() if len(filtered) else 0
avg_support_tickets = filtered["SUPPORT_TICKETS"].mean() if len(filtered) else 0
claygent_adoption_rate = filtered["CLAYGENT_USED"].mean() if len(filtered) else 0

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Overview", "Why & How", "Activation", "Expansion", "Churn Risk", "Forecast", "Signal Feed", "Analytics Workbench", "AI Analyst"
])

with tab1:
    purpose_card("Executive overview", "Shows the selected segment’s GTM health: activation lift, Claygent lift, expansion upside, and ARR at risk. Use this as the leadership summary.")
    section_label("Executive summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Activation Multiplier", format_multiplier(activation_multiplier), "filtered segment", help="Compares average pipeline for customers with 3+ workflows in their first 14 days vs customers below that threshold.")
    c2.metric("Claygent Lift", format_multiplier(claygent_multiplier), "filtered segment", help="Compares average pipeline for Claygent adopters vs non-adopters in the selected segment.")
    c3.metric("Expansion ARR", money(expansion_arr_opportunity), f"{len(expansion_candidates)} accounts", help="Estimated ARR uplift if high-fit non-enterprise accounts move toward an Enterprise-like plan.")
    c4.metric("ARR at Risk", money(churn_arr_at_risk), f"{len(high_risk)} accounts", help="Current ARR tied to accounts classified as high churn risk.")

    if activation_multiplier is None or claygent_multiplier is None:
        st.warning("One or more multipliers show N/A because the selected segment is too narrow and does not contain both comparison groups.")

    st.markdown(f"""
    <div class="card">
      <div class="card-title">Key Findings for Selected Segment</div>
      <div class="card-sub">These findings update when filters change.</div>
      <div class="finding-grid">
        <div class="finding" style="background:#EBF4E3;border-color:#C5E0AA;"><div class="label" style="color:#3D7A1C;">Activation Signal</div>Customers that build 3+ workflows generate <strong>{multiplier_sentence(activation_multiplier)}</strong>.</div>
        <div class="finding" style="background:#E8F0FC;border-color:#AACAF4;"><div class="label" style="color:#1A5FA8;">Claygent Adoption</div>Claygent adopters generate <strong>{multiplier_sentence(claygent_multiplier)}</strong> than non-adopters.</div>
        <div class="finding" style="background:#FDF0E8;border-color:#F4C4A0;"><div class="label" style="color:#C44B0A;">Expansion Play</div><strong>{len(expansion_candidates)}</strong> selected accounts show expansion signals, worth about <strong>{money(expansion_arr_opportunity)}</strong> ARR.</div>
        <div class="finding" style="background:#FCE8E8;border-color:#F0AAAA;"><div class="label" style="color:#B52626;">Churn Risk</div><strong>{len(high_risk)}</strong> selected accounts show high-risk patterns, representing <strong>{money(churn_arr_at_risk)}</strong> ARR at risk.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    section_label("Customer health table")
    table = filtered[[
        "COMPANY_NAME","INDUSTRY","PLAN_TIER","ARR","WORKFLOW_RUNS","DATA_CREDITS_USED",
        "PIPELINE_GENERATED","PIPELINE_PER_CREDIT","EXPANSION_SCORE","CHURN_RISK_SCORE",
        "RISK_BAND","RECOMMENDED_ACTION"
    ]].sort_values("PIPELINE_GENERATED", ascending=False)
    st.dataframe(business_table(table, money_cols=["ARR","PIPELINE_GENERATED"]), use_container_width=True)

with tab2:
    purpose_card("Why & How", "Explains what is happening, why it may be happening, how the app knows, and what Sales or Customer Success should do next.")
    section_label("Diagnostic intelligence: what, why, how, and next action")

    if churn_arr_at_risk > expansion_arr_opportunity and len(high_risk) > 0:
        why_how_card(
            "Main Signal: Retention risk is the highest priority",
            "Selected accounts show elevated churn risk, weak outcome efficiency, or support friction.",
            f"{len(high_risk)} high-risk accounts represent {money(churn_arr_at_risk)} ARR at risk. Average support tickets: {avg_support_tickets:.1f}.",
            "Run CS workflow audits for high-risk accounts and identify whether workflows are failing, targeting is poor, or credits are being spent before value is created.",
            f"Protect up to {money(churn_arr_at_risk)} ARR exposure.",
            "High" if len(high_risk) >= 3 else "Medium",
            "#B52626"
        )
    elif len(expansion_candidates) > 0:
        why_how_card(
            "Main Signal: Expansion opportunity is the highest priority",
            "Selected accounts have strong usage, strong pipeline efficiency, and enough workflow depth to justify an upsell review.",
            f"{len(expansion_candidates)} expansion candidates represent {money(expansion_arr_opportunity)} potential ARR uplift. Avg pipeline per credit: {avg_pipeline_per_credit:.2f}.",
            "Send top candidates to AE/CS for Enterprise upsell review. Lead with proof of pipeline created per Data Credit.",
            f"Potential {money(expansion_arr_opportunity)} ARR uplift.",
            "High" if len(expansion_candidates) >= 5 else "Medium",
            "#E8632A"
        )
    elif claygent_multiplier is not None and claygent_multiplier >= 2:
        why_how_card(
            "Main Signal: Claygent adoption is the strongest growth lever",
            "Claygent users are likely moving from basic enrichment into AI-assisted research and personalization.",
            f"Claygent adopters generate {claygent_multiplier}x more pipeline in this selected segment. Current Claygent adoption rate: {claygent_adoption_rate:.0%}.",
            "Promote Claygent templates earlier in onboarding and target users who have built workflows but have not adopted Claygent.",
            "Higher pipeline generation without immediately increasing paid acquisition spend.",
            "Medium",
            "#1A5FA8"
        )
    elif activation_multiplier is not None and activation_multiplier >= 2:
        why_how_card(
            "Main Signal: Activation depth is the growth lever",
            "Customers reaching 3+ workflows are likely hitting the product aha moment faster.",
            f"Activated users generate {activation_multiplier}x more pipeline. Average workflow runs in selected segment: {avg_workflows:.1f}.",
            "Use day 3 and day 7 nudges to push new workspaces toward 3 completed workflows.",
            "Improves activation and downstream pipeline creation.",
            "Medium",
            "#3D7A1C"
        )
    else:
        why_how_card(
            "Main Signal: No urgent intervention detected",
            "The selected segment does not show a strong enough expansion, activation, or churn signal.",
            f"Selected accounts: {len(filtered)}. Avg pipeline per credit: {avg_pipeline_per_credit:.2f}.",
            "Monitor the segment and collect more usage history before taking action.",
            "Avoids unnecessary CS or Sales effort.",
            "Low",
            "#9A6B00"
        )

    st.markdown("""
    <div class="card">
      <div class="card-title">How this diagnostic layer works</div>
      <div class="card-sub">
      The app does not use fixed text here. It checks the selected segment, compares expansion upside against ARR at risk,
      checks Claygent and activation lift, and then chooses the most relevant business explanation and action.
      </div>
    </div>
    """, unsafe_allow_html=True)


with tab3:
    purpose_card("Activation analysis", "Shows whether early workflow creation and Claygent adoption are tied to stronger pipeline outcomes. Useful for onboarding and product-led growth decisions.")
    section_label("Cohort comparison: first 14-day workflow adoption")
    activation_summary = (
        activation_filtered.assign(
            ACTIVATION_GROUP=activation_filtered["WORKFLOWS_FIRST_14D"].apply(lambda x: "3+ Workflows" if x >= 3 else "<3 Workflows")
        )
        .groupby("ACTIVATION_GROUP")
        .agg(CUSTOMERS=("CUSTOMER_ID","count"), AVG_PIPELINE=("PIPELINE_GENERATED","mean"), AVG_OPPORTUNITIES=("OPPORTUNITIES_CREATED","mean"))
        .reset_index()
    )
    if not activation_summary.empty:
        activation_summary["AVG_PIPELINE"] = activation_summary["AVG_PIPELINE"].round(0)
        activation_summary["AVG_OPPORTUNITIES"] = activation_summary["AVG_OPPORTUNITIES"].round(1)
    c1, c2 = st.columns(2)
    with c1:
        html_bar_chart(activation_summary, "ACTIVATION_GROUP", "AVG_PIPELINE", "Average Pipeline by Activation Group", "Dynamic from selected filters.", "#3D7A1C", "money")
    with c2:
        st.dataframe(business_table(activation_summary, money_cols=["AVG_PIPELINE"]), use_container_width=True)

    claygent_summary = (
        activation_filtered.assign(CLAYGENT_GROUP=activation_filtered["CLAYGENT_ADOPTED"].map({1:"Claygent Adopted",0:"No Claygent"}))
        .groupby("CLAYGENT_GROUP")
        .agg(CUSTOMERS=("CUSTOMER_ID","count"), AVG_PIPELINE=("PIPELINE_GENERATED","mean"), AVG_OPPORTUNITIES=("OPPORTUNITIES_CREATED","mean"))
        .reset_index()
    )
    if not claygent_summary.empty:
        claygent_summary["AVG_PIPELINE"] = claygent_summary["AVG_PIPELINE"].round(0)
        claygent_summary["AVG_OPPORTUNITIES"] = claygent_summary["AVG_OPPORTUNITIES"].round(1)
    c3, c4 = st.columns(2)
    with c3:
        html_bar_chart(claygent_summary, "CLAYGENT_GROUP", "AVG_PIPELINE", "Average Pipeline by Claygent Adoption", "Shows whether Claygent adoption is associated with stronger outcomes.", "#1A5FA8", "money")
    with c4:
        st.dataframe(business_table(claygent_summary, money_cols=["AVG_PIPELINE"]), use_container_width=True)

with tab4:
    purpose_card("Expansion analysis", "Ranks non-enterprise accounts that look ready for upsell based on usage depth, pipeline efficiency, integrations, and expansion score.")
    section_label("Non-enterprise accounts with Enterprise-tier behavior")
    c1, c2, c3 = st.columns(3)
    c1.metric("Expansion Candidates", len(expansion_candidates), help="Non-enterprise accounts with strong expansion score.")
    c2.metric("Potential ARR Uplift", money(expansion_arr_opportunity), help="Estimated annual uplift if expansion candidates move to an Enterprise-like plan.")
    c3.metric("Avg Expansion Score", round(expansion_candidates["EXPANSION_SCORE"].mean(), 1) if len(expansion_candidates) else 0, help="Composite score based on pipeline efficiency, total pipeline, workflow depth, integration depth, and Claygent adoption.")

    top_expansion = expansion_candidates.sort_values("EXPANSION_SCORE", ascending=False)
    st.markdown('<div class="card"><div class="card-title">Top Expansion Candidates</div><div class="card-sub">Ranked by expansion score. Pipeline per Credit means pipeline created for every Data Credit consumed.</div></div>', unsafe_allow_html=True)
    st.dataframe(
        business_table(
            top_expansion[["COMPANY_NAME","PLAN_TIER","ARR","WORKFLOW_RUNS","DATA_CREDITS_USED","PIPELINE_GENERATED","PIPELINE_PER_CREDIT","INTEGRATION_DEPTH","CLAYGENT_USED","EXPANSION_SCORE","RECOMMENDED_ACTION"]],
            money_cols=["ARR","PIPELINE_GENERATED"],
            bool_cols=["CLAYGENT_USED"]
        ),
        use_container_width=True
    )
    leaderboard = filtered.sort_values("PIPELINE_PER_CREDIT", ascending=False).head(15)
    html_bar_chart(leaderboard, "COMPANY_NAME", "PIPELINE_PER_CREDIT", "Pipeline per Credit Leaderboard", "Efficiency score for upsell readiness.", "#E8632A", "decimal", max_rows=15)

with tab5:
    purpose_card("Churn risk analysis", "Identifies accounts that may need Customer Success intervention based on credit burn, low outcome efficiency, support friction, and product adoption.")
    section_label("Churn risk model: Snowflake-scored")
    risk_summary = (
        filtered.groupby("RISK_BAND", observed=True)
        .agg(CUSTOMERS=("CUSTOMER_ID","count"), AVG_RISK_SCORE=("CHURN_RISK_SCORE","mean"), ARR_AT_RISK=("ARR","sum"), AVG_PIPELINE=("PIPELINE_GENERATED","mean"), AVG_CREDITS=("DATA_CREDITS_USED","mean"))
        .reset_index()
    )
    if not risk_summary.empty:
        risk_summary["AVG_RISK_SCORE"] = risk_summary["AVG_RISK_SCORE"].round(1)
        risk_summary["ARR_AT_RISK"] = risk_summary["ARR_AT_RISK"].round(0)
        risk_summary["AVG_PIPELINE"] = risk_summary["AVG_PIPELINE"].round(0)
        risk_summary["AVG_CREDITS"] = risk_summary["AVG_CREDITS"].round(0)
    c1, c2 = st.columns(2)
    with c1:
        html_bar_chart(risk_summary, "RISK_BAND", "CUSTOMERS", "Risk Band Distribution", "High risk means high friction or low outcome efficiency.", "#B52626", "number")
    with c2:
        st.dataframe(business_table(risk_summary, money_cols=["ARR_AT_RISK","AVG_PIPELINE"]), use_container_width=True)
    st.markdown('<div class="card"><div class="card-title">At-Risk Intervention Queue</div><div class="card-sub">Sorted by Snowflake churn score.</div></div>', unsafe_allow_html=True)
    st.dataframe(
        business_table(
            filtered.sort_values("CHURN_RISK_SCORE", ascending=False)[["COMPANY_NAME","PLAN_TIER","ARR","DATA_CREDITS_USED","PIPELINE_GENERATED","PIPELINE_PER_CREDIT","SUPPORT_TICKETS","CLAYGENT_USED","CHURN_RISK_SCORE","RISK_BAND","RECOMMENDED_ACTION"]].head(25),
            money_cols=["ARR","PIPELINE_GENERATED"],
            bool_cols=["CLAYGENT_USED"]
        ),
        use_container_width=True
    )

with tab6:
    purpose_card("Revenue scenario planner", "Lets the business test what-if scenarios for activation, Claygent adoption, expansion conversion, and churn prevention.")
    section_label("Revenue scenario planner")
    st.markdown("""
    <div class="card">
      <div class="card-title">How to read this forecast</div>
      <div class="card-sub">
      This is a directional what-if model, not a prediction model. It estimates MRR impact from four GTM levers:
      activation improvement, Claygent adoption, expansion conversion, and churn prevention.
      These assumptions should be calibrated with real historical conversion data.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="forecast-control-card">
          <div class="forecast-control-title">Scenario assumptions</div>
          <div class="forecast-control-sub">Adjust the GTM levers below to estimate directional MRR impact.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            """
            <div class="compact-label">
                <span>Target activation improvement</span>
                <span class="help-dot" title="Assumed improvement in the share of accounts reaching the early activation threshold.">?</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        activation_lift = st.slider("Target activation improvement", 0, 30, 10, label_visibility="collapsed")

        st.markdown(
            """
            <div class="compact-label">
                <span>Expansion candidate conversion rate</span>
                <span class="help-dot" title="Assumed share of expansion-ready accounts that convert into paid expansion.">?</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        expansion_capture = st.slider("Expansion candidate conversion rate", 0, 100, 25, label_visibility="collapsed")

    with s2:
        st.markdown(
            """
            <div class="compact-label">
                <span>Target Claygent adoption improvement</span>
                <span class="help-dot" title="Assumed improvement in Claygent adoption across the selected segment.">?</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        claygent_lift = st.slider("Target Claygent adoption improvement", 0, 30, 10, label_visibility="collapsed")

        st.markdown(
            """
            <div class="compact-label">
                <span>High-risk account save rate</span>
                <span class="help-dot" title="Assumed share of high-risk ARR that Customer Success can retain.">?</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        churn_save_rate = st.slider("High-risk account save rate", 0, 100, 20, label_visibility="collapsed")

    activation_mrr_impact = current_mrr * (activation_lift / 100) * 0.35
    claygent_mrr_impact = current_mrr * (claygent_lift / 100) * 0.28
    expansion_mrr_impact = (expansion_arr_opportunity / 12) * (expansion_capture / 100)
    churn_mrr_saved = (churn_arr_at_risk / 12) * (churn_save_rate / 100)
    forecast_mrr = current_mrr + activation_mrr_impact + claygent_mrr_impact + expansion_mrr_impact + churn_mrr_saved

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current MRR", money(current_mrr), help="Monthly recurring revenue from selected accounts.")
    c2.metric("Forecast MRR", money(forecast_mrr), help="Projected MRR after applying scenario sliders.")
    c3.metric("MRR Lift", money(forecast_mrr - current_mrr), help="Difference between forecast and current MRR.")
    c4.metric("Lift %", f"{(safe_divide(forecast_mrr-current_mrr, current_mrr) or 0)*100:.1f}%", help="Percentage increase from current MRR to forecast MRR.")

    intervention_table = pd.DataFrame([
        {"Lever":"Activation Lift","Formula":"Current MRR × activation improvement % × 0.35 sensitivity","Estimated MRR Impact":activation_mrr_impact,"Effort Hours":30},
        {"Lever":"Claygent Lift","Formula":"Current MRR × Claygent improvement % × 0.28 sensitivity","Estimated MRR Impact":claygent_mrr_impact,"Effort Hours":24},
        {"Lever":"Expansion Capture","Formula":"Expansion ARR ÷ 12 × conversion rate","Estimated MRR Impact":expansion_mrr_impact,"Effort Hours":40},
        {"Lever":"Churn Saved","Formula":"ARR at Risk ÷ 12 × save rate","Estimated MRR Impact":churn_mrr_saved,"Effort Hours":50},
    ])
    intervention_table["Estimated MRR per GTM Hour"] = intervention_table.apply(lambda r: (safe_divide(r["Estimated MRR Impact"], r["Effort Hours"]) or 0), axis=1)
    st.dataframe(business_table(intervention_table, money_cols=["Estimated MRR Impact","Estimated MRR per GTM Hour"]), use_container_width=True)
    forecast_df = pd.DataFrame({"Scenario":["Current MRR","Activation Lift","Claygent Lift","Expansion Capture","Churn Saved","Forecast MRR"],"Value":[current_mrr,activation_mrr_impact,claygent_mrr_impact,expansion_mrr_impact,churn_mrr_saved,forecast_mrr]})
    html_bar_chart(forecast_df, "Scenario", "Value", "Scenario Impact", "Visual breakdown of current MRR, each lever, and forecast MRR.", "#6B2FA8", "money", max_rows=6)

with tab7:
    purpose_card("Signal Feed", "Converts Snowflake metrics into prioritized GTM alerts with hypotheses and recommended actions.")
    section_label("Auto-surfaced signals from the selected segment")
    has_signal = False
    if activation_multiplier is not None and activation_multiplier >= 2:
        signal_card("Activation threshold is highly predictive", f"Customers reaching 3+ workflows generate {activation_multiplier}x more pipeline in the selected segment.", "Add onboarding prompts that push new users to create 3 workflows within 14 days.", "P0", "#3D7A1C")
        has_signal = True
    if claygent_multiplier is not None and claygent_multiplier >= 2:
        signal_card("Claygent adoption has strong pipeline lift", f"Claygent adopters generate {claygent_multiplier}x more pipeline than non-adopters in the selected segment.", "Promote Claygent templates earlier in onboarding and Customer Success playbooks.", "P0", "#1A5FA8")
        has_signal = True
    if len(expansion_candidates) > 0:
        signal_card("Expansion-ready accounts detected", f"{len(expansion_candidates)} selected non-enterprise accounts show Enterprise-like usage and outcomes.", "Send account list to Sales and Customer Success for upsell review.", "P1", "#E8632A")
        has_signal = True
    if len(high_risk) > 0:
        signal_card("High-risk credit waste segment detected", f"{len(high_risk)} selected accounts show poor outcome efficiency and elevated churn risk.", "Trigger Customer Success intervention for high-risk accounts with ARR exposure.", "P1", "#B52626")
        has_signal = True
    if not has_signal:
        st.success("No major risk or expansion signals detected for the selected segment.")
    st.markdown('<div class="card"><div class="card-title">Global Snowflake Signal Feed</div><div class="card-sub">Generated from the dbt mart DBT_NSHANKAR.SIGNAL_FEED.</div></div>', unsafe_allow_html=True)
    st.dataframe(business_table(global_signals), use_container_width=True)

with tab8:
    purpose_card("Analytics Workbench", "Lets technical users inspect analytical logic, run useful business queries, preview results, and download CSV outputs.")
    section_label("Interactive Analytics Workbench")

    sql_models = {
        "Churn Risk Queue": {
            "what": "Which accounts should Customer Success prioritize first?",
            "user": "Customer Success, GTM Ops",
            "why": "Turns credit usage, weak outcomes, support friction, and adoption signals into an intervention queue.",
            "business_use": "Gives CS a ranked list of high-risk accounts and the supporting evidence behind each recommendation.",
            "query": """SELECT
    company_name,
    plan_tier,
    industry,
    arr,
    churn_risk_score,
    risk_band,
    support_tickets,
    data_credits_used,
    pipeline_generated,
    pipeline_per_credit,
    claygent_used,
    recommended_action
FROM CLAY_REVENUE_INTELLIGENCE.DBT_NSHANKAR.CHURN_RISK_SCORES
WHERE risk_band = 'HIGH'
ORDER BY churn_risk_score DESC, arr DESC
LIMIT 25;"""
        },
        "Activation Drivers": {
            "what": "Which early product behaviors are associated with stronger pipeline?",
            "user": "Product, Customer Success, Growth",
            "why": "Shows whether customers who build 3+ workflows in the first 14 days generate stronger downstream outcomes.",
            "business_use": "Helps the team decide what onboarding behavior to push during the first two weeks.",
            "query": """SELECT
    CASE
        WHEN workflows_first_14d >= 3 THEN '3+ Workflows'
        ELSE '<3 Workflows'
    END AS activation_group,
    COUNT(*) AS customers,
    ROUND(AVG(pipeline_generated), 0) AS avg_pipeline,
    ROUND(AVG(opportunities_created), 1) AS avg_opportunities
FROM CLAY_REVENUE_INTELLIGENCE.DBT_NSHANKAR.ACTIVATION_VELOCITY
GROUP BY 1
ORDER BY avg_pipeline DESC;"""
        },
        "Claygent Adoption Lift": {
            "what": "Does Claygent adoption appear to improve GTM outcomes?",
            "user": "Product, Growth, Customer Success",
            "why": "Compares downstream pipeline and opportunities between Claygent adopters and non-adopters.",
            "business_use": "Supports decisions around Claygent onboarding, templates, and adoption campaigns.",
            "query": """SELECT
    CASE
        WHEN claygent_adopted = 1 THEN 'Claygent Adopted'
        ELSE 'No Claygent'
    END AS claygent_group,
    COUNT(*) AS customers,
    ROUND(AVG(pipeline_generated), 0) AS avg_pipeline,
    ROUND(AVG(opportunities_created), 1) AS avg_opportunities
FROM CLAY_REVENUE_INTELLIGENCE.DBT_NSHANKAR.ACTIVATION_VELOCITY
GROUP BY 1
ORDER BY avg_pipeline DESC;"""
        },
        "Expansion Candidates": {
            "what": "Which accounts should Sales review for upsell?",
            "user": "Sales, Customer Success, GTM Ops",
            "why": "Finds non-enterprise accounts with strong usage, high pipeline efficiency, and strong expansion score.",
            "business_use": "Gives Sales and CS a prioritized account list for Enterprise upsell conversations.",
            "query": """SELECT
    company_name,
    plan_tier,
    industry,
    arr,
    expansion_score,
    workflow_runs,
    integration_depth,
    pipeline_generated,
    pipeline_per_credit,
    claygent_used,
    recommended_action
FROM CLAY_REVENUE_INTELLIGENCE.DBT_NSHANKAR.CHURN_RISK_SCORES
WHERE plan_tier IN ('Starter', 'Explorer', 'Pro')
  AND expansion_score >= 70
ORDER BY expansion_score DESC, pipeline_per_credit DESC
LIMIT 25;"""
        },
        "Credit Efficiency": {
            "what": "Which accounts create the most pipeline per Data Credit?",
            "user": "Finance, GTM Ops, Customer Success",
            "why": "Shows whether usage is translating into business value or just consuming credits.",
            "business_use": "Helps identify efficient accounts for expansion and inefficient accounts for workflow audits.",
            "query": """SELECT
    company_name,
    plan_tier,
    industry,
    data_credits_used,
    pipeline_generated,
    pipeline_per_credit,
    workflow_runs,
    claygent_used,
    recommended_action
FROM CLAY_REVENUE_INTELLIGENCE.DBT_NSHANKAR.CHURN_RISK_SCORES
WHERE data_credits_used > 0
ORDER BY pipeline_per_credit DESC
LIMIT 25;"""
        },
        "Prioritized Signal Feed": {
            "what": "What should the GTM team pay attention to right now?",
            "user": "GTM Leadership, RevOps, Sales, Customer Success",
            "why": "Converts thresholds into prioritized signals with hypotheses and recommended actions.",
            "business_use": "Turns analytics into an action list instead of just reporting metrics.",
            "query": """SELECT
    severity,
    signal_type,
    signal_title,
    metric_value,
    comparison_value,
    hypothesis,
    recommended_action
FROM CLAY_REVENUE_INTELLIGENCE.DBT_NSHANKAR.SIGNAL_FEED
ORDER BY
    CASE severity
        WHEN 'P0' THEN 1
        WHEN 'P1' THEN 2
        ELSE 3
    END;"""
        }
    }

    selected_model = st.selectbox("Choose an analysis", list(sql_models.keys()))
    selected = sql_models[selected_model]

    st.markdown(
        f"""
        <div class="workbench-grid">
          <div class="workbench-mini"><span>What it answers</span>{selected["what"]}</div>
          <div class="workbench-mini"><span>Business user</span>{selected["user"]}</div>
          <div class="workbench-mini"><span>Why it matters</span>{selected["why"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"**Business use:** {selected['business_use']}")

    query = st.text_area("SQL query", value=selected["query"], height=230)

    col_run, col_note = st.columns([1, 4])
    with col_run:
        run_clicked = st.button("Run query")
    with col_note:
        st.caption("Queries are editable and restricted to read-only SELECT/WITH statements for governed analysis.")

    if run_clicked:
        cleaned_query = query.strip().lower()
        if not cleaned_query.startswith("select") and not cleaned_query.startswith("with"):
            st.error("Only read-only SELECT/WITH queries are allowed in this governed analytics workspace.")
        else:
            result = run_query(query)
            st.dataframe(business_table(result), use_container_width=True)
            st.download_button(
                "Download result as CSV",
                result.to_csv(index=False).encode("utf-8"),
                file_name=f"{selected_model.lower().replace(' ','_')}.csv",
                mime="text/csv"
            )

with tab9:
    purpose_card("AI Analyst", "Explains the selected segment in plain English using only the Snowflake metrics shown in the app. Cortex-ready architecture with a deterministic fallback when LLM functions are unavailable.")
    section_label("AI Analyst: grounded explanation layer")

    st.markdown("""
    <div class="card">
      <div class="card-title">How this explanation layer works</div>
      <div class="card-sub">
      This tab uses a deterministic explanation layer powered by the same Snowflake metrics used in the rest of the app.
      In environments where Snowflake Cortex LLM functions are enabled, the same grounded context can be passed to AI_COMPLETE for natural-language analysis.
      </div>
    </div>
    """, unsafe_allow_html=True)

    context_summary = {
        "Selected Accounts": len(filtered),
        "Activation Multiplier": activation_multiplier,
        "Claygent Multiplier": claygent_multiplier,
        "Expansion Candidates": len(expansion_candidates),
        "Expansion ARR Opportunity": expansion_arr_opportunity,
        "High Risk Accounts": len(high_risk),
        "ARR at Risk": churn_arr_at_risk,
        "Avg Pipeline per Credit": avg_pipeline_per_credit,
        "Avg Workflows": avg_workflows,
        "Avg Support Tickets": avg_support_tickets,
        "Claygent Adoption Rate": claygent_adoption_rate
    }

    st.markdown("""
    <div class="card">
      <div class="card-title">Grounding context from Snowflake</div>
      <div class="card-sub">
      The answer below is generated only from these selected-segment metrics.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(
        pd.DataFrame(
            [{"Metric": k, "Value": money(v) if "ARR" in k or "Opportunity" in k else v} for k, v in context_summary.items()]
        ),
        use_container_width=True
    )

    question = st.text_input(
        "Ask the AI analyst",
        "Why is this selected segment risky or valuable?"
    )

    def fallback_ai_answer(question_text):
        q = question_text.lower()

        if len(filtered) == 0:
            return """
**What happened:** There are no accounts in the selected segment.

**Why it may be happening:** The selected filters are too narrow.

**Evidence:** The filtered account count is 0.

**Recommended action:** Broaden the filters before drawing conclusions.

**Confidence:** High.
"""

        if "risk" in q or "risky" in q or "churn" in q:
            if len(high_risk) > 0:
                return f"""
**What happened:** This segment has a meaningful churn-risk pocket.

**Why it may be happening:** Some accounts appear to have weaker outcome efficiency, support friction, or low conversion of usage into pipeline.

**Evidence:** {len(high_risk)} accounts are marked high risk, representing {money(churn_arr_at_risk)} ARR at risk. Average support tickets are {avg_support_tickets:.1f}, and average pipeline per credit is {avg_pipeline_per_credit:.2f}.

**Recommended action:** Prioritize these accounts for CS workflow audits. Check whether credits are being spent on low-quality workflows, poor targeting, or setup friction.

**Confidence:** {"High" if len(high_risk) >= 3 else "Medium"}.
"""
            return f"""
**What happened:** This selected segment does not show a major churn-risk signal.

**Why it may be happening:** The selected accounts have limited high-risk exposure based on the current risk scoring model.

**Evidence:** High-risk accounts: {len(high_risk)}. ARR at risk: {money(churn_arr_at_risk)}.

**Recommended action:** Monitor this segment and focus on expansion or activation opportunities instead.

**Confidence:** Medium.
"""

        if "expansion" in q or "upsell" in q or "sales" in q or "valuable" in q:
            if len(expansion_candidates) > 0:
                return f"""
**What happened:** This segment has expansion-ready accounts.

**Why it may be happening:** These accounts show strong usage, stronger pipeline efficiency, or enough workflow depth to justify an upsell review.

**Evidence:** {len(expansion_candidates)} accounts qualify as expansion candidates, representing about {money(expansion_arr_opportunity)} in potential ARR uplift. Average pipeline per credit is {avg_pipeline_per_credit:.2f}.

**Recommended action:** Send the top expansion candidates to Sales and Customer Success. Lead the conversation with proof of pipeline generated per Data Credit.

**Confidence:** {"High" if len(expansion_candidates) >= 5 else "Medium"}.
"""
            return f"""
**What happened:** This selected segment does not currently show a strong expansion signal.

**Why it may be happening:** There may not be enough non-enterprise accounts with high expansion scores in the selected filters.

**Evidence:** Expansion candidates: {len(expansion_candidates)}. Expansion ARR opportunity: {money(expansion_arr_opportunity)}.

**Recommended action:** Look at activation and Claygent adoption first, then re-evaluate expansion once more accounts show deeper usage.

**Confidence:** Medium.
"""

        if "claygent" in q:
            if claygent_multiplier is not None and claygent_multiplier >= 2:
                return f"""
**What happened:** Claygent adoption is a strong growth lever in this selected segment.

**Why it may be happening:** Claygent users are likely moving beyond basic enrichment into AI-assisted research and personalization, which can create better outbound quality and stronger GTM outcomes.

**Evidence:** Claygent adopters generate {claygent_multiplier}x more pipeline than non-adopters. Current Claygent adoption rate is {claygent_adoption_rate:.0%}.

**Recommended action:** Promote Claygent templates earlier in onboarding and target users who have built workflows but have not adopted Claygent.

**Confidence:** Medium.
"""
            return f"""
**What happened:** Claygent impact is not conclusive for this selected segment.

**Why it may be happening:** The filtered segment may not contain enough Claygent adopters and non-adopters to make a fair comparison.

**Evidence:** Claygent multiplier: {format_multiplier(claygent_multiplier)}. Claygent adoption rate: {claygent_adoption_rate:.0%}.

**Recommended action:** Broaden the filters or collect more Claygent usage data before making a decision.

**Confidence:** Low.
"""

        if "activation" in q or "workflow" in q or "onboarding" in q:
            if activation_multiplier is not None and activation_multiplier >= 2:
                return f"""
**What happened:** Activation depth is strongly tied to pipeline generation.

**Why it may be happening:** Customers that build 3+ workflows may be reaching the product aha moment faster and turning Clay into a repeatable GTM motion.

**Evidence:** Customers with 3+ workflows generate {activation_multiplier}x more pipeline. Average workflow runs in this segment are {avg_workflows:.1f}.

**Recommended action:** Add day 3 and day 7 onboarding nudges that push new customers toward 3 completed workflows.

**Confidence:** Medium.
"""
            return f"""
**What happened:** Activation lift is not conclusive for this selected segment.

**Why it may be happening:** The selected filters may not include enough accounts in both workflow comparison groups.

**Evidence:** Activation multiplier: {format_multiplier(activation_multiplier)}. Average workflows: {avg_workflows:.1f}.

**Recommended action:** Broaden the segment or inspect workflow completion quality instead of only workflow count.

**Confidence:** Low.
"""

        if churn_arr_at_risk > expansion_arr_opportunity and len(high_risk) > 0:
            return f"""
**What happened:** Retention risk should be the main priority for this segment.

**Why it may be happening:** ARR at risk is larger than the estimated expansion opportunity, so protecting existing revenue matters more than chasing upsell first.

**Evidence:** ARR at risk is {money(churn_arr_at_risk)} versus expansion ARR opportunity of {money(expansion_arr_opportunity)}.

**Recommended action:** Start with CS intervention and workflow audits for high-risk accounts.

**Confidence:** High.
"""
        elif len(expansion_candidates) > 0:
            return f"""
**What happened:** Expansion is the main opportunity for this segment.

**Why it may be happening:** Selected accounts show strong usage or efficiency patterns that suggest they may be ready for a higher plan or Enterprise motion.

**Evidence:** {len(expansion_candidates)} expansion candidates represent {money(expansion_arr_opportunity)} in potential ARR uplift.

**Recommended action:** Prioritize top expansion candidates for AE/CS review.

**Confidence:** High.
"""
        else:
            return f"""
**What happened:** No dominant business signal is detected for this segment.

**Why it may be happening:** The segment does not currently show strong enough churn, expansion, activation, or Claygent signals.

**Evidence:** Selected accounts: {len(filtered)}. Expansion candidates: {len(expansion_candidates)}. High-risk accounts: {len(high_risk)}.

**Recommended action:** Monitor the segment and gather more usage history before taking action.

**Confidence:** Low.
"""

    if st.button("Ask AI Analyst"):
        st.markdown(fallback_ai_answer(question))

    with st.expander("Cortex implementation note"):
        st.markdown("""
In a Snowflake environment where Cortex LLM functions are enabled, this deterministic fallback can be replaced with:

```sql
SELECT AI_COMPLETE(
  'llama3.1-8b',
  '<grounded prompt with selected-segment Snowflake metrics>'
) AS answer;
```

The important architecture remains the same:

1. dbt-built Snowflake metrics are the source of truth  
2. The selected segment context is passed to the model  
3. The model is instructed to answer only from that context  
4. If the context is insufficient, it must say not enough data  
""")
