import base64
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
    layout="wide",
)

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------

DATA_PATH = Path("data/renewable_projects.csv")
HERO_IMAGE_PATH = Path("assets/hero.jpg")
DEMO_VIDEO_PATH = Path("assets/demo.mp4")

# ---------------------------------------------------
# PREMIUM DASHBOARD CSS
# ---------------------------------------------------

st.markdown(
    """
    <style>
    /* ---------- App shell ---------- */

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 4rem;
        max-width: 1220px;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                     "Inter", "Segoe UI", sans-serif;
    }

    body {
        background-color: #F5F5F2;
    }

    h1, h2, h3 {
        color: #111111;
        letter-spacing: -0.045em;
    }

    h1 {
        font-size: clamp(2.4rem, 4.8vw, 4.3rem);
        line-height: 1;
        font-weight: 760;
        margin-bottom: 0.65rem;
        white-space: nowrap;
    }

    h2 {
        font-size: clamp(1.8rem, 3vw, 2.7rem);
        line-height: 1.05;
        font-weight: 720;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
    }

    h3 {
        font-size: 1.18rem;
        font-weight: 660;
        margin-top: 1.45rem;
    }

    p, li {
        color: #3A3A3C;
        font-size: 1rem;
        line-height: 1.62;
    }

    /* ---------- Compact hero ---------- */

    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.1rem;
        color: #6E6E73;
        font-size: 0.88rem;
    }

    .brand-lockup {
        font-weight: 720;
        color: #111111;
        letter-spacing: -0.02em;
    }

    .topbar-meta {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .topbar-pill {
        border: 1px solid #E5E5E0;
        background: rgba(255, 255, 255, 0.78);
        padding: 0.4rem 0.7rem;
        border-radius: 999px;
        color: #4B5563;
    }

    .hero {
        min-height: 430px;
        border-radius: 2.1rem;
        margin-bottom: 1.45rem;
        padding: 3.2rem;
        display: flex;
        align-items: flex-end;
        background-size: cover;
        background-position: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.15);
    }

    .hero-content {
        max-width: 960px;
        z-index: 2;
    }

    .eyebrow {
        color: rgba(255, 255, 255, 0.78);
        font-size: 0.76rem;
        font-weight: 760;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .hero-title {
        color: white;
        font-size: clamp(2.55rem, 5vw, 5rem);
        line-height: 0.96;
        letter-spacing: -0.075em;
        font-weight: 780;
        margin-bottom: 1rem;
        white-space: nowrap;
    }

    .hero-subtitle {
        color: rgba(255, 255, 255, 0.88);
        font-size: clamp(1rem, 1.45vw, 1.25rem);
        line-height: 1.5;
        max-width: 760px;
        margin-bottom: 1.25rem;
    }

    .hero-meta {
        display: inline-flex;
        gap: 0.55rem;
        flex-wrap: wrap;
    }

    .hero-pill {
        color: white;
        background: rgba(255, 255, 255, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.24);
        border-radius: 999px;
        padding: 0.48rem 0.75rem;
        font-size: 0.8rem;
        backdrop-filter: blur(16px);
    }

    /* ---------- Capability strip ---------- */

    .capability-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.85rem;
        margin-top: 0.9rem;
        margin-bottom: 1.6rem;
    }

    .capability-card {
        background: #FFFFFF;
        border: 1px solid #E7E7E2;
        border-radius: 1.35rem;
        padding: 1.15rem 1.25rem;
        min-height: 118px;
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.04);
    }

    .capability-number {
        color: #A18F69;
        font-size: 0.74rem;
        font-weight: 760;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.78rem;
    }

    .capability-title {
        color: #111111;
        font-size: 1.25rem;
        font-weight: 730;
        letter-spacing: -0.035em;
        margin-bottom: 0.35rem;
    }

    .capability-text {
        color: #60636A;
        font-size: 0.94rem;
        line-height: 1.48;
    }

    /* ---------- Filter drawer ---------- */

    details {
        background: #FFFFFF;
        border: 1px solid #E7E7E2;
        border-radius: 1.35rem;
        padding: 0.75rem 1rem;
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.035);
        margin-bottom: 1.35rem;
    }

    summary {
        cursor: pointer;
        font-weight: 700;
        color: #111111;
        letter-spacing: -0.025em;
    }

    /* ---------- Metrics ---------- */

    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E7E7E2;
        padding: 1.15rem 1.25rem;
        border-radius: 1.25rem;
        box-shadow: 0 14px 38px rgba(0, 0, 0, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #737373;
        font-size: 0.84rem;
        font-weight: 520;
    }

    [data-testid="stMetricValue"] {
        color: #111111;
        font-size: 1.55rem;
        font-weight: 730;
        letter-spacing: -0.035em;
    }

    /* ---------- Tabs ---------- */

    button[data-baseweb="tab"] {
        font-size: 0.94rem;
        font-weight: 630;
        color: #777777;
        padding-top: 0.7rem;
        padding-bottom: 0.7rem;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #111111;
    }

    /* ---------- Tables / buttons / sidebar ---------- */

    div[data-testid="stDataFrame"] {
        border-radius: 1rem;
        overflow: hidden;
        border: 1px solid #E7E7E2;
    }

    .stDownloadButton button {
        border-radius: 999px;
        background-color: #111111;
        color: white;
        border: 1px solid #111111;
        font-weight: 650;
        padding: 0.55rem 1.25rem;
    }

    .stAlert {
        border-radius: 1rem;
        border: 1px solid #E7E7E2;
    }

    section[data-testid="stSidebar"] {
        display: none;
    }

    /* ---------- Mobile ---------- */

    @media (max-width: 900px) {
        h1 {
            white-space: normal;
        }

        .hero {
            padding: 2.2rem 1.5rem;
            min-height: 420px;
        }

        .hero-title {
            white-space: normal;
        }

        .capability-grid {
            grid-template-columns: 1fr;
        }

        .topbar {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.7rem;
        }

        .topbar-meta {
            justify-content: flex-start;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------


def image_to_base64(image_path: Path) -> str | None:
    """Convert a local image file to base64 for use in the hero background."""

    if not image_path.exists():
        return None

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and clean the renewable energy dataset."""

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
    """Calculate a simple renewable project screening score out of 100."""

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


def polish_chart(fig):
    """Apply a cleaner dashboard style to Plotly charts."""

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
            color="#111111",
        ),
        title=dict(
            font=dict(size=20, color="#111111"),
            x=0,
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

try:
    df = load_data()

except Exception as e:
    st.error("Error loading dataset.")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------
# PREMIUM HEADER
# ---------------------------------------------------

hero_image = image_to_base64(HERO_IMAGE_PATH)

if hero_image:
    hero_background = (
        "linear-gradient(90deg, rgba(0,0,0,0.82) 0%, "
        "rgba(0,0,0,0.52) 42%, rgba(0,0,0,0.12) 100%), "
        f"url('data:image/jpeg;base64,{hero_image}')"
    )
else:
    hero_background = "linear-gradient(135deg, #050505 0%, #242424 48%, #87785D 100%)"

st.markdown(
    """
    <div class="topbar">
        <div class="brand-lockup">Renewable Project Screening Studio</div>
        <div class="topbar-meta">
            <span class="topbar-pill">Portfolio project</span>
            <span class="topbar-pill">UK planning data</span>
            <span class="topbar-pill">Python · Streamlit</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <section class="hero" style="background-image: {hero_background};">
        <div class="hero-content">
            <div class="eyebrow">Renewable infrastructure intelligence</div>
            <div class="hero-title">Renewable Project Screening Studio</div>
            <div class="hero-subtitle">
                A clean portfolio-grade dashboard for exploring UK renewable project pipelines,
                mapping developments, generating project briefs and testing simplified offshore
                wind feasibility assumptions.
            </div>
            <div class="hero-meta">
                <span class="hero-pill">Screen projects</span>
                <span class="hero-pill">Compare pipeline capacity</span>
                <span class="hero-pill">Map developments</span>
                <span class="hero-pill">Model offshore wind</span>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="capability-grid">
        <div class="capability-card">
            <div class="capability-number">01</div>
            <div class="capability-title">Screen</div>
            <div class="capability-text">
                Filter renewable infrastructure projects by technology, development stage and region.
            </div>
        </div>
        <div class="capability-card">
            <div class="capability-number">02</div>
            <div class="capability-title">Compare</div>
            <div class="capability-text">
                Analyse capacity pipelines, regional concentration and major project clusters.
            </div>
        </div>
        <div class="capability-card">
            <div class="capability-number">03</div>
            <div class="capability-title">Model</div>
            <div class="capability-text">
                Estimate offshore wind generation, CAPEX, payback and carbon impact.
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if DEMO_VIDEO_PATH.exists():
    with st.expander("Watch short project walkthrough"):
        st.video(str(DEMO_VIDEO_PATH))

# ---------------------------------------------------
# COMPACT FILTER DRAWER
# ---------------------------------------------------

technology_options = sorted(df["Technology Type"].dropna().unique())
status_options = sorted(df["Development Status (short)"].dropna().unique())
region_options = sorted(df["Region"].dropna().unique())

with st.expander("Refine project universe", expanded=False):
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        selected_technology = st.multiselect(
            "Technology",
            technology_options,
            default=technology_options,
        )

    with filter_col2:
        selected_status = st.multiselect(
            "Development stage",
            status_options,
            default=status_options,
        )

    with filter_col3:
        selected_region = st.multiselect(
            "Region",
            region_options,
            default=region_options,
        )

    st.caption(
        "Filters are collapsed by default to keep the dashboard clean. "
        "Leaving a filter empty is treated as selecting all options."
    )

technology_filter = selected_technology or technology_options
status_filter = selected_status or status_options
region_filter = selected_region or region_options

# ---------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------

filtered_df = df[
    (df["Technology Type"].isin(technology_filter))
    & (df["Development Status (short)"].isin(status_filter))
    & (df["Region"].isin(region_filter))
].copy()

if filtered_df.empty:
    st.warning(
        "No projects match the current filters. "
        "Try selecting more technologies, regions or development statuses."
    )
    st.stop()

filtered_df["Screening Score"] = filtered_df.apply(
    calculate_screening_score,
    axis=1,
)

# ---------------------------------------------------
# SHARED SUMMARY VALUES
# ---------------------------------------------------

total_capacity = filtered_df["Installed Capacity (MWelec)"].sum()
avg_capacity = filtered_df["Installed Capacity (MWelec)"].mean()

latest_update_text = "N/A"

if "Record Last Updated Parsed" in filtered_df.columns:
    latest_update = filtered_df["Record Last Updated Parsed"].max()

    if pd.notna(latest_update):
        latest_update_text = latest_update.strftime("%d %b %Y")

# ---------------------------------------------------
# TABS
# ---------------------------------------------------

overview_tab, explorer_tab, map_tab, report_tab, offshore_tab, methodology_tab = st.tabs(
    [
        "Portfolio Overview",
        "Project Pipeline",
        "Geographic View",
        "Project Briefs",
        "Offshore Wind Model",
        "Methodology",
    ]
)

# ---------------------------------------------------
# PORTFOLIO OVERVIEW TAB
# ---------------------------------------------------

with overview_tab:
    st.header("Portfolio Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Projects", f"{len(filtered_df):,}")

    with col2:
        st.metric("Total Capacity", f"{total_capacity:,.0f} MW")

    with col3:
        st.metric("Average Capacity", f"{avg_capacity:,.1f} MW")

    with col4:
        st.metric("Latest Update", latest_update_text)

    st.subheader("Executive Summary")

    largest_tech = (
        filtered_df
        .groupby("Technology Type")["Installed Capacity (MWelec)"]
        .sum()
        .idxmax()
    )

    largest_region = (
        filtered_df
        .groupby("Region")["Installed Capacity (MWelec)"]
        .sum()
        .idxmax()
    )

    largest_project_row = filtered_df.sort_values(
        "Installed Capacity (MWelec)",
        ascending=False,
    ).iloc[0]

    largest_project_name = largest_project_row["Site Name"]
    largest_project_capacity = largest_project_row["Installed Capacity (MWelec)"]

    top_10_capacity = (
        filtered_df
        .sort_values("Installed Capacity (MWelec)", ascending=False)
        .head(10)["Installed Capacity (MWelec)"]
        .sum()
    )

    top_10_share = top_10_capacity / total_capacity * 100

    st.markdown(
        f"""
        Under the current filters:

        - **{largest_tech}** represents the largest share of filtered capacity.
        - **{largest_region}** is the leading region by filtered installed capacity.
        - The largest project is **{largest_project_name}** at **{largest_project_capacity:,.0f} MW**.
        - The top 10 projects account for approximately **{top_10_share:,.1f}%** of filtered capacity.
        """
    )

    st.subheader("Technology Pipeline")

    tech_capacity = (
        filtered_df
        .groupby("Technology Type")["Installed Capacity (MWelec)"]
        .sum()
        .reset_index()
        .sort_values("Installed Capacity (MWelec)", ascending=False)
    )

    fig1 = px.bar(
        tech_capacity,
        x="Technology Type",
        y="Installed Capacity (MWelec)",
        title="Installed Capacity by Technology",
        labels={
            "Technology Type": "Technology Type",
            "Installed Capacity (MWelec)": "Installed Capacity (MW)",
        },
    )

    st.plotly_chart(polish_chart(fig1), width="stretch")

    st.subheader("Regional Pipeline")

    region_capacity = (
        filtered_df
        .groupby("Region")["Installed Capacity (MWelec)"]
        .sum()
        .reset_index()
        .sort_values("Installed Capacity (MWelec)", ascending=False)
    )

    fig2 = px.bar(
        region_capacity,
        x="Region",
        y="Installed Capacity (MWelec)",
        title="Installed Capacity by Region",
        labels={
            "Region": "Region",
            "Installed Capacity (MWelec)": "Installed Capacity (MW)",
        },
    )

    st.plotly_chart(polish_chart(fig2), width="stretch")

# ---------------------------------------------------
# PROJECT PIPELINE TAB
# ---------------------------------------------------

with explorer_tab:
    st.header("Project Pipeline")

    st.write(
        """
        Explore the filtered project universe. The table below shows a readable preview;
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
        "Planning Application Reference",
        "Screening Score",
    ]

    available_display_columns = [
        col for col in display_columns if col in filtered_df.columns
    ]

    st.dataframe(
        filtered_df[available_display_columns].head(500),
        width="stretch",
    )

    st.caption(
        "Showing first 500 filtered rows for readability. "
        "Download the CSV for the full filtered dataset."
    )

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="filtered_renewable_projects.csv",
        mime="text/csv",
    )

    st.subheader("Major Projects")

    top_projects = (
        filtered_df
        .sort_values("Installed Capacity (MWelec)", ascending=False)
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

    st.dataframe(top_projects, width="stretch")

    st.subheader("Capacity by Development Stage")

    status_capacity = (
        filtered_df
        .groupby("Development Status (short)")["Installed Capacity (MWelec)"]
        .sum()
        .reset_index()
        .sort_values("Installed Capacity (MWelec)", ascending=False)
    )

    fig_status = px.bar(
        status_capacity,
        x="Development Status (short)",
        y="Installed Capacity (MWelec)",
        title="Filtered Capacity by Development Stage",
        labels={
            "Development Status (short)": "Development Stage",
            "Installed Capacity (MWelec)": "Installed Capacity (MW)",
        },
    )

    st.plotly_chart(polish_chart(fig_status), width="stretch")

    st.subheader("Technology Pipeline by Development Stage")

    pipeline_matrix = (
        filtered_df
        .groupby(["Technology Type", "Development Status (short)"])
        ["Installed Capacity (MWelec)"]
        .sum()
        .reset_index()
    )

    fig_pipeline = px.bar(
        pipeline_matrix,
        x="Technology Type",
        y="Installed Capacity (MWelec)",
        color="Development Status (short)",
        title="Technology Pipeline by Development Stage",
        labels={
            "Technology Type": "Technology",
            "Installed Capacity (MWelec)": "Installed Capacity (MW)",
            "Development Status (short)": "Development Stage",
        },
    )

    st.plotly_chart(polish_chart(fig_pipeline), width="stretch")

# ---------------------------------------------------
# GEOGRAPHIC VIEW TAB
# ---------------------------------------------------

with map_tab:
    st.header("Geographic View")

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
            height=650,
            title="UK Renewable Energy Projects",
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
        )

        st.plotly_chart(fig_map, width="stretch")

# ---------------------------------------------------
# PROJECT BRIEFS TAB
# ---------------------------------------------------

with report_tab:
    st.header("Project Briefs")

    st.write(
        """
        Select a project to generate a structured project brief with key planning,
        technical and screening information.
        """
    )

    project_options = sorted(filtered_df["Site Name"].dropna().unique())

    if len(project_options) == 0:
        st.warning("No projects are available under the current filters.")

    else:
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

        st.markdown("### Project Details")

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

        st.markdown("### Comparable Projects")

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
                width="stretch",
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

        safe_project_name = (
            selected_report_project
            .replace("/", "-")
            .replace("\\", "-")
            .replace(" ", "_")
        )

        st.download_button(
            label="Download project brief",
            data=report_text,
            file_name=f"{safe_project_name}_project_brief.txt",
            mime="text/plain",
        )

# ---------------------------------------------------
# OFFSHORE WIND MODEL TAB
# ---------------------------------------------------

with offshore_tab:
    st.header("Offshore Wind Model")

    st.write(
        """
        This section estimates basic engineering and commercial metrics for offshore wind projects.
        The model is simplified and intended for educational and portfolio purposes.
        """
    )

    offshore_df = filtered_df[
        filtered_df["Technology Type"].str.contains(
            "Wind Offshore",
            case=False,
            na=False,
        )
    ].copy()

    if offshore_df.empty:
        st.warning(
            "No offshore wind projects are currently visible. "
            "Change the filters in the dashboard controls to include Wind Offshore projects."
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

        st.subheader("Selected Project")

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

        st.subheader("Calculated Results")

        result_col1, result_col2, result_col3 = st.columns(3)

        with result_col1:
            st.metric("Annual Energy", f"{annual_energy_mwh:,.0f} MWh/year")

        with result_col2:
            st.metric("Turbines", f"{number_of_turbines:,.1f}")

        with result_col3:
            st.metric(
                "Annual Revenue",
                f"£{annual_revenue / 1_000_000:,.1f}m/year",
            )

        result_col4, result_col5, result_col6 = st.columns(3)

        with result_col4:
            st.metric("CAPEX", f"£{total_capex / 1_000_000_000:,.2f}bn")

        with result_col5:
            st.metric("Simple Payback", f"{simple_payback:,.1f} years")

        with result_col6:
            st.metric(
                "Lifetime Revenue",
                f"£{lifetime_revenue / 1_000_000_000:,.2f}bn",
            )

        result_col7, result_col8 = st.columns(2)

        with result_col7:
            st.metric(
                "Annual Carbon Savings",
                f"{annual_carbon_savings_tonnes:,.0f} tonnes CO₂e/year",
            )

        with result_col8:
            st.metric(
                "Lifetime Carbon Savings",
                f"{lifetime_carbon_savings_tonnes:,.0f} tonnes CO₂e",
            )

        st.subheader("Sensitivity Analysis")

        st.write(
            """
            This table shows how the simple payback period changes as the capacity factor changes,
            while keeping the other assumptions constant.
            """
        )

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

        st.dataframe(sensitivity_df, width="stretch")

        fig_sensitivity = px.line(
            sensitivity_df,
            x="Capacity factor",
            y="Simple payback (years)",
            markers=True,
            title="Simple Payback Sensitivity to Capacity Factor",
        )

        st.plotly_chart(polish_chart(fig_sensitivity), width="stretch")

# ---------------------------------------------------
# METHODOLOGY TAB
# ---------------------------------------------------

with methodology_tab:
    st.header("Methodology")

    st.write(
        """
        This project is a simplified renewable infrastructure screening tool.
        It is designed to demonstrate engineering judgement, data cleaning,
        visualisation, geospatial mapping and basic techno-economic analysis.
        """
    )

    st.subheader("Data Processing")

    st.markdown(
        """
        The app performs the following steps:

        1. Loads the renewable project dataset from CSV.
        2. Converts installed capacity to numeric values.
        3. Removes projects without valid installed capacity.
        4. Converts British National Grid coordinates into latitude and longitude.
        5. Applies user-selected filters for technology, region and development status.
        """
    )

    st.subheader("Project Screening Score")

    st.markdown(
        """
        Each project receives a simplified score out of 100 based on:

        - installed capacity
        - development status
        - technology type
        - completeness of key project information

        The score is intended as an early-stage screening indicator, not a definitive
        investment ranking.
        """
    )

    st.subheader("Offshore Wind Formulae")

    st.markdown(
        """
        The offshore wind model uses the following simplified formulae:

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
        This is a simplified educational and portfolio model. It does not include:

        - detailed wind resource modelling
        - turbine availability
        - wake losses
        - grid connection cost
        - financing cost
        - CfD pricing
        - inflation
        - operational expenditure
        - decommissioning costs
        - planning-risk modelling

        The tool should not be interpreted as an investment-grade renewable energy model.
        """
    )