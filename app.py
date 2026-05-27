import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from pyproj import Transformer

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="UK Renewable Energy Infrastructure Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# SIMPLE CUSTOM CSS
# ---------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    h1 {
        font-size: 2.8rem;
        font-weight: 800;
    }

    h2, h3 {
        margin-top: 2rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.7rem;
    }

    .stAlert {
        border-radius: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# LOAD AND CLEAN DATA
# ---------------------------------------------------

DATA_PATH = Path("data/renewable_projects.csv")


@st.cache_data
def load_data():
    """Load and clean the renewable energy dataset."""

    data = pd.read_csv(DATA_PATH, encoding="latin1")

    # Convert capacity column to numeric
    data["Installed Capacity (MWelec)"] = pd.to_numeric(
        data["Installed Capacity (MWelec)"],
        errors="coerce"
    )

    # Remove rows without capacity
    data = data.dropna(subset=["Installed Capacity (MWelec)"])

    # Convert X/Y coordinates to numeric
    data["X-coordinate"] = pd.to_numeric(data["X-coordinate"], errors="coerce")
    data["Y-coordinate"] = pd.to_numeric(data["Y-coordinate"], errors="coerce")

    # Convert British National Grid coordinates to latitude/longitude
    transformer = Transformer.from_crs(
        "EPSG:27700",
        "EPSG:4326",
        always_xy=True
    )

    valid_coords = (
        data["X-coordinate"].notna()
        & data["Y-coordinate"].notna()
    )

    data.loc[valid_coords, "Longitude"], data.loc[valid_coords, "Latitude"] = (
        transformer.transform(
            data.loc[valid_coords, "X-coordinate"].values,
            data.loc[valid_coords, "Y-coordinate"].values
        )
    )

    # Convert record update date where possible
    if "Record Last Updated (dd/mm/yyyy)" in data.columns:
        data["Record Last Updated Parsed"] = pd.to_datetime(
            data["Record Last Updated (dd/mm/yyyy)"],
            dayfirst=True,
            errors="coerce"
        )

    return data


try:
    df = load_data()

except Exception as e:
    st.error("Error loading dataset")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------
# TITLE / INTRO
# ---------------------------------------------------

st.title("UK Renewable Energy Infrastructure Dashboard")

st.markdown(
    """
    Explore UK renewable energy projects, compare regional capacity, identify major developments,
    and run simplified offshore wind feasibility calculations.

    **Built with Python, Streamlit, pandas, Plotly and pyproj.**
    """
)

st.info(
    "This tool is designed as an early-stage renewable infrastructure analysis dashboard. "
    "It is not an investment-grade model, but it demonstrates how public energy datasets "
    "can be turned into useful engineering and commercial insight."
)

st.caption(
    "Data source: UK Renewable Energy Planning Database. "
    "This app uses a locally stored extract of the public dataset."
)

# ---------------------------------------------------
# USE CASE CARDS
# ---------------------------------------------------

st.subheader("What this dashboard helps with")

use_col1, use_col2, use_col3 = st.columns(3)

with use_col1:
    st.markdown(
        """
        **Project Screening**

        Quickly filter renewable energy projects by technology, region and development status.
        """
    )

with use_col2:
    st.markdown(
        """
        **Energy Analysis**

        Estimate offshore wind generation, revenue, CAPEX, payback and carbon savings.
        """
    )

with use_col3:
    st.markdown(
        """
        **Portfolio Insight**

        Compare regional capacity and identify major renewable energy developments.
        """
    )

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------

st.sidebar.header("Filters")

technology_options = sorted(
    df["Technology Type"].dropna().unique()
)

selected_technology = st.sidebar.multiselect(
    "Select Technology Type",
    technology_options,
    default=technology_options
)

status_options = sorted(
    df["Development Status (short)"].dropna().unique()
)

selected_status = st.sidebar.multiselect(
    "Select Development Status",
    status_options,
    default=status_options
)

region_options = sorted(
    df["Region"].dropna().unique()
)

selected_region = st.sidebar.multiselect(
    "Select Region",
    region_options,
    default=region_options
)

# ---------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------

filtered_df = df[
    (df["Technology Type"].isin(selected_technology))
    & (df["Development Status (short)"].isin(selected_status))
    & (df["Region"].isin(selected_region))
].copy()

# ---------------------------------------------------
# EMPTY FILTER WARNING
# ---------------------------------------------------

if filtered_df.empty:
    st.warning(
        "No projects match the current filters. "
        "Try selecting more technologies, regions or development statuses."
    )
    st.stop()

# ---------------------------------------------------
# OVERVIEW METRICS
# ---------------------------------------------------

st.header("Overview")

total_capacity = filtered_df["Installed Capacity (MWelec)"].sum()
avg_capacity = filtered_df["Installed Capacity (MWelec)"].mean()
largest_project_capacity = filtered_df["Installed Capacity (MWelec)"].max()

latest_update_text = "N/A"

if "Record Last Updated Parsed" in filtered_df.columns:
    latest_update = filtered_df["Record Last Updated Parsed"].max()

    if pd.notna(latest_update):
        latest_update_text = latest_update.strftime("%d %b %Y")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Number of Projects",
        f"{len(filtered_df):,}"
    )

with col2:
    st.metric(
        "Total Capacity",
        f"{total_capacity:,.0f} MW"
    )

with col3:
    st.metric(
        "Average Capacity",
        f"{avg_capacity:,.1f} MW"
    )

with col4:
    st.metric(
        "Latest Record Update",
        latest_update_text
    )

# ---------------------------------------------------
# DATA PREVIEW
# ---------------------------------------------------

st.header("Project Data Explorer")

st.write(
    """
    Use the filters in the sidebar to narrow the dataset. You can also download
    the filtered project data as a CSV.
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
    "Planning Application Reference"
]

available_display_columns = [
    col for col in display_columns if col in filtered_df.columns
]

st.dataframe(
    filtered_df[available_display_columns],
    width="stretch"
)

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="filtered_renewable_projects.csv",
    mime="text/csv"
)

# ---------------------------------------------------
# CAPACITY BY TECHNOLOGY
# ---------------------------------------------------

st.header("Capacity by Technology")

tech_capacity = (
    filtered_df
    .groupby("Technology Type")["Installed Capacity (MWelec)"]
    .sum()
    .reset_index()
    .sort_values(
        "Installed Capacity (MWelec)",
        ascending=False
    )
)

fig1 = px.bar(
    tech_capacity,
    x="Technology Type",
    y="Installed Capacity (MWelec)",
    title="Installed Capacity by Technology",
    labels={
        "Technology Type": "Technology Type",
        "Installed Capacity (MWelec)": "Installed Capacity (MW)"
    }
)

st.plotly_chart(fig1, width="stretch")

# ---------------------------------------------------
# CAPACITY BY REGION
# ---------------------------------------------------

st.header("Capacity by Region")

region_capacity = (
    filtered_df
    .groupby("Region")["Installed Capacity (MWelec)"]
    .sum()
    .reset_index()
    .sort_values(
        "Installed Capacity (MWelec)",
        ascending=False
    )
)

fig2 = px.bar(
    region_capacity,
    x="Region",
    y="Installed Capacity (MWelec)",
    title="Installed Capacity by Region",
    labels={
        "Region": "Region",
        "Installed Capacity (MWelec)": "Installed Capacity (MW)"
    }
)

st.plotly_chart(fig2, width="stretch")

# ---------------------------------------------------
# TOP 10 PROJECTS
# ---------------------------------------------------

st.header("Top 10 Largest Projects")

top_projects = (
    filtered_df
    .sort_values(
        "Installed Capacity (MWelec)",
        ascending=False
    )
    [
        [
            "Site Name",
            "Technology Type",
            "Installed Capacity (MWelec)",
            "Region",
            "Development Status (short)"
        ]
    ]
    .head(10)
)

st.dataframe(top_projects, width="stretch")

# ---------------------------------------------------
# PROJECT MAP
# ---------------------------------------------------

st.header("Project Map")

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
            "Development Status (short)"
        ],
        zoom=4,
        height=650,
        title="UK Renewable Energy Projects"
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={
            "r": 0,
            "t": 40,
            "l": 0,
            "b": 0
        }
    )

    st.plotly_chart(fig_map, width="stretch")

# ---------------------------------------------------
# PROJECT REPORT GENERATOR
# ---------------------------------------------------

st.header("Project Report Generator")

st.write(
    """
    Select a project to generate a simple summary report with key planning,
    technical and commercial information.
    """
)

project_options = sorted(filtered_df["Site Name"].dropna().unique())

if len(project_options) == 0:
    st.warning("No projects are available under the current filters.")

else:
    selected_report_project = st.selectbox(
        "Select a project",
        project_options,
        key="project_report_selector"
    )

    report_row = filtered_df[
        filtered_df["Site Name"] == selected_report_project
    ].iloc[0]

    st.subheader(selected_report_project)

    report_col1, report_col2, report_col3 = st.columns(3)

    with report_col1:
        st.metric(
            "Technology",
            report_row.get("Technology Type", "N/A")
        )

    with report_col2:
        st.metric(
            "Capacity",
            f"{report_row.get('Installed Capacity (MWelec)', 0):,.1f} MW"
        )

    with report_col3:
        st.metric(
            "Status",
            report_row.get("Development Status (short)", "N/A")
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

    report_text = f"""
Project Report: {selected_report_project}

Technology: {report_row.get("Technology Type", "N/A")}
Capacity: {report_row.get("Installed Capacity (MWelec)", "N/A")} MW
Development Status: {report_row.get("Development Status (short)", "N/A")}
Operator / Applicant: {report_row.get("Operator (or Applicant)", "N/A")}
Region: {report_row.get("Region", "N/A")}
County: {report_row.get("County", "N/A")}
Country: {report_row.get("Country", "N/A")}
Planning Authority: {report_row.get("Planning Authority", "N/A")}
Planning Application Reference: {report_row.get("Planning Application Reference", "N/A")}
Planning Submitted: {report_row.get("Planning Application Submitted", "N/A")}
Planning Granted: {report_row.get("Planning Permission  Granted", "N/A")}
Operational Date: {report_row.get("Operational", "N/A")}

Generated using the UK Renewable Energy Infrastructure Dashboard.
"""

    safe_project_name = (
        selected_report_project
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )

    st.download_button(
        label="Download project summary as TXT",
        data=report_text,
        file_name=f"{safe_project_name}_project_summary.txt",
        mime="text/plain"
    )

# ---------------------------------------------------
# OFFSHORE WIND FEASIBILITY CALCULATOR
# ---------------------------------------------------

st.header("Offshore Wind Feasibility Calculator")

st.write(
    """
    This section estimates basic engineering and commercial metrics for offshore wind projects.
    The model is simplified and intended for educational/CV project purposes.
    """
)

offshore_df = filtered_df[
    filtered_df["Technology Type"].str.contains(
        "Wind Offshore",
        case=False,
        na=False
    )
].copy()

if offshore_df.empty:
    st.warning(
        "No offshore wind projects are currently visible. "
        "Change the filters in the sidebar to include Wind Offshore projects."
    )

else:
    project_names = sorted(offshore_df["Site Name"].dropna().unique())

    selected_project = st.selectbox(
        "Select an offshore wind project",
        project_names,
        key="offshore_project_selector"
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
            step=0.01
        )

    with ass_col2:
        turbine_rating = st.slider(
            "Turbine rating (MW)",
            min_value=5.0,
            max_value=25.0,
            value=15.0,
            step=0.5
        )

    with ass_col3:
        electricity_price = st.slider(
            "Electricity price (£/MWh)",
            min_value=20,
            max_value=200,
            value=70,
            step=5
        )

    ass_col4, ass_col5, ass_col6 = st.columns(3)

    with ass_col4:
        capex_per_mw = st.slider(
            "CAPEX (£ million per MW)",
            min_value=1.0,
            max_value=8.0,
            value=3.0,
            step=0.1
        )

    with ass_col5:
        lifetime = st.slider(
            "Project lifetime (years)",
            min_value=10,
            max_value=40,
            value=25,
            step=1
        )

    with ass_col6:
        grid_carbon_intensity = st.slider(
            "Displaced grid carbon intensity (kg CO₂e/kWh)",
            min_value=0.00,
            max_value=0.60,
            value=0.20,
            step=0.01
        )

    annual_energy_mwh = project_capacity * capacity_factor * 8760
    number_of_turbines = project_capacity / turbine_rating
    annual_revenue = annual_energy_mwh * electricity_price
    total_capex = project_capacity * capex_per_mw * 1_000_000
    simple_payback = total_capex / annual_revenue
    lifetime_revenue = annual_revenue * lifetime

    annual_carbon_savings_tonnes = annual_energy_mwh * grid_carbon_intensity
    lifetime_carbon_savings_tonnes = (
        annual_carbon_savings_tonnes * lifetime
    )

    st.subheader("Calculated Results")

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:
        st.metric(
            "Estimated annual energy",
            f"{annual_energy_mwh:,.0f} MWh/year"
        )

    with result_col2:
        st.metric(
            "Estimated number of turbines",
            f"{number_of_turbines:,.1f}"
        )

    with result_col3:
        st.metric(
            "Estimated annual revenue",
            f"£{annual_revenue / 1_000_000:,.1f} million/year"
        )

    result_col4, result_col5, result_col6 = st.columns(3)

    with result_col4:
        st.metric(
            "Estimated CAPEX",
            f"£{total_capex / 1_000_000_000:,.2f} billion"
        )

    with result_col5:
        st.metric(
            "Simple payback period",
            f"{simple_payback:,.1f} years"
        )

    with result_col6:
        st.metric(
            "Lifetime revenue",
            f"£{lifetime_revenue / 1_000_000_000:,.2f} billion"
        )

    result_col7, result_col8 = st.columns(2)

    with result_col7:
        st.metric(
            "Estimated annual carbon savings",
            f"{annual_carbon_savings_tonnes:,.0f} tonnes CO₂e/year"
        )

    with result_col8:
        st.metric(
            "Estimated lifetime carbon savings",
            f"{lifetime_carbon_savings_tonnes:,.0f} tonnes CO₂e"
        )

    # ---------------------------------------------------
    # SENSITIVITY ANALYSIS
    # ---------------------------------------------------

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
        title="Simple Payback Sensitivity to Capacity Factor"
    )

    st.plotly_chart(fig_sensitivity, width="stretch")

# ---------------------------------------------------
# METHODOLOGY
# ---------------------------------------------------

st.header("Methodology")

st.write(
    """
    The calculations use the following simplified formulas:

    - Annual energy generation = capacity × capacity factor × 8760
    - Number of turbines = project capacity ÷ turbine rating
    - Annual revenue = annual energy generation × electricity price
    - Total CAPEX = project capacity × CAPEX per MW
    - Simple payback = total CAPEX ÷ annual revenue
    - Annual carbon savings = annual energy generation × displaced grid carbon intensity
    - Lifetime carbon savings = annual carbon savings × project lifetime

    These values are approximate and do not include financing costs, operational expenditure,
    grid connection costs, curtailment, maintenance downtime, inflation, strike prices,
    decommissioning costs or detailed wind resource modelling.
    """
)

# ---------------------------------------------------
# COMMERCIAL CALL TO ACTION
# ---------------------------------------------------

st.divider()

st.header("Need a custom dashboard?")

st.write(
    """
    I can build similar dashboards for engineering, energy, operations,
    finance, research or project data.

    If you have CSV files, Excel trackers, survey results, telemetry data,
    project databases or messy reports, I can help turn them into a clean,
    interactive web dashboard.
    """
)

cta_col1, cta_col2 = st.columns(2)

with cta_col1:
    st.markdown(
        """
        **Possible dashboard projects**

        - Renewable energy project dashboards
        - Formula Student telemetry dashboards
        - Business KPI dashboards
        - Financial tracking dashboards
        - Research data dashboards
        - Student society operations dashboards
        """
    )

with cta_col2:
    st.markdown(
        """
        **What I can provide**

        - Data cleaning
        - Interactive filters
        - Charts and maps
        - Downloadable reports
        - Deployment online
        - Documentation and handover
        """
    )

st.markdown(
    """
    **Contact:** replace-with-your-email@example.com  
    **GitHub:** replace-with-your-github-link  
    **LinkedIn:** replace-with-your-linkedin-link
    """
)