import streamlit as st

st.set_page_config(
    page_title="UK Energy Infrastructure Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

project_explorer = st.Page(
    "pages/1_Project_Explorer.py",
    title="Project Explorer",
    url_path="project-explorer",
    default=True,
)

forecasting = st.Page(
    "pages/2_Forecasting.py",
    title="Forecasting",
    url_path="forecasting",
)

current_page = st.navigation(
    [project_explorer, forecasting],
    position="hidden",
)

current_title = getattr(current_page, "title", "Project Explorer")
sections = ["Project Explorer", "Forecasting"]

with st.container(key="platform_top_navigation"):
    selected_section = st.segmented_control(
        "Platform section",
        options=sections,
        default=current_title if current_title in sections else "Project Explorer",
        required=True,
        label_visibility="collapsed",
        width="content",
        key=f"platform_section_{current_title.lower().replace(' ', '_')}",
    )

if selected_section != current_title:
    if selected_section == "Project Explorer":
        st.switch_page(project_explorer)
    else:
        st.switch_page(forecasting)

st.divider()
# BEGIN SHARED NUMBER TYPOGRAPHY
st.markdown(
    '''
    <style>
    /*
    Use the same number typography on Project Explorer and Forecasting.
    This applies to header summary cards and all st.metric values.
    */
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricValue"] p,
    [data-testid="stMetricValue"] span {
        font-family: inherit !important;
        font-size: clamp(1.65rem, 2vw, 2rem) !important;
        font-weight: 650 !important;
        line-height: 1.08 !important;
        letter-spacing: -0.035em !important;
        font-variant-numeric: tabular-nums lining-nums !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] span {
        font-family: inherit !important;
        font-size: 0.92rem !important;
        font-weight: 560 !important;
        line-height: 1.25 !important;
        letter-spacing: -0.01em !important;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)
# END SHARED NUMBER TYPOGRAPHY


# BEGIN UNIFIED METRIC TYPOGRAPHY
st.markdown(
    '''
    <style>
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"],
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"],
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] * {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                     "Inter", "Segoe UI", sans-serif !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricLabel"],
    div[data-testid="stMetric"] div[data-testid="stMetricLabel"] * {
        font-size: 0.86rem !important;
        font-weight: 560 !important;
        line-height: 1.25 !important;
        letter-spacing: -0.01em !important;
        color: #526158 !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"],
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] *,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] p {
        font-size: 1.62rem !important;
        font-weight: 650 !important;
        line-height: 1.08 !important;
        letter-spacing: -0.035em !important;
        color: #17221C !important;
        font-variant-numeric: tabular-nums lining-nums !important;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)
# END UNIFIED METRIC TYPOGRAPHY


current_page.run()

st.markdown(
    '''
    <style>
    section[data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    

    .st-key-platform_top_navigation {
        position: relative !important;
        z-index: 20 !important;
        margin-top: 4.25rem !important;
        margin-bottom: 0.15rem !important;
        overflow: visible !important;
    }

    .st-key-platform_top_navigation,
    .st-key-platform_top_navigation > div,
    .st-key-platform_top_navigation [data-testid="stSegmentedControl"] {
        min-height: 2.75rem !important;
        overflow: visible !important;
    }

    .st-key-platform_top_navigation [role="radiogroup"] {
        box-shadow: 0 1px 2px rgba(23, 34, 28, 0.05);
    }

    h1 {
        color: #17221C !important;
        font-size: clamp(2.25rem, 4vw, 3.65rem) !important;
        font-weight: 760 !important;
        letter-spacing: -0.045em !important;
        line-height: 1.04 !important;
        margin-bottom: 0.55rem !important;
    }

    h2 {
        color: #17221C !important;
        font-weight: 720 !important;
        letter-spacing: -0.025em !important;
        margin-top: 1.4rem !important;
    }

    h3 {
        color: #25332B !important;
        font-weight: 680 !important;
        letter-spacing: -0.015em !important;
    }

    p, li, label {
        color: #33423A;
    }

    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #DDE5DF !important;
        border-radius: 18px !important;
        padding: 1rem 1.05rem !important;
        box-shadow: 0 8px 24px rgba(23, 34, 28, 0.035) !important;
        min-height: 108px;
    }

    

    

    [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #DDE5DF !important;
        border-radius: 14px !important;
        overflow: hidden !important;
    }

    [data-testid="stTabs"] [role="tablist"] {
        background: #FFFFFF !important;
        border: 1px solid #DDE5DF !important;
        border-radius: 14px !important;
        padding: 0.35rem !important;
        gap: 0.2rem !important;
        box-shadow: 0 5px 18px rgba(23, 34, 28, 0.025) !important;
    }

    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 10px !important;
        color: #33423A !important;
        font-weight: 600 !important;
        padding: 0.6rem 0.82rem !important;
    }

    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #172B22 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #FFFFFF !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        font-weight: 650 !important;
        border-radius: 999px !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #DDE5DF !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        background: #FFFFFF !important;
    }

    [data-testid="stPlotlyChart"] {
        border-radius: 14px !important;
        overflow: hidden !important;
    }

    hr {
        border-color: #DDE5DF !important;
        margin-top: 0.65rem !important;
        margin-bottom: 1.25rem !important;
    }

    @media (max-width: 700px) {
        .st-key-platform_top_navigation {
            margin-top: 3.75rem !important;
        }

        h1 {
            font-size: 2.2rem !important;
        }
    }
    </style>
    ''',
    unsafe_allow_html=True,
)

# BEGIN SHARED PLATFORM WIDTH
st.markdown(
    '''
    <style>
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer,
    .block-container {
        width: 100% !important;
        max-width: none !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"],
        .stMainBlockContainer,
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }
    </style>
    ''',
    unsafe_allow_html=True,
)
# END SHARED PLATFORM WIDTH

