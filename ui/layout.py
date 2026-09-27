"""Scoped layout rules for RTL text and the requested sidebar footer."""

import streamlit as st

from ui.i18n import translate

LINKEDIN_URL = "https://www.linkedin.com/in/abdelkader-bouzourine-data-analyst/"


def layout_css(language):
    direction, align = ("rtl", "right") if language == "ar" else ("ltr", "left")
    # Native bottom containers do not support sidebars. A flex footer stays in
    # document flow, so it cannot cover controls on small displays or at 200% zoom.
    return f"""
    <style>
    .st-key-sidebar_shell {{
        min-height: calc(100dvh - 7rem);
        justify-content: space-between;
    }}
    .st-key-professional_footer {{
        border-top: 1px solid var(--st-border-color, #d0d7de);
        padding-top: 1rem;
        margin-top: 1.5rem;
    }}
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"], [data-testid="stAlert"] {{
        direction: {direction};
        text-align: {align};
    }}
    [data-testid="stRadio"], [data-testid="stCheckbox"],
    [data-testid="stSelectbox"] [data-baseweb="select"] {{ direction: {direction}; }}
    [data-testid="stTextInput"] input {{ unicode-bidi: plaintext; }}
    [data-testid="stDataFrame"], [data-testid="stNumberInput"] input,
    [data-testid="stMetricValue"], code, pre {{ direction: ltr; }}
    .st-key-professional_footer strong {{ direction: ltr; unicode-bidi: isolate; display: inline-block; }}
    @media (max-height: 650px) {{
        .st-key-sidebar_shell {{ min-height: 0; }}
    }}
    </style>
    """


def render_styles(language):
    st.html(layout_css(language))


def render_contact(language):
    with st.container(key="professional_footer"):
        st.markdown("**Abdelkader Bouzourine**")
        st.caption(translate("Consultant en BI", language))
        st.link_button(
            translate("Voir mon profil LinkedIn", language),
            LINKEDIN_URL,
            icon=":material/open_in_new:",
            width="stretch",
        )
