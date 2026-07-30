from __future__ import annotations

import streamlit as st


GITHUB_URL = "https://github.com/hj-nakamura421/uk-renewable-energy-dashboard"


def render_portfolio_footer() -> None:
    """Render the same portfolio footer on every platform page."""
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
