from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pyproj import Transformer

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Renewable Project Screening Studio",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------
# PATHS / LINKS
# ---------------------------------------------------

DATA_PATH = Path("data/renewable_projects.csv")
GITHUB_URL = "https://github.com/hj-nakamura421/uk-renewable-energy-dashboard"

# ---------------------------------------------------
# CSS
# ---------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        padding-left: 2.7rem;
        padding-right: 2.7rem;
        max-width: none;
        width: 100%;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                     "SF Pro Text", "Inter", "Segoe UI", sans-serif;
    }

    h1 {
        font-size: clamp(2.1rem, 3.4vw, 3.35rem);
        line-height: 1.12;
        font-weight: 680;
        letter-spacing: 0.005em;
        word-spacing: 0.08em;
        color: #111111;
        margin-bottom: 0.7rem;
        max-width: 1050px;
    }

    h2 {
        font-size: clamp(1.45rem, 2.1vw, 1.95rem);
        line-height: 1.16;
        font-weight: 650;
        color: #111111;
        margin-top: 2rem;
        margin-bottom: 0.8rem;
    }

    h3 {
        font-size: 1.1rem;
        font-weight: 610;
        color: #111111;
    }

    p, li {
        color: #3A3A3C;
        font-size: 1rem;
        line-height: 1.6;
    }

    .stMarkdown p {
        max-width: 980px;
    }

    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E7E7E2;
        padding: 1rem 1.1rem;
        border-radius: 1.05rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.035);
    }

    [data-testid="stMetricLabel"] {
        color: #737373;
        font-size: 0.82rem;
        font-weight: 520;
    }

    [data-testid="stMetricValue"] {
        color: #111111;
        font-size: 1.28rem;
        font-weight: 650;
        letter-spacing: -0.005em;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 1rem;
        overflow: hidden;
        border: 1px solid #E7E7E2;
    }

    div[data-testid="stDownloadButton"] button,
    div[data-testid="stLinkButton"] a {
        border-radius: 999px !important;
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border: 1px solid #111111 !important;
        font-weight: 650 !important;
        padding: 0.55rem 1.15rem !important;
    }

    div[data-testid="stDownloadButton"] button *,
    div[data-testid="stLinkButton"] a * {
        color: #FFFFFF !important;
    }

    div[data-testid="stDownloadButton"] button:hover,
    div[data-testid="stLinkButton"] a:hover {
        background-color: #303030 !important;
        border-color: #303030 !important;
        color: #FFFFFF !important;
    }

    .stAlert {
        border-radius: 1rem;
        border: 1px solid #E7E7E2;
    }

    section[data-testid="stSidebar"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.45rem;
        background: #FFFFFF;
        border: 1px solid #E2E2DD;
        border-radius: 999px;
        padding: 0.42rem;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.04);
        margin-top: 0.75rem;
        margin-bottom: 1.45rem;
        flex-wrap: wrap;
        position: sticky;
        top: 0.6rem;
        z-index: 20;
    }

    .stTabs [data-baseweb="tab"] {
        height: 2.75rem;
        border-radius: 999px;
        padding: 0.45rem 0.95rem;
        font-size: 0.94rem;
        font-weight: 650;
        color: #555555;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] p {
        font-size: 0.94rem;
        font-weight: 650;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #111111;
        color: #FFFFFF;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] p {
        color: #FFFFFF;
    }

    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    details {
        border-radius: 1rem !important;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        h1 {
            word-spacing: 0.03em;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------


@st.cache_data
def load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH, encoding="latin1")

    data["Installed Capacity (MWelec)"] = pd.to_numeric(
        data["Installed Capacity (MWelec)"],
        errors="coerce",
    )

    data = data.dropna(subset=["Installed Capacity (MWelec)"])

    data["X-coordinate"] = pd.to_numeric(
        data["X-coordinate"],
        errors="coerce",
    )

    data["Y-coordinate"] = pd.to_numeric(
        data["Y-coordinate"],
        errors="coerce",
    )

    transformer = Transformer.from_crs(
        "EPSG:27700",
        "EPSG:4326",
        always_xy=True,
    )

    valid_coords = data["X-coordinate"].notna() & data["Y-coordinate"].notna()

    data.loc[valid_coords, "Longitude"], data.loc[valid_coords, "Latitude"] = (
        transformer.transform(
            data.loc[valid_coords, "X-coordinate"].values,
            data.loc[valid_coords, "Y-coordinate"].values,
        )
    )

    if "Record Last Updated (dd/mm/yyyy)" in data.columns:
        data["Record Last Updated Parsed"] = pd.to_datetime(
            data["Record Last Updated (dd/mm/yyyy)"],
            dayfirst=True,
            errors="coerce",
        )

    return data


def calculate_screening_score(row: pd.Series) -> int:
    score = 0

    capacity = row.get("Installed Capacity (MWelec)", 0)
    status = str(row.get("Development Status (short)", "")).lower()
    technology = str(row.get("Technology Type", "")).lower()

    if capacity >= 1000:
        score += 35
    elif capacity >= 500:
        score += 28
    elif capacity >= 100:
        score += 20
    elif capacity >= 20:
        score += 12
    else:
        score += 5

    if "operational" in status:
        score += 35
    elif "construction" in status:
        score += 30
    elif "planning granted" in status:
        score += 25
    elif "planning" in status:
        score += 15
    else:
        score += 8

    if "wind offshore" in technology:
        score += 20
    elif "battery" in technology or "storage" in technology:
        score += 18
    elif "solar" in technology:
        score += 15
    elif "wind onshore" in technology:
        score += 15
    else:
        score += 10

    useful_fields = [
        "Operator (or Applicant)",
        "Region",
        "County",
        "Planning Authority",
        "Planning Application Reference",
    ]

    completed_fields = sum(
        pd.notna(row.get(field)) and str(row.get(field)).strip() != ""
        for field in useful_fields
    )

    score += min(10, completed_fields * 2)

    return min(score, 100)


def polish_chart(fig, height=420):
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
            color="#111111",
        ),
        title=None,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        hovermode="closest",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#EFEFEA",
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
    )

    return fig


def top_capacity_table(
    data: pd.DataFrame,
    group_col: str,
    value_col: str = "Installed Capacity (MWelec)",
    n: int = 10,
) -> pd.DataFrame:
    return (
        data.groupby(group_col)[value_col]
        .sum()
        .reset_index()
        .sort_values(value_col, ascending=False)
        .head(n)
    )


def safe_filename(name: str) -> str:
    return (
        name.replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
        .replace(":", "-")
    )


def apply_search(data: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query.strip():
        return data

    searchable_columns = [
        "Site Name",
        "Operator (or Applicant)",
        "Technology Type",
        "Development Status (short)",
        "Region",
        "County",
        "Planning Authority",
        "Planning Application Reference",
    ]

    available_columns = [col for col in searchable_columns if col in data.columns]

    search_text = (
        data[available_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
    )

    return data[search_text.str.contains(query.lower(), na=False)].copy()


# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

try:
    df = load_data()
except Exception as e:
    st.error("Error loading dataset.")
    st.code(str(e))
    st.stop()

latest_dataset_update_text = "N/A"

if "Record Last Updated Parsed" in df.columns:
    latest_dataset_update = df["Record Last Updated Parsed"].max()
    if pd.notna(latest_dataset_update):
        latest_dataset_update_text = latest_dataset_update.strftime("%d %b %Y")

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------

with st.container(border=True):
    header_left, header_right = st.columns([1.8, 1])

    with header_left:
        st.title("UK Renewable Project Screening Dashboard")
        st.write(
            """
            An interactive UK renewable energy dashboard for exploring renewable energy planning data,
            screening infrastructure projects, mapping project locations, comparing regional capacity
            and modelling offshore wind feasibility.
            """
        )

    with header_right:
        search_query = st.text_input(
            "Search projects",
            placeholder="Search Dogger Bank, solar, Scotland, battery...",
        )

        stat_col1, stat_col2 = st.columns(2)

        with stat_col1:
            st.metric("Dataset records", f"{len(df):,}")

        with stat_col2:
            st.metric("Latest update", latest_dataset_update_text)

# ---------------------------------------------------
# FILTERS
# ---------------------------------------------------

technology_options = sorted(df["Technology Type"].dropna().unique())
status_options = sorted(df["Development Status (short)"].dropna().unique())
region_options = sorted(df["Region"].dropna().unique())

with st.expander("Advanced filters", expanded=False):
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        selected_technology = st.selectbox(
            "Technology",
            ["All"] + technology_options,
            index=0,
            help="Choose one technology, or leave as All.",
        )

    with filter_col2:
        selected_status = st.selectbox(
            "Development stage",
            ["All"] + status_options,
            index=0,
            help="Choose one project stage, or leave as All.",
        )

    with filter_col3:
        selected_region = st.selectbox(
            "Region",
            ["All"] + region_options,
            index=0,
            help="Choose one UK region, or leave as All.",
        )

# ---------------------------------------------------
# APPLY SEARCH AND FILTERS
# ---------------------------------------------------

filtered_df = apply_search(df.copy(), search_query)

if selected_technology != "All":
    filtered_df = filtered_df[
        filtered_df["Technology Type"] == selected_technology
    ]

if selected_status != "All":
    filtered_df = filtered_df[
        filtered_df["Development Status (short)"] == selected_status
    ]

if selected_region != "All":
    filtered_df = filtered_df[
        filtered_df["Region"] == selected_region
    ]

if filtered_df.empty:
    st.warning(
        "No projects match the current search and filters. Try clearing the search or choosing All in the filters."
    )
    st.stop()

filtered_df["Screening Score"] = filtered_df.apply(
    calculate_screening_score,
    axis=1,
)

active_filters = []

if search_query.strip():
    active_filters.append(f"Search: {search_query.strip()}")

if selected_technology != "All":
    active_filters.append(f"Technology: {selected_technology}")

if selected_status != "All":
    active_filters.append(f"Stage: {selected_status}")

if selected_region != "All":
    active_filters.append(f"Region: {selected_region}")

if active_filters:
    st.caption("Active view · " + " · ".join(active_filters))
else:
    st.caption("Active view · All projects")

# ---------------------------------------------------
# SUMMARY VALUES
# ---------------------------------------------------

total_capacity = filtered_df["Installed Capacity (MWelec)"].sum()
avg_capacity = filtered_df["Installed Capacity (MWelec)"].mean()

latest_update_text = "N/A"

if "Record Last Updated Parsed" in filtered_df.columns:
    latest_update = filtered_df["Record Last Updated Parsed"].max()

    if pd.notna(latest_update):
        latest_update_text = latest_update.strftime("%d %b %Y")

largest_project_row = filtered_df.sort_values(
    "Installed Capacity (MWelec)",
    ascending=False,
).iloc[0]

largest_project_name = largest_project_row["Site Name"]
largest_project_capacity = largest_project_row["Installed Capacity (MWelec)"]

largest_tech = (
    filtered_df.groupby("Technology Type")["Installed Capacity (MWelec)"]
    .sum()
    .idxmax()
)

largest_region = (
    filtered_df.groupby("Region")["Installed Capacity (MWelec)"]
    .sum()
    .idxmax()
)

top_10_capacity = (
    filtered_df.sort_values(
        "Installed Capacity (MWelec)",
        ascending=False,
    )
    .head(10)["Installed Capacity (MWelec)"]
    .sum()
)

top_10_share = top_10_capacity / total_capacity * 100 if total_capacity else 0

# ---------------------------------------------------
# NAVIGATION
# ---------------------------------------------------

st.subheader("Explore")

overview_tab, pipeline_tab, map_tab, briefs_tab, offshore_tab, methodology_tab = st.tabs(
    [
        "Overview",
        "Pipeline",
        "Map",
        "Briefs",
        "Offshore Model",
        "Methodology",
    ]
)

# ---------------------------------------------------
# OVERVIEW
# ---------------------------------------------------

with overview_tab:
    st.header("Overview")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        st.metric("Projects", f"{len(filtered_df):,}")

    with metric_col2:
        st.metric("Total Capacity", f"{total_capacity:,.0f} MW")

    with metric_col3:
        st.metric("Average Capacity", f"{avg_capacity:,.1f} MW")

    with metric_col4:
        st.metric("Latest Update", latest_update_text)

    st.subheader("Key insights")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.metric("Leading technology", largest_tech)

    with insight_col2:
        st.metric("Leading region", largest_region)

    with insight_col3:
        st.metric("Top 10 share", f"{top_10_share:,.1f}%")

    st.write(
        f"""
        The largest project under the current view is **{largest_project_name}**
        at **{largest_project_capacity:,.0f} MW**.
        """
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Top technologies")

        tech_capacity = top_capacity_table(filtered_df, "Technology Type", n=8)
        tech_capacity = tech_capacity.sort_values(
            "Installed Capacity (MWelec)",
            ascending=True,
        )

        fig_tech = px.bar(
            tech_capacity,
            x="Installed Capacity (MWelec)",
            y="Technology Type",
            orientation="h",
            labels={
                "Installed Capacity (MWelec)": "Capacity (MW)",
                "Technology Type": "",
            },
        )

        st.plotly_chart(
            polish_chart(fig_tech, height=390),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with chart_col2:
        st.subheader("Top regions")

        region_capacity = top_capacity_table(filtered_df, "Region", n=8)
        region_capacity = region_capacity.sort_values(
            "Installed Capacity (MWelec)",
            ascending=True,
        )

        fig_region = px.bar(
            region_capacity,
            x="Installed Capacity (MWelec)",
            y="Region",
            orientation="h",
            labels={
                "Installed Capacity (MWelec)": "Capacity (MW)",
                "Region": "",
            },
        )

        st.plotly_chart(
            polish_chart(fig_region, height=390),
            use_container_width=True,
            config={"displayModeBar": False},
        )

# ---------------------------------------------------
# PIPELINE
# ---------------------------------------------------

with pipeline_tab:
    st.header("Project pipeline")

    st.write(
        """
        A filtered view of the project universe. The table shows a readable preview;
        the full filtered dataset can be downloaded.
        """
    )

    display_columns = [
        "Site Name",
        "Operator (or Applicant)",
        "Technology Type",
        "Installed Capacity (MWelec)",
        "Development Status (short)",
        "Region",
        "County",
        "Planning Authority",
        "Screening Score",
    ]

    available_display_columns = [
        col for col in display_columns if col in filtered_df.columns
    ]

    st.dataframe(
        filtered_df[available_display_columns].head(250),
        use_container_width=True,
    )

    st.caption(
        "Showing first 250 filtered rows for readability. Download the CSV for the full filtered dataset."
    )

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered data",
        data=csv,
        file_name="filtered_renewable_projects.csv",
        mime="text/csv",
    )

    st.subheader("Major projects")

    top_projects = (
        filtered_df.sort_values(
            "Installed Capacity (MWelec)",
            ascending=False,
        )
        [
            [
                "Site Name",
                "Technology Type",
                "Installed Capacity (MWelec)",
                "Region",
                "Development Status (short)",
                "Screening Score",
            ]
        ]
        .head(10)
    )

    st.dataframe(top_projects, use_container_width=True)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Capacity by stage")

        status_capacity = top_capacity_table(
            filtered_df,
            "Development Status (short)",
            n=10,
        )

        status_capacity = status_capacity.sort_values(
            "Installed Capacity (MWelec)",
            ascending=True,
        )

        fig_status = px.bar(
            status_capacity,
            x="Installed Capacity (MWelec)",
            y="Development Status (short)",
            orientation="h",
            labels={
                "Installed Capacity (MWelec)": "Capacity (MW)",
                "Development Status (short)": "",
            },
        )

        st.plotly_chart(
            polish_chart(fig_status, height=420),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with chart_col2:
        st.subheader("Technology by stage")

        top_technology_list = (
            filtered_df.groupby("Technology Type")["Installed Capacity (MWelec)"]
            .sum()
            .sort_values(ascending=False)
            .head(6)
            .index
            .tolist()
        )

        pipeline_matrix = (
            filtered_df[filtered_df["Technology Type"].isin(top_technology_list)]
            .groupby(["Technology Type", "Development Status (short)"])
            ["Installed Capacity (MWelec)"]
            .sum()
            .reset_index()
        )

        fig_pipeline = px.bar(
            pipeline_matrix,
            x="Installed Capacity (MWelec)",
            y="Technology Type",
            color="Development Status (short)",
            orientation="h",
            labels={
                "Installed Capacity (MWelec)": "Capacity (MW)",
                "Technology Type": "",
                "Development Status (short)": "Stage",
            },
        )

        st.plotly_chart(
            polish_chart(fig_pipeline, height=420),
            use_container_width=True,
            config={"displayModeBar": False},
        )

# ---------------------------------------------------
# MAP
# ---------------------------------------------------

with map_tab:
    st.header("Map")

    st.write("Use your mouse wheel or trackpad to zoom. Drag the map to move around.")

    map_df = filtered_df.dropna(subset=["Latitude", "Longitude"]).copy()

    if map_df.empty:
        st.warning("No valid coordinates are available for the current filters.")

    else:
        fig_map = px.scatter_mapbox(
            map_df,
            lat="Latitude",
            lon="Longitude",
            size="Installed Capacity (MWelec)",
            color="Technology Type",
            hover_name="Site Name",
            hover_data=[
                "Technology Type",
                "Installed Capacity (MWelec)",
                "Region",
                "Development Status (short)",
                "Screening Score",
            ],
            zoom=4,
            height=680,
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            dragmode="pan",
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": [
                    "lasso2d",
                    "select2d",
                ],
            },
        )

# ---------------------------------------------------
# BRIEFS
# ---------------------------------------------------

with briefs_tab:
    st.header("Project briefs")

    project_options = sorted(filtered_df["Site Name"].dropna().unique())

    selected_report_project = st.selectbox(
        "Select a project",
        project_options,
        key="project_report_selector",
    )

    report_row = filtered_df[
        filtered_df["Site Name"] == selected_report_project
    ].iloc[0]

    st.subheader(selected_report_project)

    report_col1, report_col2, report_col3, report_col4 = st.columns(4)

    with report_col1:
        st.metric("Technology", report_row.get("Technology Type", "N/A"))

    with report_col2:
        st.metric(
            "Capacity",
            f"{report_row.get('Installed Capacity (MWelec)', 0):,.1f} MW",
        )

    with report_col3:
        st.metric("Status", report_row.get("Development Status (short)", "N/A"))

    with report_col4:
        st.metric(
            "Screening Score",
            f"{report_row.get('Screening Score', 0):.0f}/100",
        )

    st.subheader("Project details")

    project_details = pd.DataFrame(
        {
            "Field": [
                "Operator / Applicant",
                "Region",
                "County",
                "Country",
                "Planning Authority",
                "Planning Application Reference",
                "Planning Submitted",
                "Planning Granted",
                "Operational Date",
            ],
            "Value": [
                report_row.get("Operator (or Applicant)", "N/A"),
                report_row.get("Region", "N/A"),
                report_row.get("County", "N/A"),
                report_row.get("Country", "N/A"),
                report_row.get("Planning Authority", "N/A"),
                report_row.get("Planning Application Reference", "N/A"),
                report_row.get("Planning Application Submitted", "N/A"),
                report_row.get("Planning Permission  Granted", "N/A"),
                report_row.get("Operational", "N/A"),
            ],
        }
    )

    st.table(project_details)

    st.subheader("Comparable projects")

    selected_technology_for_report = report_row.get("Technology Type", "")
    selected_capacity = report_row.get("Installed Capacity (MWelec)", 0)

    lower_bound = selected_capacity * 0.7
    upper_bound = selected_capacity * 1.3

    comparable_projects = filtered_df[
        (filtered_df["Technology Type"] == selected_technology_for_report)
        & (filtered_df["Installed Capacity (MWelec)"] >= lower_bound)
        & (filtered_df["Installed Capacity (MWelec)"] <= upper_bound)
        & (filtered_df["Site Name"] != selected_report_project)
    ].sort_values(
        "Installed Capacity (MWelec)",
        ascending=False,
    ).head(5)

    if comparable_projects.empty:
        st.write("No close comparable projects found under the current filters.")
    else:
        st.dataframe(
            comparable_projects[
                [
                    "Site Name",
                    "Technology Type",
                    "Installed Capacity (MWelec)",
                    "Region",
                    "Development Status (short)",
                    "Screening Score",
                ]
            ],
            use_container_width=True,
        )

    report_text = f"""
Renewable Project Brief
=======================

Project: {selected_report_project}

1. Project Overview
-------------------
Technology: {report_row.get("Technology Type", "N/A")}
Installed Capacity: {report_row.get("Installed Capacity (MWelec)", "N/A")} MW
Development Status: {report_row.get("Development Status (short)", "N/A")}
Screening Score: {report_row.get("Screening Score", "N/A")}/100

2. Developer and Location
-------------------------
Operator / Applicant: {report_row.get("Operator (or Applicant)", "N/A")}
Region: {report_row.get("Region", "N/A")}
County: {report_row.get("County", "N/A")}
Country: {report_row.get("Country", "N/A")}

3. Planning Information
-----------------------
Planning Authority: {report_row.get("Planning Authority", "N/A")}
Planning Application Reference: {report_row.get("Planning Application Reference", "N/A")}
Planning Submitted: {report_row.get("Planning Application Submitted", "N/A")}
Planning Granted: {report_row.get("Planning Permission  Granted", "N/A")}
Operational Date: {report_row.get("Operational", "N/A")}

4. Interpretation
-----------------
This brief provides an early-stage screening summary based on public project data.
The screening score is a simplified indicator based on capacity, development stage,
technology type and data completeness.

Generated using the Renewable Project Screening Studio.
"""

    st.download_button(
        label="Download project brief",
        data=report_text,
        file_name=f"{safe_filename(selected_report_project)}_project_brief.txt",
        mime="text/plain",
    )

# ---------------------------------------------------
# OFFSHORE MODEL
# ---------------------------------------------------

with offshore_tab:
    st.header("Offshore wind model")

    offshore_df = filtered_df[
        filtered_df["Technology Type"].str.contains(
            "Wind Offshore",
            case=False,
            na=False,
        )
    ].copy()

    if offshore_df.empty:
        st.warning(
            "No offshore wind projects are visible under the current filters."
        )

    else:
        project_names = sorted(offshore_df["Site Name"].dropna().unique())

        selected_project = st.selectbox(
            "Select an offshore wind project",
            project_names,
            key="offshore_project_selector",
        )

        project_row = offshore_df[
            offshore_df["Site Name"] == selected_project
        ].iloc[0]

        project_capacity = project_row["Installed Capacity (MWelec)"]

        selected_col1, selected_col2, selected_col3 = st.columns(3)

        with selected_col1:
            st.metric("Project", selected_project)

        with selected_col2:
            st.metric("Capacity", f"{project_capacity:,.0f} MW")

        with selected_col3:
            st.metric("Region", project_row.get("Region", "N/A"))

        st.subheader("Assumptions")

        ass_col1, ass_col2, ass_col3 = st.columns(3)

        with ass_col1:
            capacity_factor = st.slider(
                "Capacity factor",
                min_value=0.20,
                max_value=0.70,
                value=0.45,
                step=0.01,
            )

        with ass_col2:
            turbine_rating = st.slider(
                "Turbine rating (MW)",
                min_value=5.0,
                max_value=25.0,
                value=15.0,
                step=0.5,
            )

        with ass_col3:
            electricity_price = st.slider(
                "Electricity price (£/MWh)",
                min_value=20,
                max_value=200,
                value=70,
                step=5,
            )

        ass_col4, ass_col5, ass_col6 = st.columns(3)

        with ass_col4:
            capex_per_mw = st.slider(
                "CAPEX (£ million per MW)",
                min_value=1.0,
                max_value=8.0,
                value=3.0,
                step=0.1,
            )

        with ass_col5:
            lifetime = st.slider(
                "Project lifetime (years)",
                min_value=10,
                max_value=40,
                value=25,
                step=1,
            )

        with ass_col6:
            grid_carbon_intensity = st.slider(
                "Displaced grid carbon intensity (kg CO₂e/kWh)",
                min_value=0.00,
                max_value=0.60,
                value=0.20,
                step=0.01,
            )

        annual_energy_mwh = project_capacity * capacity_factor * 8760
        number_of_turbines = project_capacity / turbine_rating
        annual_revenue = annual_energy_mwh * electricity_price
        total_capex = project_capacity * capex_per_mw * 1_000_000
        simple_payback = total_capex / annual_revenue
        lifetime_revenue = annual_revenue * lifetime

        annual_carbon_savings_tonnes = (
            annual_energy_mwh * grid_carbon_intensity
        )

        lifetime_carbon_savings_tonnes = (
            annual_carbon_savings_tonnes * lifetime
        )

        st.subheader("Calculated results")

        result_col1, result_col2, result_col3 = st.columns(3)

        with result_col1:
            st.metric("Annual energy", f"{annual_energy_mwh:,.0f} MWh/year")

        with result_col2:
            st.metric("Turbines", f"{number_of_turbines:,.1f}")

        with result_col3:
            st.metric(
                "Annual revenue",
                f"£{annual_revenue / 1_000_000:,.1f}m/year",
            )

        result_col4, result_col5, result_col6 = st.columns(3)

        with result_col4:
            st.metric("CAPEX", f"£{total_capex / 1_000_000_000:,.2f}bn")

        with result_col5:
            st.metric("Simple payback", f"{simple_payback:,.1f} years")

        with result_col6:
            st.metric(
                "Lifetime revenue",
                f"£{lifetime_revenue / 1_000_000_000:,.2f}bn",
            )

        result_col7, result_col8 = st.columns(2)

        with result_col7:
            st.metric(
                "Annual carbon savings",
                f"{annual_carbon_savings_tonnes:,.0f} tonnes CO₂e/year",
            )

        with result_col8:
            st.metric(
                "Lifetime carbon savings",
                f"{lifetime_carbon_savings_tonnes:,.0f} tonnes CO₂e",
            )

        st.subheader("Sensitivity analysis")

        sensitivity_rows = []

        for cf in [0.35, 0.40, 0.45, 0.50, 0.55]:
            energy = project_capacity * cf * 8760
            revenue = energy * electricity_price
            payback = total_capex / revenue

            sensitivity_rows.append(
                {
                    "Capacity factor": cf,
                    "Annual energy (MWh)": energy,
                    "Annual revenue (£m)": revenue / 1_000_000,
                    "Simple payback (years)": payback,
                }
            )

        sensitivity_df = pd.DataFrame(sensitivity_rows)

        st.dataframe(sensitivity_df, use_container_width=True)

        fig_sensitivity = px.line(
            sensitivity_df,
            x="Capacity factor",
            y="Simple payback (years)",
            markers=True,
        )

        st.plotly_chart(
            polish_chart(fig_sensitivity, height=380),
            use_container_width=True,
            config={"displayModeBar": False},
        )

# ---------------------------------------------------
# METHODOLOGY
# ---------------------------------------------------

with methodology_tab:
    st.header("Methodology")

    st.write(
        """
        This project is a simplified renewable infrastructure screening tool.
        It demonstrates data cleaning, visualisation, geospatial mapping and basic
        techno-economic analysis.
        """
    )

    st.subheader("Data processing")

    st.markdown(
        """
        1. Loads the renewable project dataset from CSV.
        2. Converts installed capacity to numeric values.
        3. Removes projects without valid installed capacity.
        4. Converts British National Grid coordinates into latitude and longitude.
        5. Applies selected filters for technology, region and development status.
        """
    )

    st.subheader("Project screening score")

    st.markdown(
        """
        Each project receives a simplified score out of 100 based on installed capacity,
        development status, technology type and completeness of key project information.
        """
    )

    st.subheader("Offshore wind formulae")

    st.markdown(
        """
        - Annual energy generation = capacity × capacity factor × 8760
        - Number of turbines = project capacity ÷ turbine rating
        - Annual revenue = annual energy generation × electricity price
        - Total CAPEX = project capacity × CAPEX per MW
        - Simple payback = total CAPEX ÷ annual revenue
        - Annual carbon savings = annual energy generation × displaced grid carbon intensity
        - Lifetime carbon savings = annual carbon savings × project lifetime
        """
    )

    st.subheader("Limitations")

    st.markdown(
        """
        This is a simplified educational and portfolio model. It does not include detailed
        wind resource modelling, turbine availability, wake losses, grid connection cost,
        financing cost, CfD pricing, inflation, operational expenditure, decommissioning
        costs or planning-risk modelling.
        """
    )

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.divider()

footer_col1, footer_col2, footer_col3 = st.columns([1.2, 1, 1])

with footer_col1:
    st.markdown(
        """
        **HJ Nakamura**  
        Mechanical Engineering, Imperial College London
        """
    )


with footer_col2:
    st.markdown(
        f"""
        **Code**  
        [GitHub repository]({GITHUB_URL})
        """
    )

st.caption(
    "Educational portfolio project only."
)