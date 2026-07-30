from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared_ui import render_portfolio_footer
from src.scenario import Scenario, apply_scenario, scenario_summary

PANEL_PATH = Path("data/processed/repd_panel.csv.gz")
FORECAST_PATH = Path("data/processed/latest_forecasts.csv.gz")
METRICS_PATH = Path("data/processed/model_metrics.json")
QUALITY_PATH = Path("data/processed/data_quality_report.json")
EXTERNAL_CONTEXT_PATH = Path("data/processed/external_context.csv")
EXTERNAL_METADATA_PATH = Path("data/processed/external_metadata.json")

MODEL_LABELS = {
    "empirical_survival": "Empirical survival baseline",
    "survival_logistic": "Logistic survival model",
    "catboost_survival": "CatBoost AI challenger",
    "historical_base_rate": "Historical base rate",
}
STATUS_LABELS = {
    "promising": "Promising research model",
    "experimental": "Experimental model",
    "research_only": "Research-only forecast",
}

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    .forecast-status {
        border: 1px solid #D8E2DB;
        border-radius: 16px;
        padding: .85rem 1rem;
        background: #F8FAF8;
        margin: .35rem 0 1rem;
    }
    .forecast-status strong {color: #17221C;}
    .factor-positive, .factor-risk {
        border-radius: 14px;
        padding: .85rem 1rem;
        min-height: 92px;
    }
    .factor-positive {
        background: #F0F8F3;
        border: 1px solid #CDE5D4;
    }
    .factor-risk {
        background: #FFF8ED;
        border: 1px solid #F0DDB8;
    }
    .factor-positive p, .factor-risk p {margin: 0;}
    .source-card {
        border: 1px solid #DDE5DF;
        border-radius: 14px;
        padding: .9rem 1rem;
        background: #FFFFFF;
        min-height: 134px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict, pd.DataFrame, dict]:
    required = [
        PANEL_PATH,
        FORECAST_PATH,
        METRICS_PATH,
        QUALITY_PATH,
        EXTERNAL_CONTEXT_PATH,
        EXTERNAL_METADATA_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing generated files: "
            + ", ".join(missing)
            + ". Run `uv run python bootstrap.py --skip-download`."
        )
    panel = pd.read_csv(PANEL_PATH, compression="gzip", low_memory=False)
    forecasts = pd.read_csv(FORECAST_PATH, compression="gzip", low_memory=False)
    for frame in (panel, forecasts):
        for column in (
            "snapshot_date",
            "planning_submitted",
            "planning_granted",
            "under_construction_date",
            "operational_date",
        ):
            if column in frame:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    quality = json.loads(QUALITY_PATH.read_text(encoding="utf-8"))
    external = pd.read_csv(EXTERNAL_CONTEXT_PATH)
    external["date"] = pd.to_datetime(external["date"], errors="coerce")
    external = external.dropna(subset=["date"]).sort_values("date")
    external_metadata = json.loads(
        EXTERNAL_METADATA_PATH.read_text(encoding="utf-8")
    )
    return panel, forecasts, metrics, quality, external, external_metadata


def style_chart(figure: go.Figure, *, height: int = 430) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=45, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, Inter, Segoe UI, sans-serif",
            color="#17221C",
        ),
        colorway=["#0E6B4F", "#7AAE92", "#D59C4A", "#5D7C6A", "#9AA69E"],
        legend_title_text="",
        hoverlabel=dict(bgcolor="white"),
    )
    figure.update_xaxes(gridcolor="#EDF1EE", zeroline=False)
    figure.update_yaxes(gridcolor="#EDF1EE", zeroline=False)
    return figure


def format_probability(value: float) -> str:
    return "N/A" if pd.isna(value) else f"{100 * float(value):.1f}%"


def format_metric(value: float | None, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.{digits}f}"


def format_capacity(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "Not reported"
    return f"{float(value):,.{digits}f} MW"


def project_brief(row: pd.Series, snapshot: pd.Timestamp) -> str:
    lines = [
        f"# {row.get('site_name', 'Unnamed project')}",
        "",
        f"Forecast snapshot: {snapshot:%d %B %Y}",
        f"Developer / applicant: {row.get('operator', 'Unknown')}",
        f"Technology: {row.get('technology', 'Unknown')}",
        f"Region: {row.get('region', 'Unknown')}",
        f"Stage: {row.get('stage', 'Unknown')}",
        f"Capacity: {format_capacity(row.get('capacity_mw'))}",
        "",
        "## Time-to-operation forecast",
        "",
        f"- Within 2 years: {format_probability(row.get('prob_operational_2y'))}",
        f"- Within 3 years: {format_probability(row.get('prob_operational_3y'))}",
        f"- Within 5 years: {format_probability(row.get('prob_operational_5y'))}",
        f"- Public-data confidence: {row.get('forecast_confidence', 'Low')}",
        "",
        "## Public-data signals",
        "",
        f"Positive: {row.get('positive_factors', '')}",
        f"Risks: {row.get('risk_factors', '')}",
        "",
        "Forecasts are experimental research estimates based on public data and are "
        "not investment advice.",
    ]
    return "\n".join(lines)


try:
    panel, forecasts, metrics, quality, external, external_metadata = load_data()
except Exception as exc:  # noqa: BLE001
    st.error("The forecasting package has not been generated correctly.")
    st.code(str(exc))
    st.markdown(
        """
        From the project folder, run:

        ```bash
        uv sync
        uv run python bootstrap.py --skip-download
        uv run streamlit run app.py
        ```
        """
    )
    st.stop()

latest_snapshot = pd.Timestamp(forecasts["snapshot_date"].max())
release_status = metrics.get("release_status", "research_only")
selected_model = metrics.get("selected_model", "empirical_survival")

with st.container(border=True):
    header_left, header_right = st.columns([1.9, 1], vertical_alignment="top")
    with header_left:
        st.title("UK Renewable Infrastructure Forecasting")
        st.write(
            "Explore project histories, compare time-to-operation estimates and stress-test "
            "the UK pipeline against economic, grid and policy scenarios."
        )
        st.caption(
            "This section models the active, non-operational pipeline. The complete "
            "Project Explorer dataset and all of its screening tools remain unchanged."
        )
        forecast_search = st.text_input(
            "Search projects",
            placeholder="Search project, developer, technology or region…",
            key="forecast_project_search_v2",
        )
    with header_right:
        a, b = st.columns(2)
        with a:
            st.metric("Projects modelled", f"{len(forecasts):,}")
        with b:
            st.metric("Data snapshots", f"{metrics.get('snapshots', 0):,}")
        st.caption(
            f"Forecast snapshot · {latest_snapshot:%d %b %Y}  \n"
            f"Model v{metrics.get('model_version', '2.0.0')} · "
            f"{STATUS_LABELS.get(release_status, release_status)}"
        )

if release_status == "research_only":
    st.warning(
        "The corrected backtests do not yet support decision-grade probabilities. "
        "The transparent survival baseline is shown; the CatBoost AI challenger was "
        "automatically rejected because it did not improve reliability consistently."
    )
elif release_status == "experimental":
    st.info(
        "These are experimental, time-based probability estimates. Use the Trust Centre "
        "before relying on any individual forecast."
    )

with st.expander("Filters", expanded=False):
    filter_a, filter_b, filter_c, filter_d = st.columns(4)
    with filter_a:
        technology = st.multiselect(
            "Technology",
            sorted(forecasts["technology"].dropna().astype(str).unique()),
        )
    with filter_b:
        region = st.multiselect(
            "Region", sorted(forecasts["region"].dropna().astype(str).unique())
        )
    with filter_c:
        stage = st.multiselect(
            "Current stage",
            sorted(forecasts["stage"].dropna().astype(str).unique()),
        )
    with filter_d:
        minimum_capacity = st.number_input(
            "Minimum capacity (MW)",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )

filtered = forecasts.copy()
if forecast_search.strip():
    term = forecast_search.strip()
    search_columns = [
        column
        for column in ("site_name", "operator", "technology", "region", "stage")
        if column in filtered
    ]
    mask = pd.Series(False, index=filtered.index)
    for column in search_columns:
        mask |= filtered[column].astype(str).str.contains(
            term, case=False, na=False, regex=False
        )
    filtered = filtered[mask]
if technology:
    filtered = filtered[filtered["technology"].isin(technology)]
if region:
    filtered = filtered[filtered["region"].isin(region)]
if stage:
    filtered = filtered[filtered["stage"].isin(stage)]
filtered = filtered[
    pd.to_numeric(filtered["capacity_mw"], errors="coerce").fillna(0)
    >= minimum_capacity
].copy()

if filtered.empty:
    st.warning("No current projects match these filters.")
    st.stop()

active_view: list[str] = []
if forecast_search.strip():
    active_view.append(f"Search: {forecast_search.strip()}")
if technology:
    active_view.append("Technology: " + ", ".join(technology[:3]))
if region:
    active_view.append("Region: " + ", ".join(region[:3]))
if stage:
    active_view.append("Stage: " + ", ".join(stage[:3]))
if minimum_capacity:
    active_view.append(f"Minimum capacity: {minimum_capacity:,.0f} MW")
st.caption("Active view · " + (" · ".join(active_view) if active_view else "All projects"))

overview_tab, project_tab, scenario_tab, history_tab, map_tab, trust_tab = st.tabs(
    ["Overview", "Projects", "Scenario Lab", "History", "Map", "Trust Centre"]
)

with overview_tab:
    total_capacity = filtered["capacity_mw"].fillna(0).sum()
    expected_3y = filtered["expected_capacity_3y_mw"].fillna(0).sum()
    moderate_confidence = filtered["forecast_confidence"].eq("Moderate").mean()
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    with metric_1:
        st.metric("Active projects", f"{len(filtered):,}")
    with metric_2:
        st.metric("Pipeline capacity", f"{total_capacity:,.0f} MW")
    with metric_3:
        st.metric("3-year expected capacity", f"{expected_3y:,.0f} MW")
    with metric_4:
        st.metric("Moderate-confidence records", f"{100 * moderate_confidence:.1f}%")

    chart_left, chart_right = st.columns([1.35, 1])
    with chart_left:
        region_forecast = (
            filtered.groupby("region", dropna=False)
            .agg(
                pipeline_mw=("capacity_mw", "sum"),
                expected_3y_mw=("expected_capacity_3y_mw", "sum"),
            )
            .reset_index()
            .sort_values("expected_3y_mw", ascending=False)
            .head(12)
            .sort_values("expected_3y_mw")
        )
        fig = go.Figure()
        fig.add_bar(
            y=region_forecast["region"],
            x=region_forecast["pipeline_mw"],
            name="Raw pipeline",
            orientation="h",
            marker_color="#DDE8E1",
        )
        fig.add_bar(
            y=region_forecast["region"],
            x=region_forecast["expected_3y_mw"],
            name="Probability-weighted",
            orientation="h",
            marker_color="#0E6B4F",
        )
        fig.update_layout(
            barmode="overlay",
            title="Where probability-weighted capacity is concentrated",
        )
        fig.update_xaxes(title="Capacity (MW)")
        fig.update_yaxes(title=None)
        st.plotly_chart(style_chart(fig, height=500), width="stretch")
    with chart_right:
        distribution = filtered[
            ["prob_operational_3y", "stage"]
        ].dropna()
        fig = px.histogram(
            distribution,
            x="prob_operational_3y",
            color="stage",
            nbins=25,
            labels={
                "prob_operational_3y": "Probability of operation within 3 years",
                "count": "Projects",
                "stage": "Stage",
            },
            title="Forecast distribution by current stage",
        )
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(style_chart(fig, height=500), width="stretch")

    st.subheader("Projects to review")
    review = filtered.sort_values(
        ["prob_operational_3y", "capacity_mw"], ascending=False
    ).head(20).copy()
    review["3-year forecast"] = review["prob_operational_3y"].map(format_probability)
    st.dataframe(
        review[
            [
                "site_name",
                "operator",
                "technology",
                "region",
                "stage",
                "capacity_mw",
                "3-year forecast",
                "forecast_confidence",
            ]
        ].rename(
            columns={
                "site_name": "Project",
                "operator": "Developer / applicant",
                "technology": "Technology",
                "region": "Region",
                "stage": "Stage",
                "capacity_mw": "Capacity (MW)",
                "forecast_confidence": "Evidence confidence",
            }
        ),
        width="stretch",
        hide_index=True,
    )

with project_tab:
    st.header("Project intelligence")
    choices = filtered.sort_values(
        ["site_name", "capacity_mw"], ascending=[True, False]
    ).reset_index(drop=True)
    selected_index = st.selectbox(
        "Choose a project",
        options=list(choices.index),
        format_func=lambda index: (
            f"{choices.loc[index, 'site_name']} · "
            f"{choices.loc[index, 'region']} · "
            f"{format_capacity(choices.loc[index, 'capacity_mw'], digits=0)}"
        ),
    )
    selected = choices.loc[selected_index]

    a, b, c, d = st.columns(4)
    with a:
        st.metric("Capacity", format_capacity(selected["capacity_mw"]))
    with b:
        st.metric(
            "Within 2 years", format_probability(selected["prob_operational_2y"])
        )
    with c:
        st.metric(
            "Within 3 years", format_probability(selected["prob_operational_3y"])
        )
    with d:
        st.metric(
            "Within 5 years", format_probability(selected["prob_operational_5y"])
        )

    factor_left, factor_right = st.columns(2)
    with factor_left:
        st.markdown(
            '<div class="factor-positive"><p><strong>Positive public-data signals</strong>'
            f"<br>{selected.get('positive_factors', '')}</p></div>",
            unsafe_allow_html=True,
        )
    with factor_right:
        st.markdown(
            '<div class="factor-risk"><p><strong>Risks and missing evidence</strong>'
            f"<br>{selected.get('risk_factors', '')}</p></div>",
            unsafe_allow_html=True,
        )

    detail_left, detail_right = st.columns([1.15, 1])
    with detail_left:
        curve = pd.DataFrame(
            {
                "Years": [2, 3, 5],
                "Deployed forecast": [
                    selected["prob_operational_2y"],
                    selected["prob_operational_3y"],
                    selected["prob_operational_5y"],
                ],
                "CatBoost challenger": [
                    selected["ai_prob_operational_2y"],
                    selected["ai_prob_operational_3y"],
                    selected["ai_prob_operational_5y"],
                ],
            }
        )
        fig = go.Figure()
        fig.add_scatter(
            x=curve["Years"],
            y=curve["Deployed forecast"],
            mode="lines+markers",
            name="Deployed survival baseline",
            line=dict(color="#0E6B4F", width=4),
        )
        fig.add_scatter(
            x=curve["Years"],
            y=curve["CatBoost challenger"],
            mode="lines+markers",
            name="Rejected AI challenger",
            line=dict(color="#C7954A", width=2, dash="dot"),
        )
        fig.update_layout(title="Probability of reaching operation")
        fig.update_xaxes(title="Forecast horizon (years)", tickvals=[2, 3, 5])
        fig.update_yaxes(title="Probability", tickformat=".0%", range=[0, 1])
        st.plotly_chart(style_chart(fig), width="stretch")
        st.caption(
            "The CatBoost line is diagnostic only. It is not deployed because its "
            "temporal-holdout reliability was worse."
        )
    with detail_right:
        details = pd.DataFrame(
            {
                "Field": [
                    "Developer / applicant",
                    "Technology",
                    "Region",
                    "Country",
                    "Current stage",
                    "Planning authority",
                    "Evidence confidence",
                    "Historical observations",
                ],
                "Value": [
                    selected.get("operator", ""),
                    selected.get("technology", ""),
                    selected.get("region", ""),
                    selected.get("country", ""),
                    selected.get("stage", ""),
                    selected.get("planning_authority", ""),
                    selected.get("forecast_confidence", ""),
                    str(int(selected.get("observations_to_date", 0))),
                ],
            }
        )
        st.dataframe(details, width="stretch", hide_index=True)
        brief = project_brief(selected, latest_snapshot)
        st.download_button(
            "Download project brief",
            data=brief,
            file_name=(
                str(selected.get("site_name", "project"))
                .replace("/", "-")
                .replace(" ", "_")
                + "_forecast.md"
            ),
            mime="text/markdown",
            width="stretch",
        )

    project_history = panel[
        panel["project_key"].eq(selected["project_key"])
    ].sort_values("snapshot_date")
    if not project_history.empty:
        st.subheader("Observed history")
        st.dataframe(
            project_history[
                ["snapshot_date", "stage", "capacity_mw", "status_short"]
            ].drop_duplicates(),
            width="stretch",
            hide_index=True,
        )

with scenario_tab:
    st.header("Economic and policy scenario lab")
    st.write(
        "Adjust external conditions to stress-test the published forecast. These effects "
        "are explicit assumptions—not AI-generated facts or causal estimates."
    )
    latest_external = external.iloc[-1]
    macro_1, macro_2, macro_3 = st.columns(3)
    with macro_1:
        st.metric(
            "Bank Rate",
            f"{latest_external.get('bank_rate_pct', np.nan):.2f}%",
            help="Latest monthly Bank of England observation in the packaged context.",
        )
    with macro_2:
        st.metric(
            "UK CPI inflation",
            f"{latest_external.get('cpi_annual_pct', np.nan):.1f}%",
            help="ONS headline CPI annual rate.",
        )
    with macro_3:
        st.metric(
            "Infrastructure cost inflation",
            f"{latest_external.get('construction_opi_annual_pct', np.nan):.1f}%",
            help="ONS infrastructure Construction Output Price Index annual change.",
        )

    control_1, control_2, control_3 = st.columns(3)
    with control_1:
        bank_change = st.slider(
            "Bank Rate change",
            min_value=-3.0,
            max_value=3.0,
            value=0.0,
            step=0.25,
            format="%+.2f pp",
        )
        cost_change = st.slider(
            "Construction-cost shock",
            min_value=-20,
            max_value=30,
            value=0,
            step=5,
            format="%+d%%",
        )
    with control_2:
        policy_regime = st.segmented_control(
            "Policy environment",
            options=["Restrictive", "Neutral", "Supportive"],
            default="Neutral",
            width="stretch",
        )
        grid_delay = st.slider(
            "Additional grid delay",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.5,
            format="%.1f years",
        )
    with control_3:
        new_cfd = st.toggle(
            "Assume new CfD support",
            value=False,
            help="Adds a bounded positive stress adjustment only to projects without recorded CfD support.",
        )
        st.caption(
            "Early-stage and capital-intensive projects receive larger rate, cost and "
            "grid-delay sensitivities."
        )

    scenario = Scenario(
        bank_rate_change_pp=bank_change,
        construction_cost_change_pct=float(cost_change),
        policy_regime=policy_regime or "Neutral",
        grid_delay_years=grid_delay,
        new_cfd_support=new_cfd,
    )
    stressed = filtered.copy()
    for horizon in (2, 3, 5):
        stressed[f"scenario_prob_operational_{horizon}y"] = apply_scenario(
            stressed,
            f"prob_operational_{horizon}y",
            scenario,
        )
        stressed[f"scenario_expected_{horizon}y_mw"] = (
            stressed["capacity_mw"].fillna(0)
            * stressed[f"scenario_prob_operational_{horizon}y"]
        )

    scenario_capacity = pd.DataFrame(
        {
            "Horizon": ["2 years", "3 years", "5 years"],
            "Reference": [
                stressed[f"expected_capacity_{horizon}y_mw"].sum()
                for horizon in (2, 3, 5)
            ],
            "Scenario": [
                stressed[f"scenario_expected_{horizon}y_mw"].sum()
                for horizon in (2, 3, 5)
            ],
        }
    )
    base_3y = scenario_capacity.loc[1, "Reference"]
    scenario_3y = scenario_capacity.loc[1, "Scenario"]
    change_3y = scenario_3y - base_3y
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Reference 3-year capacity", f"{base_3y:,.0f} MW")
    with s2:
        st.metric(
            "Scenario 3-year capacity",
            f"{scenario_3y:,.0f} MW",
            delta=f"{change_3y:+,.0f} MW",
        )
    with s3:
        st.metric(
            "Scenario change",
            format_probability(change_3y / base_3y if base_3y else np.nan),
        )

    melted = scenario_capacity.melt(
        id_vars="Horizon",
        var_name="Forecast",
        value_name="Capacity (MW)",
    )
    fig = px.bar(
        melted,
        x="Horizon",
        y="Capacity (MW)",
        color="Forecast",
        barmode="group",
        title="Probability-weighted capacity under the selected scenario",
        color_discrete_map={"Reference": "#9FB8A8", "Scenario": "#0E6B4F"},
    )
    st.plotly_chart(style_chart(fig), width="stretch")
    st.caption(" · ".join(scenario_summary(scenario)))
    st.info(
        "The scenario layer adjusts log-odds using documented, bounded assumptions. "
        f"It is deliberately separated from the trained model because "
        f"{metrics.get('snapshots', 0)} REPD snapshots cannot identify reliable "
        "inflation or political effects."
    )

with history_tab:
    st.header("Historical project progression")
    history = panel.copy()
    if technology:
        history = history[history["technology"].isin(technology)]
    if region:
        history = history[history["region"].isin(region)]
    history = history[
        pd.to_numeric(history["capacity_mw"], errors="coerce").fillna(0)
        >= minimum_capacity
    ]
    stage_history = (
        history.groupby(["snapshot_date", "stage"], dropna=False)["capacity_mw"]
        .sum()
        .reset_index()
    )
    fig = px.area(
        stage_history,
        x="snapshot_date",
        y="capacity_mw",
        color="stage",
        labels={
            "snapshot_date": "Source snapshot",
            "capacity_mw": "Capacity represented in REPD (MW)",
            "stage": "Stage",
        },
        title="Capacity represented in each source snapshot",
    )
    st.plotly_chart(style_chart(fig, height=520), width="stretch")
    left, right = st.columns(2)
    with left:
        new_projects = (
            history.groupby("project_key")["snapshot_date"]
            .min()
            .reset_index()
            .assign(
                period=lambda frame: frame["snapshot_date"]
                .dt.to_period("Q")
                .dt.to_timestamp()
            )
            .groupby("period")
            .size()
            .rename("new_projects")
            .reset_index()
        )
        fig = px.bar(
            new_projects,
            x="period",
            y="new_projects",
            title="Projects first observed by quarter",
        )
        st.plotly_chart(style_chart(fig), width="stretch")
    with right:
        operational = history[history["stage"].eq("Operational")]
        first_operation = (
            operational.groupby("project_key")
            .agg(
                first_operational=("snapshot_date", "min"),
                capacity_mw=("capacity_mw", "last"),
            )
            .reset_index()
        )
        first_operation["period"] = (
            first_operation["first_operational"].dt.to_period("Q").dt.to_timestamp()
        )
        commissioned = (
            first_operation.groupby("period")["capacity_mw"].sum().reset_index()
        )
        fig = px.bar(
            commissioned,
            x="period",
            y="capacity_mw",
            title="Capacity first observed operational",
        )
        st.plotly_chart(style_chart(fig), width="stretch")
    st.warning(
        "REPD's minimum threshold fell from 1 MW to 150 kW in 2021. Project-count "
        "changes across that boundary are not directly comparable."
    )

with map_tab:
    st.header("Current pipeline map")
    map_data = filtered.copy()
    numeric_columns = [
        "latitude",
        "longitude",
        "capacity_mw",
        "prob_operational_3y",
    ]
    for column in numeric_columns:
        map_data[column] = pd.to_numeric(map_data[column], errors="coerce")
    map_data[numeric_columns] = map_data[numeric_columns].replace(
        [np.inf, -np.inf], np.nan
    )
    map_data = map_data.dropna(subset=numeric_columns)
    map_data = map_data[
        map_data["latitude"].between(49.0, 61.5)
        & map_data["longitude"].between(-9.5, 3.5)
        & map_data["capacity_mw"].ge(0)
    ].copy()
    if map_data.empty:
        st.info("No mapped projects are available for this view.")
    else:
        map_data["marker_size"] = map_data["capacity_mw"].clip(lower=0)
        map_data["3-year forecast"] = map_data["prob_operational_3y"].map(
            format_probability
        )
        fig = px.scatter_map(
            map_data,
            lat="latitude",
            lon="longitude",
            size="marker_size",
            size_max=34,
            color="prob_operational_3y",
            hover_name="site_name",
            hover_data={
                "technology": True,
                "region": True,
                "stage": True,
                "capacity_mw": ":,.1f",
                "3-year forecast": True,
                "latitude": False,
                "longitude": False,
                "prob_operational_3y": False,
                "marker_size": False,
            },
            color_continuous_scale="Viridis",
            range_color=(0, 1),
            zoom=4,
            height=700,
        )
        fig.update_layout(
            map_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(
            fig,
            width="stretch",
            config={"scrollZoom": True, "displaylogo": False},
        )

with trust_tab:
    st.header("Trust Centre")
    trust_1, trust_2, trust_3, trust_4 = st.columns(4)
    with trust_1:
        st.metric("Panel rows", f"{metrics.get('panel_rows', 0):,}")
    with trust_2:
        st.metric("Projects linked", f"{metrics.get('projects', 0):,}")
    with trust_3:
        st.metric("Survival intervals", f"{metrics.get('survival_training_rows', 0):,}")
    with trust_4:
        st.metric(
            "Release status",
            STATUS_LABELS.get(release_status, release_status),
        )

    st.subheader("Temporal holdout results")
    result_rows: list[dict] = []
    for horizon, values in metrics.get("models", {}).items():
        for candidate, scores in values.get("candidates", {}).items():
            result_rows.append(
                {
                    "Horizon": f"{horizon} years",
                    "Candidate": MODEL_LABELS.get(candidate, candidate),
                    "ROC-AUC": scores.get("roc_auc"),
                    "Average precision": scores.get("average_precision"),
                    "Brier score": scores.get("brier_score"),
                    "Mean prediction": scores.get("mean_prediction"),
                    "Observed rate": values.get("positive_rate_test"),
                    "Test rows": values.get("test_rows"),
                }
            )
    validation = pd.DataFrame(result_rows)
    st.dataframe(
        validation,
        width="stretch",
        hide_index=True,
        column_config={
            "ROC-AUC": st.column_config.NumberColumn(format="%.3f"),
            "Average precision": st.column_config.NumberColumn(format="%.3f"),
            "Brier score": st.column_config.NumberColumn(format="%.3f"),
            "Mean prediction": st.column_config.NumberColumn(format="percent"),
            "Observed rate": st.column_config.NumberColumn(format="percent"),
        },
    )
    st.caption(
        "Lower Brier score is better. ROC-AUC near 0.5 indicates random ranking. "
        "The model is not promoted merely because it is more complex."
    )

    horizon_choice = st.selectbox(
        "Calibration view",
        options=sorted(metrics.get("models", {}).keys(), key=int),
        format_func=lambda value: f"{value}-year horizon",
    )
    calibration = pd.DataFrame(
        metrics["models"][horizon_choice].get("calibration", [])
    )
    if not calibration.empty:
        fig = go.Figure()
        fig.add_scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect calibration",
            line=dict(dash="dash", color="#9AA69E"),
        )
        fig.add_scatter(
            x=calibration["mean_prediction"],
            y=calibration["observed_rate"],
            mode="lines+markers",
            name="Selected holdout candidate",
            marker=dict(
                size=np.maximum(np.sqrt(calibration["count"]) * 1.6, 7),
                color="#0E6B4F",
            ),
        )
        fig.update_layout(title="Reliability: predicted versus observed")
        fig.update_xaxes(title="Mean predicted probability", tickformat=".0%")
        fig.update_yaxes(title="Observed operation rate", tickformat=".0%")
        st.plotly_chart(style_chart(fig), width="stretch")

    st.subheader("Source-data quality")
    quality_1, quality_2, quality_3 = st.columns(3)
    with quality_1:
        st.metric(
            "Duplicate snapshot-project rows",
            f"{quality.get('duplicate_snapshot_project_rows', 0):,}",
        )
    with quality_2:
        st.metric(
            "Fallback-key rate",
            format_probability(quality.get("fallback_project_key_rate", 0)),
        )
    with quality_3:
        st.metric("Independent snapshots", f"{quality.get('snapshots', 0):,}")
    for issue in quality.get("issues", []):
        message = (
            f"**{issue.get('severity', '').title()} · {issue.get('check', '')}** — "
            f"{issue.get('impact', '')} Evidence: {issue.get('evidence')}."
        )
        if issue.get("severity") in {"critical", "high"}:
            st.warning(message)
        else:
            st.info(message)

    st.subheader("Official external context")
    source_columns = st.columns(3)
    for column, source in zip(
        source_columns,
        external_metadata.get("sources", [])[:3],
        strict=False,
    ):
        with column:
            st.markdown(
                '<div class="source-card">'
                f"<strong>{source.get('name', '')}</strong><br>"
                f"<small>{source.get('note', '')}</small><br><br>"
                f"<a href=\"{source.get('url', '#')}\">Open official source</a>"
                "</div>",
                unsafe_allow_html=True,
            )

    with st.expander("Methodology and limitations", expanded=False):
        st.markdown(
            """
            **Target.** The system estimates discrete annual time-to-operation hazard,
            then combines those hazards into two-, three- and five-year cumulative
            probabilities. Unresolved projects are right-censored instead of being
            labelled as failures.

            **Features.** Public information available at each snapshot includes capacity,
            stage, time in stage, stage changes, capacity revisions, planning and
            construction dates, CfD evidence, data completeness, developer track record,
            and technology–region track record.

            **Validation.** Test outcomes come only from fully observed historical
            cohorts. Projects in each test cohort are removed from the corresponding
            survival-training rows. Brier score, ROC-AUC, average precision and
            reliability bins are reported.

            **External conditions.** Bank Rate, CPI and infrastructure construction costs
            are displayed from official sources. They are used in an explicitly labelled
            scenario layer, not passed to the trained model while only 14 independent
            REPD snapshots exist.

            **Limitations.** Public data omit private finance, land, equipment contracts,
            detailed grid studies and confidential delivery information. Entity matching
            can be imperfect, and REPD coverage changed in 2021. Outputs are research and
            portfolio work, not investment advice.
            """
        )

    st.download_button(
        "Download filtered forecast data",
        data=filtered.to_csv(index=False),
        file_name="uk_renewable_project_forecasts.csv",
        mime="text/csv",
    )

render_portfolio_footer()
