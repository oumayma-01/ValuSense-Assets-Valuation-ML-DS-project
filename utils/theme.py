import streamlit as st


def inject_theme_css():
    dark = st.session_state.get("dark_mode", False)
    bg = "#0E1117" if dark else "#FFFFFF"
    bg2 = "#262730" if dark else "#F0F2F6"
    text = "#FAFAFA" if dark else "#0A0A0A"
    text_muted = "#9DA0A6" if dark else "#666"
    card_bg = "#1E2029" if dark else "#FAFBFC"
    border = "#333" if dark else "#E0E0E0"

    st.markdown(f"""
<style>
    .stApp {{ background-color: {bg}; color: {text}; }}
    .main-header {{ text-align: center; padding: 0.5rem 0 0 0; }}
    .main-header h1 {{ font-size: 2.2rem; margin-bottom: 0; color: {text}; }}
    .main-header p {{ font-size: 1rem; color: {text_muted}; }}
    .main-header .sub {{ font-size: 0.85rem; color: {text_muted}; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.8rem; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 0; }}
    .stTabs [data-baseweb="tab"] {{ color: {text}; padding: 0.5rem 1.5rem; font-size: 1rem; }}
    .stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.2rem; }}
    .stButton button {{ width: 100%; }}
    input[type="number"] {{ padding-right: 30px !important; }}
    input[type="number"]::-webkit-inner-spin-button {{ opacity: 1; width: 22px; height: 26px; cursor: pointer; transform: scale(1); }}
    .st-emotion-cache-1v0mbdj {{ color: {text}; }}
    section[data-testid="stSidebar"] .stMarkdown {{ color: {text}; }}
    .badge-row {{ display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; margin: 0.5rem 0; }}
    .badge {{ background: {bg2}; color: {text}; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.8rem; border: 1px solid {border}; }}
    .kpi-card {{ background: {card_bg}; padding: 1rem; border-radius: 0.5rem; text-align: center; border-left: 4px solid var(--kpi-color, #00A67E); }}
    .kpi-label {{ color: {text_muted}; font-size: 0.85rem; }}
    .kpi-value {{ font-size: 1.8rem; font-weight: bold; }}
    .pipeline-step {{ background: {bg2}; padding: 0.75rem; border-radius: 0.5rem; text-align: center; min-height: 120px; display: flex; flex-direction: column; justify-content: center; }}
    .pipeline-step .title {{ font-weight: bold; font-size: 1rem; color: {text}; }}
    .pipeline-step .desc {{ font-size: 0.75rem; color: {text_muted}; margin-top: 0.25rem; }}
    div.stDataFrame {{ color: {text}; }}
    .stAlert {{ color: {text}; }}
    h2, h3 {{ margin-top: 1.5rem; margin-bottom: 0.75rem; }}
    .stTabs + div {{ margin-top: 1rem; }}
</style>
""", unsafe_allow_html=True)

    if not dark:
        st.markdown(f"""
<style>
    .stApp header {{ background-color: #FFFFFF !important; }}
    .stApp .st-emotion-cache-1avcm0n {{ background-color: #FFFFFF !important; }}
    section[data-testid="stSidebar"] {{ background-color: #F8F9FA !important; }}
    .stApp [data-testid="stMetric"] {{ background-color: #FFFFFF; }}
    .stTabs [data-baseweb="tab"] {{ background-color: #F0F2F6; }}
    .st-bb {{ color: #0A0A0A !important; }}
</style>
""", unsafe_allow_html=True)
