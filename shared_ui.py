from __future__ import annotations

import streamlit as st


GITHUB_URL = "https://github.com/hj-nakamura421/uk-renewable-energy-dashboard"


def apply_shared_control_styles() -> None:
    """Apply one control language across the Explorer and Forecasting pages."""
    st.markdown(
        """
        <style>
        [data-testid="stSlider"] {
            padding: 0.25rem 0.15rem 0.75rem;
        }

        [data-testid="stSlider"] label p {
            color: #17221C !important;
            font-size: 0.88rem !important;
            font-weight: 650 !important;
            letter-spacing: -0.005em;
        }

        [data-testid="stSlider"] [data-baseweb="slider"] {
            margin-top: 0.45rem;
        }

        [data-testid="stSlider"] [role="slider"] {
            background: #0E6B4F !important;
            border: 2px solid #FFFFFF !important;
            box-shadow:
                0 0 0 1px #0E6B4F,
                0 3px 9px rgba(14, 107, 79, 0.24) !important;
        }

        [data-testid="stSlider"] [data-testid="stThumbValue"] {
            color: #0E6B4F !important;
            font-size: 0.78rem !important;
            font-weight: 700 !important;
        }

        [data-testid="stSlider"] [data-testid="stTickBar"] {
            color: #718078 !important;
            font-size: 0.72rem !important;
        }

        [data-testid="stSlider"] div[role="progressbar"] {
            background-color: #0E6B4F !important;
        }

        [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
            border-radius: 999px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_portfolio_footer() -> None:
    """Render the same portfolio footer on every platform page."""
    apply_shared_control_styles()
    st.markdown(
        '''
        <style>
        .st-key-portfolio_footer {
            margin-top: 3.25rem;
            padding-top: 0.35rem;
        }

        .st-key-portfolio_footer hr {
            margin-bottom: 1.4rem !important;
        }

        .st-key-portfolio_footer p {
            margin-bottom: 0.18rem;
        }

        .st-key-portfolio_footer [data-testid="stCaptionContainer"] {
            margin-top: -0.2rem;
        }

        .st-key-portfolio_footer a {
            color: #0E6B4F !important;
            font-weight: 650;
            text-decoration: none;
        }

        .st-key-portfolio_footer a:hover {
            text-decoration: underline;
        }
        </style>
        ''',
        unsafe_allow_html=True,
    )

    with st.container(key="portfolio_footer"):
        st.divider()
        identity, code, spacer = st.columns(
            [4.4, 1.35, 0.25],
            vertical_alignment="top",
        )

        with identity:
            st.markdown("**HJ Nakamura**")
            st.caption("Mechanical Engineering, Imperial College London")

        with code:
            st.markdown("**Code**")
            st.markdown(f"[GitHub repository]({GITHUB_URL})")
