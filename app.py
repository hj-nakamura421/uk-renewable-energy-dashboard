import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

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

st.plotly_chart(fig1, use_container_width=True)

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

st.plotly_chart(fig2, use_container_width=True)

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