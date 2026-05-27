import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from pyproj import Transformer

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="UK Renewable Energy Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("UK Renewable Energy Dashboard")

st.write(
    """
    Interactive dashboard for exploring UK renewable energy infrastructure projects.
    """
)

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

DATA_PATH = Path("data/renewable_projects.csv")

try:
    df = pd.read_csv(DATA_PATH, encoding="latin1")

except Exception as e:
    st.error("Error loading dataset")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------

# Convert capacity column to numeric
df["Installed Capacity (MWelec)"] = pd.to_numeric(
    df["Installed Capacity (MWelec)"],
    errors="coerce"
)

# Remove rows without capacity
df = df.dropna(subset=["Installed Capacity (MWelec)"])

# Convert X/Y coordinates to numeric
df["X-coordinate"] = pd.to_numeric(df["X-coordinate"], errors="coerce")
df["Y-coordinate"] = pd.to_numeric(df["Y-coordinate"], errors="coerce")

# Convert British National Grid coordinates to latitude/longitude
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

valid_coords = df["X-coordinate"].notna() & df["Y-coordinate"].notna()

df.loc[valid_coords, "Longitude"], df.loc[valid_coords, "Latitude"] = transformer.transform(
    df.loc[valid_coords, "X-coordinate"].values,
    df.loc[valid_coords, "Y-coordinate"].values
)

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------

st.sidebar.header("Filters")

# Technology filter
technology_options = sorted(
    df["Technology Type"].dropna().unique()
)

selected_technology = st.sidebar.multiselect(
    "Select Technology Type",
    technology_options,
    default=technology_options
)

# Development status filter
status_options = sorted(
    df["Development Status (short)"].dropna().unique()
)

selected_status = st.sidebar.multiselect(
    "Select Development Status",
    status_options,
    default=status_options
)

# Region filter
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
    (df["Technology Type"].isin(selected_technology)) &
    (df["Development Status (short)"].isin(selected_status)) &
    (df["Region"].isin(selected_region))
]

# ---------------------------------------------------
# TOP METRICS
# ---------------------------------------------------

st.header("Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Number of Projects",
        len(filtered_df)
    )

with col2:
    total_capacity = filtered_df["Installed Capacity (MWelec)"].sum()

    st.metric(
        "Total Capacity (MW)",
        f"{total_capacity:,.0f}"
    )

with col3:
    avg_capacity = filtered_df["Installed Capacity (MWelec)"].mean()

    st.metric(
        "Average Capacity (MW)",
        f"{avg_capacity:,.1f}"
    )

# ---------------------------------------------------
# DATA PREVIEW
# ---------------------------------------------------

st.header("Dataset Preview")

st.dataframe(filtered_df)

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
    title="Installed Capacity by Technology"
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
    title="Installed Capacity by Region"
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

st.dataframe(top_projects)

# ---------------------------------------------------
# PROJECT MAP
# ---------------------------------------------------

st.header("Project Map")

map_df = filtered_df.dropna(subset=["Latitude", "Longitude"]).copy()

if map_df.empty:
    st.warning("No valid coordinates available for the current filters.")

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
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    st.plotly_chart(fig_map, width="stretch")


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

# Filter to offshore wind projects only
offshore_df = filtered_df[
    filtered_df["Technology Type"].str.contains("Wind Offshore", case=False, na=False)
].copy()

if offshore_df.empty:
    st.warning(
        "No offshore wind projects are currently visible. "
        "Change the filters in the sidebar to include Offshore Wind projects."
    )

else:
    # Select a project
    project_names = sorted(offshore_df["Site Name"].dropna().unique())

    selected_project = st.selectbox(
        "Select an offshore wind project",
        project_names
    )

    project_row = offshore_df[
        offshore_df["Site Name"] == selected_project
    ].iloc[0]

    project_capacity = project_row["Installed Capacity (MWelec)"]

    st.subheader("Selected Project")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Project", selected_project)

    with col2:
        st.metric("Capacity", f"{project_capacity:,.0f} MW")

    with col3:
        st.metric("Region", project_row["Region"])

    st.subheader("Assumptions")

    col1, col2, col3 = st.columns(3)

    with col1:
        capacity_factor = st.slider(
            "Capacity factor",
            min_value=0.20,
            max_value=0.70,
            value=0.45,
            step=0.01
        )

    with col2:
        turbine_rating = st.slider(
            "Turbine rating (MW)",
            min_value=5.0,
            max_value=25.0,
            value=15.0,
            step=0.5
        )

    with col3:
        electricity_price = st.slider(
            "Electricity price (£/MWh)",
            min_value=20,
            max_value=200,
            value=70,
            step=5
        )

    col4, col5 = st.columns(2)

    with col4:
        capex_per_mw = st.slider(
            "CAPEX (£ million per MW)",
            min_value=1.0,
            max_value=8.0,
            value=3.0,
            step=0.1
        )

    with col5:
        lifetime = st.slider(
            "Project lifetime (years)",
            min_value=10,
            max_value=40,
            value=25,
            step=1
        )

    # Calculations
    annual_energy_mwh = project_capacity * capacity_factor * 8760
    number_of_turbines = project_capacity / turbine_rating
    annual_revenue = annual_energy_mwh * electricity_price
    total_capex = project_capacity * capex_per_mw * 1_000_000
    simple_payback = total_capex / annual_revenue
    lifetime_revenue = annual_revenue * lifetime

    grid_carbon_intensity = st.slider(
        "Displaced grid carbon intensity (kg CO₂e/kWh)",
        min_value=0.00,
        max_value=0.60,
        value=0.20,
        step=0.01
    )

    annual_carbon_savings_tonnes = annual_energy_mwh * grid_carbon_intensity
    lifetime_carbon_savings_tonnes = annual_carbon_savings_tonnes * lifetime

    st.subheader("Calculated Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Estimated annual energy",
            f"{annual_energy_mwh:,.0f} MWh/year"
        )

    with col2:
        st.metric(
            "Estimated number of turbines",
            f"{number_of_turbines:,.1f}"
        )

    with col3:
        st.metric(
            "Estimated annual revenue",
            f"£{annual_revenue / 1_000_000:,.1f} million/year"
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "Estimated CAPEX",
            f"£{total_capex / 1_000_000_000:,.2f} billion"
        )

    with col5:
        st.metric(
            "Simple payback period",
            f"{simple_payback:,.1f} years"
        )

    with col6:
        st.metric(
            "Lifetime revenue",
            f"£{lifetime_revenue / 1_000_000_000:,.2f} billion"
        )

    col7, col8 = st.columns(2)

    with col7:
        st.metric(
            "Estimated annual carbon savings",
            f"{annual_carbon_savings_tonnes:,.0f} tonnes CO₂e/year"
        )

    with col8:
        st.metric(
            "Estimated lifetime carbon savings",
            f"{lifetime_carbon_savings_tonnes:,.0f} tonnes CO₂e"
        )

    st.subheader("Methodology")

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