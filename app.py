import streamlit as st

st.set_page_config(
    page_title="ValuSense - Asset Valuation Method Recommender",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.markdown("### Settings")
    dark = st.toggle("Dark mode", value=st.session_state.dark_mode, key="dark_toggle")
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()

theme = "dark" if st.session_state.dark_mode else "light"

if theme == "dark":
    bg = "#0E1117"
    bg2 = "#262730"
    text = "#FAFAFA"
    text_muted = "#9DA0A6"
    card_bg = "#1E2029"
    border = "#333"
else:
    bg = "#FFFFFF"
    bg2 = "#F0F2F6"
    text = "#0A0A0A"
    text_muted = "#666"
    card_bg = "#FAFBFC"
    border = "#E0E0E0"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg}; color: {text}; }}
    .main-header {{ text-align: center; padding: 1rem 0; }}
    .main-header h1 {{ font-size: 2.5rem; margin-bottom: 0; color: {text}; }}
    .main-header p {{ font-size: 1.1rem; color: {text_muted}; }}
    .main-header .sub {{ font-size: 0.9rem; color: {text_muted}; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.8rem; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 0; }}
    .stTabs [data-baseweb="tab"] {{ color: {text}; }}
    .stButton button {{ width: 100%; }}
    input[type="number"] {{ padding-right: 30px !important; }}
    input[type="number"]::-webkit-inner-spin-button {{
        opacity: 1;
        width: 22px;
        height: 26px;
        cursor: pointer;
        transform: scale(1);
    }}
    .st-emotion-cache-1v0mbdj {{ color: {text}; }}
    .stMarkdown, .stText, p, li, h1, h2, h3, h4, h5, h6 {{ color: {text}; }}
    section[data-testid="stSidebar"] .stMarkdown {{ color: {text}; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="main-header">
    <h1>ValuSense</h1>
    <p>Intelligent Financial Asset Valuation Method Recommendation</p>
    <p class="sub">
        ML-powered  |  IFRS 13 Compliant  |  SHAP Explainable
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
**ValuSense** recommends the optimal valuation method for any financial asset using a trained XGBoost model
with IFRS 13 fair value hierarchy enforcement and SHAP-based explainability.

### Pages
- **Recommend** — Describe an asset and get a valuation method recommendation with SHAP explanation
- **Scenarios** — Run the 10 predefined test scenarios
- **Valuation Engine** — Direct access to any of the 10 valuation engines
- **Model Insights** — SHAP feature importance, model comparison, confusion matrices
- **About** — Project documentation and methodology

### Supported Asset Classes
Equities  |  Bonds  |  Options  |  Commodities  |  Currencies  |  Derivatives

### 10 Valuation Methods
Mark-to-Market  |  DCF  |  DDM  |  Black-Scholes  |  Binomial Tree  |  Monte Carlo
Cost-of-Carry  |  Forward Pricing  |  Relative Valuation  |  Credit Model
""")
