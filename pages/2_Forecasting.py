from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PANEL_PATH = Path("data/processed/repd_panel.csv.gz")
FORECAST_PATH = Path("data/processed/latest_forecasts.csv.gz")
METRICS_PATH = Path("data/processed/model_metrics.json")
GITHUB_URL = "https://github.com/hj-nakamura421/uk-renewable-energy-dashboard"

st.markdown(
    """
    <style>
    .block-container {max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem;}
    #MainMenu, footer {visibility: hidden;}
    h1 {font-weight: 720; letter-spacing: -0.035em; line-height: 1.05;}
    h2, h3 {letter-spacing: -0.018em;}
    [data-testid="stMetric"] {
        background: white; border: 1px solid #e4e9e5; border-radius: 18px;
        padding: 1rem 1.1rem; box-shadow: 0 8px 24px rgba(10,40,25,.045);
    }
    [data-testid="stDataFrame"] {border: 1px solid #e4e9e5; border-radius: 16px; overflow: hidden;}
    .stTabs [data-baseweb="tab-list"] {
        gap: .35rem; background: white; border: 1px solid #e4e9e5;
        border-radius: 16px; padding: .4rem; position: sticky; top: .4rem; z-index: 50;
    }
    .stTabs [data-baseweb="tab"] {border-radius: 12px; padding: .55rem .85rem;}
    .stTabs [aria-selected="true"] {background: #17211c; color: white;}
    
    section[data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    .forecast-meta {
        display: flex;
        flex-wrap: wrap;
        gap: .65rem;
        margin: 1rem 0 .55rem;
    }
    .forecast-meta span {
        display: inline-flex;
        align-items: baseline;
        gap: .38rem;
        padding: .48rem .72rem;
        border: 1px solid #e1e7e2;
        border-radius: 999px;
        background: #f8faf8;
        color: #56615a;
        font-size: .92rem;
    }
    .forecast-meta strong {
        color: #17211c;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if not PANEL_PATH.exists() or not FORECAST_PATH.exists() or not METRICS_PATH.exists():
        raise FileNotFoundError(
            "Forecast files are missing. Run `python bootstrap.py` in Terminal first."
        )
    panel = pd.read_csv(PANEL_PATH, compression="gzip", low_memory=False)
    forecasts = pd.read_csv(FORECAST_PATH, compression="gzip", low_memory=False)
    for frame in (panel, forecasts):
        for column in (
            "snapshot_date", "planning_submitted", "planning_granted",
            "under_construction_date", "operational_date",
        ):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return panel, forecasts, metrics


def style_chart(figure: go.Figure, *, height: int = 430) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        font=dict(family="Arial, sans-serif", color="#17211c"),
        legend_title_text="",
    )
    figure.update_xaxes(gridcolor="#edf0ed", zeroline=False)
    figure.update_yaxes(gridcolor="#edf0ed", zeroline=False)
    return figure


def format_probability(value: float) -> str:
    return "N/A" if pd.isna(value) else f"{100 * value:.1f}%"


try:
    panel, forecasts, metrics = load_data()
except Exception as exc:  # noqa: BLE001
    st.error("The forecasting dataset has not been built yet.")
    st.code(str(exc))
    st.markdown(
        """
        Run these commands from the project folder:

        ```bash
        uv sync
        uv run python bootstrap.py
        uv run streamlit run app.py
        ```
        """
    )
    st.stop()

latest_snapshot = pd.Timestamp(forecasts["snapshot_date"].max())


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

with st.container(border=True):
    header_left, header_right = st.columns([1.8, 1])

    with header_left:
        st.title("UK Renewable Infrastructure Forecasting Platform")
        st.write(
            """
            Explore historical project progression, compare current development pipelines
            and estimate which UK renewable projects are most likely to become operational
            within two, three or five years.
            """
        )

        forecast_search = st.text_input(
            "Search projects",
            placeholder="Search project, developer, technology or region...",
            key="forecast_project_search",
        )

    with header_right:
        stat_col1, stat_col2 = st.columns(2)

        with stat_col1:
            st.metric("Projects modelled", f"{len(forecasts):,}")

        with stat_col2:
            st.metric("Forecast snapshot", latest_snapshot.strftime("%d %b %Y"))

        st.caption(
            f"Built from {panel['snapshot_date'].nunique():,} historical dataset snapshots. "
            "Forecasts are experimental probability estimates, not investment advice."
        )

capability_col1, capability_col2, capability_col3 = st.columns(3)

with capability_col1:
    st.markdown("**Historical Intelligence**")
    st.caption(
        "Track project-entry, stage-progression and operational-capacity trends over time."
    )

with capability_col2:
    st.markdown("**Project Forecasts**")
    st.caption(
        "Estimate individual projects' probability of operation within two, three or five years."
    )

with capability_col3:
    st.markdown("**Capacity Outlook**")
    st.caption(
        "Compare raw pipeline capacity with probability-weighted regional and technology forecasts."
    )


with st.expander("Advanced filters", expanded=False):
    filter_a, filter_b, filter_c, filter_d = st.columns(4)
    with filter_a:
        technology = st.multiselect(
            "Technology",
            sorted(forecasts["technology"].dropna().unique()),
        )
    with filter_b:
        region = st.multiselect("Region", sorted(forecasts["region"].dropna().unique()))
    with filter_c:
        stage = st.multiselect("Current stage", sorted(forecasts["stage"].dropna().unique()))
    with filter_d:
        minimum_capacity = st.number_input("Minimum capacity (MW)", min_value=0.0, value=0.0, step=10.0)

filtered = forecasts.copy()

# BEGIN FORECAST SEARCH FILTER
if forecast_search.strip():
    search_term = forecast_search.strip()
    searchable_columns = [
        column
        for column in ["site_name", "operator", "technology", "region", "stage"]
        if column in filtered.columns
    ]

    search_mask = pd.Series(False, index=filtered.index)

    for column in searchable_columns:
        search_mask = search_mask | filtered[column].astype(str).str.contains(
            search_term,
            case=False,
            na=False,
            regex=False,
        )

    filtered = filtered[search_mask]
# END FORECAST SEARCH FILTER
if technology:
    filtered = filtered[filtered["technology"].isin(technology)]
if region:
    filtered = filtered[filtered["region"].isin(region)]
if stage:
    filtered = filtered[filtered["stage"].isin(stage)]
filtered = filtered[filtered["capacity_mw"].fillna(0) >= minimum_capacity]

if filtered.empty:
    st.warning("No current projects match these filters.")
    st.stop()


# BEGIN FORECAST ACTIVE VIEW
active_filters = []

if forecast_search.strip():
    active_filters.append(f"Search: {forecast_search.strip()}")

if technology:
    technology_text = ", ".join(technology[:3])
    if len(technology) > 3:
        technology_text += "…"
    active_filters.append(f"Technology: {technology_text}")

if region:
    region_text = ", ".join(region[:3])
    if len(region) > 3:
        region_text += "…"
    active_filters.append(f"Region: {region_text}")

if stage:
    stage_text = ", ".join(stage[:3])
    if len(stage) > 3:
        stage_text += "…"
    active_filters.append(f"Stage: {stage_text}")

if minimum_capacity > 0:
    active_filters.append(f"Minimum capacity: {minimum_capacity:,.0f} MW")

if active_filters:
    st.caption("Active view · " + " · ".join(active_filters))
else:
    st.caption("Active view · All current projects")

st.subheader("Forecast")
# END FORECAST ACTIVE VIEW

(
    executive_tab,
    history_tab,
    project_tab,
    portfolio_tab,
    map_tab,
    validation_tab,
    method_tab,
) = st.tabs(
    [
        "Executive View",
        "Historical Trends",
        "Project Forecasts",
        "Capacity Forecast",
        "Map",
        "Model Validation",
        "Methodology",
    ]
)

with executive_tab:
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    with metric_1:
        st.metric("Active projects", f"{len(filtered):,}")
    with metric_2:
        st.metric("Pipeline capacity", f"{filtered['capacity_mw'].sum():,.0f} MW")
    with metric_3:
        expected_3y = filtered.get("expected_capacity_3y_mw", pd.Series(0, index=filtered.index)).sum()
        st.metric("Probability-weighted 3-year capacity", f"{expected_3y:,.0f} MW")
    with metric_4:
        high_confidence = filtered.get("prob_operational_3y", pd.Series(0, index=filtered.index)).ge(0.7).sum()
        st.metric("Projects above 70% (3-year)", f"{high_confidence:,}")

    st.subheader("Highest-probability current projects")
    top = filtered.sort_values(["prob_operational_3y", "capacity_mw"], ascending=False).head(20).copy()
    top["3-year probability"] = top["prob_operational_3y"].map(format_probability)
    top["5-year probability"] = top["prob_operational_5y"].map(format_probability)
    st.dataframe(
        top[
            [
                "site_name", "operator", "technology", "region", "stage", "capacity_mw",
                "3-year probability", "5-year probability",
            ]
        ].rename(
            columns={
                "site_name": "Project",
                "operator": "Developer / applicant",
                "technology": "Technology",
                "region": "Region",
                "stage": "Stage",
                "capacity_mw": "Capacity (MW)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    chart_left, chart_right = st.columns(2)
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
        fig = px.bar(region_forecast, x="expected_3y_mw", y="region", orientation="h")
        fig.update_xaxes(title="Probability-weighted capacity (MW)")
        fig.update_yaxes(title=None)
        st.plotly_chart(style_chart(fig), use_container_width=True, config={"displayModeBar": False})
    with chart_right:
        tech_forecast = (
            filtered.groupby("technology", dropna=False)["expected_capacity_3y_mw"]
            .sum()
            .reset_index()
            .sort_values("expected_capacity_3y_mw", ascending=False)
            .head(10)
        )
        fig = px.pie(tech_forecast, values="expected_capacity_3y_mw", names="technology", hole=0.55)
        st.plotly_chart(style_chart(fig), use_container_width=True, config={"displayModeBar": False})

with history_tab:
    st.header("Historical project progression")
    history = panel.copy()
    if technology:
        history = history[history["technology"].isin(technology)]
    if region:
        history = history[history["region"].isin(region)]
    history = history[history["capacity_mw"].fillna(0) >= minimum_capacity]

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
        labels={"snapshot_date": "Snapshot", "capacity_mw": "Capacity in database (MW)", "stage": "Stage"},
    )
    st.plotly_chart(style_chart(fig, height=500), use_container_width=True)

    history_left, history_right = st.columns(2)
    with history_left:
        new_projects = (
            history.groupby("project_key")["snapshot_date"].min().reset_index()
            .assign(period=lambda frame: frame["snapshot_date"].dt.to_period("Q").dt.to_timestamp())
            .groupby("period").size().rename("new_projects").reset_index()
        )
        fig = px.bar(new_projects, x="period", y="new_projects")
        fig.update_xaxes(title="Quarter first observed")
        fig.update_yaxes(title="New projects")
        st.plotly_chart(style_chart(fig), use_container_width=True, config={"displayModeBar": False})
    with history_right:
        operational = history[history["stage"].eq("Operational")]
        first_operation = (
            operational.groupby("project_key").agg(
                first_operational=("snapshot_date", "min"),
                capacity_mw=("capacity_mw", "last"),
            ).reset_index()
        )
        first_operation["period"] = first_operation["first_operational"].dt.to_period("Q").dt.to_timestamp()
        commissioned = first_operation.groupby("period")["capacity_mw"].sum().reset_index()
        fig = px.bar(commissioned, x="period", y="capacity_mw")
        fig.update_xaxes(title="Quarter first observed operational")
        fig.update_yaxes(title="Capacity reaching operation (MW)")
        st.plotly_chart(style_chart(fig), use_container_width=True, config={"displayModeBar": False})

    st.info(
        "The REPD threshold fell from 1 MW to 150 kW in 2021. Treat apparent changes in small-project "
        "counts across that boundary cautiously."
    )

with project_tab:
    st.header("Project-level forecasts")
    project_names = sorted(filtered["site_name"].fillna("Unnamed project").unique())
    selected_name = st.selectbox("Select a current project", project_names)
    selected = filtered[filtered["site_name"].eq(selected_name)].sort_values("capacity_mw", ascending=False).iloc[0]

    a, b, c, d = st.columns(4)
    with a:
        st.metric("Capacity", f"{selected['capacity_mw']:,.1f} MW")
    with b:
        st.metric("2-year probability", format_probability(selected.get("prob_operational_2y", np.nan)))
    with c:
        st.metric("3-year probability", format_probability(selected.get("prob_operational_3y", np.nan)))
    with d:
        st.metric("5-year probability", format_probability(selected.get("prob_operational_5y", np.nan)))

    details = pd.DataFrame(
        {
            "Field": ["Developer / applicant", "Technology", "Region", "Country", "Current stage", "Planning authority"],
            "Value": [
                selected.get("operator", ""), selected.get("technology", ""), selected.get("region", ""),
                selected.get("country", ""), selected.get("stage", ""), selected.get("planning_authority", ""),
            ],
        }
    )
    st.dataframe(details, use_container_width=True, hide_index=True)

    project_history = panel[panel["project_key"].eq(selected["project_key"])].sort_values("snapshot_date")
    if not project_history.empty:
        timeline = project_history[["snapshot_date", "stage", "capacity_mw", "status_short"]].drop_duplicates()
        st.subheader("Observed project history")
        st.dataframe(timeline, use_container_width=True, hide_index=True)

    st.caption(
        "The model estimates progression from patterns in earlier REPD snapshots. It does not know private "
        "financing terms, detailed grid constraints or confidential developer information."
    )

with portfolio_tab:
    st.header("Probability-weighted capacity forecast")
    horizon = st.radio("Forecast horizon", [2, 3, 5], index=1, horizontal=True)
    probability_column = f"prob_operational_{horizon}y"
    expected_column = f"expected_capacity_{horizon}y_mw"

    grouping = st.radio("Group by", ["Region", "Technology"], horizontal=True)
    group_column = "region" if grouping == "Region" else "technology"
    aggregate = (
        filtered.groupby(group_column, dropna=False)
        .agg(
            projects=("project_key", "nunique"),
            pipeline_capacity_mw=("capacity_mw", "sum"),
            expected_capacity_mw=(expected_column, "sum"),
            mean_probability=(probability_column, "mean"),
        )
        .reset_index()
        .sort_values("expected_capacity_mw", ascending=False)
    )
    aggregate["conversion_ratio"] = aggregate["expected_capacity_mw"] / aggregate["pipeline_capacity_mw"].replace(0, np.nan)

    chart_data = aggregate.head(15).sort_values("expected_capacity_mw")
    fig = go.Figure()
    fig.add_bar(
        y=chart_data[group_column],
        x=chart_data["pipeline_capacity_mw"],
        name="Raw pipeline",
        orientation="h",
    )
    fig.add_bar(
        y=chart_data[group_column],
        x=chart_data["expected_capacity_mw"],
        name="Probability-weighted",
        orientation="h",
    )
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Capacity (MW)")
    fig.update_yaxes(title=None)
    st.plotly_chart(style_chart(fig, height=540), use_container_width=True)

    display = aggregate.copy()
    display["Mean probability"] = display["mean_probability"].map(format_probability)
    display["Expected / pipeline"] = display["conversion_ratio"].map(format_probability)
    st.dataframe(
        display[
            [group_column, "projects", "pipeline_capacity_mw", "expected_capacity_mw", "Mean probability", "Expected / pipeline"]
        ].rename(
            columns={
                group_column: grouping,
                "projects": "Projects",
                "pipeline_capacity_mw": "Pipeline capacity (MW)",
                "expected_capacity_mw": f"Expected within {horizon} years (MW)",
            }
        ),
        use_container_width=True,
        hide_index=True,
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
        [np.inf, -np.inf],
        np.nan,
    )

    map_data = map_data.dropna(subset=numeric_columns).copy()
    map_data = map_data[
        map_data["latitude"].between(49.0, 61.5)
        & map_data["longitude"].between(-9.5, 3.5)
        & map_data["capacity_mw"].ge(0)
    ].copy()

    if map_data.empty:
        st.info(
            "No projects with valid coordinates, capacity and forecast values "
            "are available for these filters."
        )
    else:
        map_data["marker_size"] = map_data["capacity_mw"].clip(lower=0)
        map_data["3-year probability"] = map_data[
            "prob_operational_3y"
        ].map(format_probability)

        fig = px.scatter_map(
            map_data,
            lat="latitude",
            lon="longitude",
            size="marker_size",
            size_max=35,
            color="prob_operational_3y",
            hover_name="site_name",
            hover_data={
                "technology": True,
                "region": True,
                "stage": True,
                "capacity_mw": ":,.1f",
                "3-year probability": True,
                "latitude": False,
                "longitude": False,
                "prob_operational_3y": False,
                "marker_size": False,
            },
            color_continuous_scale="Viridis",
            range_color=(0, 1),
            zoom=4,
            height=680,
        )
        fig.update_layout(
            map_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"scrollZoom": True, "displaylogo": False},
        )

with validation_tab:
    st.header("Time-based model validation")
    model_rows: list[dict] = []
    for horizon, values in metrics.get("models", {}).items():
        model_rows.append(
            {
                "Horizon": f"{horizon} years",
                "Training rows": values.get("train_rows"),
                "Test rows": values.get("test_rows"),
                "Training ends": values.get("train_end"),
                "Testing starts": values.get("test_start"),
                "ROC-AUC": values.get("roc_auc"),
                "Brier score": values.get("brier_score"),
                "Precision": values.get("precision"),
                "Recall": values.get("recall"),
            }
        )
    validation = pd.DataFrame(model_rows)
    st.dataframe(validation, use_container_width=True, hide_index=True)

    selected_horizon = st.selectbox("Calibration chart", sorted(metrics.get("models", {}).keys(), key=int))
    calibration = pd.DataFrame(metrics["models"][selected_horizon].get("calibration", []))
    if not calibration.empty:
        fig = go.Figure()
        fig.add_scatter(
            x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration", line=dict(dash="dash")
        )
        fig.add_scatter(
            x=calibration["mean_prediction"],
            y=calibration["observed_rate"],
            mode="lines+markers",
            name="Model",
            marker=dict(size=np.sqrt(calibration["count"]) * 2),
        )
        fig.update_xaxes(title="Mean predicted probability", range=[0, 1])
        fig.update_yaxes(title="Observed operation rate", range=[0, 1])
        st.plotly_chart(style_chart(fig), use_container_width=True)

    st.warning(
        "A good-looking probability is not enough. Use the time split, calibration curve and technology-level "
        "error analysis before presenting the forecasts as decision-grade evidence."
    )

with method_tab:
    st.header("Methodology and limitations")
    st.markdown(
        """
        ### What the model predicts
        Each baseline logistic-regression model estimates whether a currently non-operational project will first
        appear as operational within a fixed **2-, 3- or 5-year horizon**.

        ### Historical construction
        Official REPD snapshots are standardised into a project–snapshot panel. Reference IDs and revised-application
        links are used to join records over time. Each row contains only information visible at that snapshot.

        ### Features
        - technology, region, country and current stage
        - installed capacity and project age
        - planning-reference availability and planning/consent/construction indicators
        - data-completeness score and CfD indicator where present

        ### Back-testing
        Training uses earlier snapshots and testing uses later snapshots. This reduces the risk of accidentally
        training on information that would not have been available at the forecast date.

        ### Important limitations
        - REPD's minimum threshold changed from 1 MW to 150 kW in 2021.
        - Historical field names and status definitions have changed.
        - The model does not include private financing, detailed grid constraints, land agreements or supply-chain risk.
        - Probability-weighted capacity is an expectation, not a promise that individual projects will be built.
        - These outputs are research and portfolio work, not investment advice.
        """
    )

from shared_ui import render_portfolio_footer

render_portfolio_footer()
