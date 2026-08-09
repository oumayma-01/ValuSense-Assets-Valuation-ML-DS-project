"""ValuSense "Ledger" design system.

One shared theming module for the whole app, injected identically on every page
via `inject_theme_css()`. Provides:

* Design tokens (CSS custom properties) for light + dark themes, emitted
  directly from Python based on the active `st.session_state.theme`, so the
  correct colors are always applied — no dependence on fragile JS.
* A `data-theme` attribute applied to <html> by an injected script (best
  effort, for anything that reads the attribute), driven by the in-app sidebar
  toggle (defaults from the system / config theme.base).
* Shared components: page/section headers, KPI cards, feature-card grids,
  status pills, a styled ledger table, pipeline steps and the scrolling ticker.
* The shared sidebar controls (theme toggle + audience view).

Visual language: a precise quant/regulatory tool. IBM Plex Sans for UI/headings,
JetBrains Mono for every number/code/model output so data reads as data. A calm
functional color system (accent for nav/actions, status colors only for
pass/override/violation). Every color comes from the token set — no hardcoded
hex in any component.
"""

import streamlit as st

from utils.meta import load_model_metadata, load_agent_metadata

LIGHT = "light"
DARK = "dark"

AUDIENCE_QUICK = "Quick overview"
AUDIENCE_FULL = "Full detail"

# Legacy color names -> signal tones (old pages used raw green/blue/orange/red).
_TONE_MAP = {
    "green": "success",
    "blue": "accent",
    "purple": "accent",
    "orange": "warning",
    "yellow": "warning",
    "red": "danger",
}

_TONE_CLASS = {
    "success": "tone-success",
    "warning": "tone-warning",
    "danger": "tone-danger",
    "accent": "tone-accent",
    "neutral": "tone-neutral",
}


# ---------------------------------------------------------------------------
# Theme state
# ---------------------------------------------------------------------------

def _detect_system_theme() -> str:
    try:
        base = st.get_option("theme.base")
        if base in (LIGHT, DARK):
            return base
    except Exception:
        pass
    try:
        ctx = getattr(st, "context", None)
        theme = getattr(ctx, "theme", None) or {}
        base = theme.get("base") if isinstance(theme, dict) else None
        if base in (LIGHT, DARK):
            return base
    except Exception:
        pass
    return LIGHT


def init_theme() -> None:
    if "theme" not in st.session_state:
        try:
            param = st.query_params.get("theme")
            if param in (LIGHT, DARK):
                st.session_state.theme = param
                return
        except Exception:
            pass
        st.session_state.theme = _detect_system_theme()


def get_theme() -> str:
    return st.session_state.get("theme", LIGHT)


def is_dark() -> bool:
    return get_theme() == DARK


# ---------------------------------------------------------------------------
# Audience helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------

def get_audience_mode() -> str:
    return st.session_state.get("audience_mode", AUDIENCE_QUICK)


def is_full_detail() -> bool:
    return get_audience_mode() == AUDIENCE_FULL


def _tone(tone: str) -> str:
    """Normalise a user-supplied tone name (accepts legacy color names)."""
    tone = (tone or "neutral").lower()
    return _TONE_MAP.get(tone, tone if tone in _TONE_CLASS else "neutral")


def _tone_class(tone: str) -> str:
    return _TONE_CLASS[_tone(tone)]


# ---------------------------------------------------------------------------
# Tokens + stylesheet
# ---------------------------------------------------------------------------

_FONTS = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Sans:wght@400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500;600&display=swap');"
)

_COMMON_TOKENS = """
  --font-heading: "IBM Plex Sans", Inter, "Segoe UI", system-ui, sans-serif;
  --font-body: "IBM Plex Sans", Inter, "Segoe UI", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", "IBM Plex Mono", Consolas, "Courier New", monospace;
  --fs-13: 13px;
  --fs-14: 14px;
  --fs-16: 16px;
  --fs-20: 20px;
  --fs-28: 28px;
  --fs-36: 36px;
  --content-max: 1150px;
"""

_LIGHT_TOKENS = """
  --bg: #F7F8FA;
  --surface: #FFFFFF;
  --surface-2: #FCFCFD;
  --text: #0B0E14;
  --text-secondary: #5B6270;
  --border: #E2E5EA;
  --accent: #2DD4BF;
  --success: #22C55E;
  --warning: #F5A623;
  --error: #EF4444;
  --accent-soft: rgba(45, 212, 191, 0.14);
  --success-soft: rgba(34, 197, 94, 0.12);
  --warning-soft: rgba(245, 166, 35, 0.12);
  --error-soft: rgba(239, 68, 68, 0.12);
  --neutral-soft: rgba(91, 98, 112, 0.12);
  --shadow: 0 1px 2px rgba(11, 14, 20, 0.06);
  --on-accent: #0B0E14;
"""

# Dark mode: same accent/success/warning/error as light — only the neutrals flip.
_DARK_TOKENS = """
  --bg: #0B0E14;
  --surface: #141821;
  --surface-2: #1A1F2B;
  --text: #F2F4F8;
  --text-secondary: #8B92A5;
  --border: #232838;
  --accent: #2DD4BF;
  --success: #22C55E;
  --warning: #F5A623;
  --error: #EF4444;
  --accent-soft: rgba(45, 212, 191, 0.16);
  --success-soft: rgba(34, 197, 94, 0.14);
  --warning-soft: rgba(245, 166, 35, 0.14);
  --error-soft: rgba(239, 68, 68, 0.14);
  --neutral-soft: rgba(139, 146, 165, 0.14);
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
  --on-accent: #0B0E14;
"""

# Pre-generated (training-time) matplotlib PNGs keep white figure areas; in
# dark mode soften them so they don't glare against the app background.
_DARK_EXTRAS = """
html.dark [data-testid="stImage"] img,
html[data-theme="dark"] [data-testid="stImage"] img {
  filter: brightness(0.88) contrast(1.04);
}
"""

# Everything below is emitted verbatim for BOTH themes. It references the CSS
# custom properties (--bg, --text, ...) which are already set to the correct
# values for the active theme on `html`, so the same stylesheet serves both.
# Text colors use !important to win over Streamlit's native theme colors.
_BODY_CSS = """
/* ---- base app chrome ---- */
.stApp,
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
}
header[data-testid="stHeader"] { background: transparent; }

/* ---- headings: cover every heading API + markdown level ---- */
h1,
h2,
h3,
h4,
h5,
h6,
[data-testid="stHeading"] h1,
[data-testid="stHeading"] h2,
[data-testid="stHeading"] h3,
[data-testid="stHeading"] h4,
[data-testid="stHeading"] h5,
[data-testid="stHeading"] h6,
.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3,
.stMarkdown h4,
.stMarkdown h5,
.stMarkdown h6 {
  color: var(--text) !important;
  font-family: var(--font-heading);
}

/* ---- markdown body text ---- */
.stMarkdown,
.stMarkdown p,
.stMarkdown li,
.stMarkdown ul,
.stMarkdown ol,
.stMarkdown blockquote,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
  color: var(--text) !important;
  font-family: var(--font-body);
  line-height: 1.6;
}

/* ---- captions ---- */
.stCaption,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] [data-testid="stMarkdownContainer"] p {
  color: var(--text-secondary) !important;
}

/* ---- widget labels & option text ---- */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] #stMarkdownContainer p,
[data-testid="stWidgetLabel"] p,
#stMarkdownContainer p {
  color: var(--text) !important;
}
[data-testid="stRadio"] label,
[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] label p,
[data-testid="stSelectbox"] label,
[data-testid="stSelectbox"] label p,
[data-testid="stMultiSelect"] label,
[data-testid="stMultiSelect"] label p,
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSlider"] label,
[data-testid="stDateInput"] label,
[data-testid="stTimeInput"] label,
[data-testid="stFileUploader"] label {
  color: var(--text) !important;
}

/* ---- native inputs & selects ---- */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
[data-testid="stColorPicker"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

/* dropdown list (baseweb popover) */
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [data-baseweb="listbox"],
[data-baseweb="menu"] > div,
[data-baseweb="popover"] [data-baseweb="menu"] li,
[data-baseweb="select"] [data-baseweb="listbox"] {
  background: var(--surface) !important;
  color: var(--text) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] li:hover,
[data-baseweb="select"] [data-baseweb="listbox"] li:hover {
  background: var(--surface-2) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] li[aria-selected="true"],
[data-baseweb="select"] [data-baseweb="listbox"] li[aria-selected="true"] {
  background: var(--accent-soft) !important;
  color: var(--accent) !important;
}

/* ---- interactive controls always accent (never red) ----
   Covers the cases where Streamlit's baseweb theme leaks its default
   primary color; force every normal selected/active control to teal. */
[data-testid="stRadio"] label[data-baseweb="radio"] input:checked + div[data-baseweb="radio"],
[data-testid="stRadio"] label[data-baseweb="radio"] input:checked ~ div[data-baseweb="radio"] {
  border-color: var(--accent) !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"] input:checked + div[data-baseweb="radio"] > div,
[data-testid="stRadio"] label[data-baseweb="radio"] input:checked ~ div[data-baseweb="radio"] > div {
  background-color: var(--accent) !important;
}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] input:checked + span[data-baseweb="checkbox"],
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] input:checked ~ span[data-baseweb="checkbox"] {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] span[data-baseweb="checkbox"] svg {
  stroke: var(--on-accent) !important;
}
[data-testid="stSlider"] [role="slider"],
[data-testid="stSlider"] [data-testid="stSliderThumb"] {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
}
[data-testid="stSlider"] div[data-baseweb="slider"] div div {
  background-color: var(--accent) !important;
}
[data-testid="stSlider"] p {
  color: var(--text-secondary) !important;
}

/* ---- buttons ---- */
.stButton button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"] {
  background: var(--surface);
  color: var(--text) !important;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
[data-testid="stBaseButton-primary"] {
  background: var(--accent);
  border: 1px solid var(--accent);
  color: var(--on-accent) !important;
  font-weight: 600;
}
.stButton button:hover,
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-tertiary"]:hover {
  border-color: var(--accent);
  color: var(--accent) !important;
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--accent);
  color: var(--on-accent) !important;
  filter: brightness(0.96);
}

/* ---- code / json ---- */
.stCode,
.stCode pre,
.stCode code,
.stCodeBlock,
[data-testid="stCodeBlock"],
[data-testid="stMarkdownPre"] pre {
  color: var(--text) !important;
  font-family: var(--font-mono);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
}
[data-testid="stJson"] {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text) !important;
  font-family: var(--font-mono);
}
[data-testid="stJson"] * { color: var(--text) !important; }

/* ---- alerts / info / success / warning / error ---- */
.stAlert {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
}
[data-testid="stAlert"] p,
.stAlert p,
[data-testid="stNotification"] p {
  color: var(--text) !important;
}

/* ---- images ---- */
.stImage img {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px;
}

/* ---- progress ---- */
[data-testid="stProgress"] > div > div {
  background: var(--surface-2);
  border: 1px solid var(--border);
}
[data-testid="stProgress"] [role="progressbar"] {
  background: var(--accent);
}
[data-testid="stProgress"] p {
  color: var(--text) !important;
}

/* ---- sidebar ---- */
section[data-testid="stSidebar"] {
  background: var(--surface);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebarContent"] { color: var(--text); }
[data-testid="stSidebarContent"] p { color: var(--text) !important; }
[data-testid="stSidebarContent"] h1,
[data-testid="stSidebarContent"] h2,
[data-testid="stSidebarContent"] h3,
[data-testid="stSidebarContent"] h4 { color: var(--text) !important; }

/* sidebar page navigation — the base (light) theme paints it dark */
[data-testid="stSidebarNav"] * {
  color: var(--text-secondary) !important;
}
[data-testid="stSidebarNav"] a:hover { color: var(--text) !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
  color: var(--accent) !important;
  font-weight: 600;
  background: var(--accent-soft);
  box-shadow: inset 3px 0 0 var(--accent);
}

/* technical/reference pages grouped under a label */
[data-testid="stSidebarNav"] a[href*="05_Model_Insights"] {
  margin-top: 2.1rem;
  position: relative;
}
[data-testid="stSidebarNav"] a[href*="05_Model_Insights"]::before {
  content: "Technical Documentation";
  position: absolute;
  top: -1.5rem;
  left: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-secondary);
  white-space: nowrap;
}

/* ---- metric ---- */
[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.9rem 1rem;
  box-shadow: var(--shadow);
}
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; font-size: var(--fs-13); }
[data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-family: var(--font-mono);
  font-size: var(--fs-28);
  font-weight: 600;
}
[data-testid="stMetricDelta"] { color: var(--success) !important; }

/* ---- tabs ---- */
.stTabs [data-baseweb="tab"],
[data-testid="stTabs"] [role="tab"] p {
  color: var(--text-secondary) !important;
  font-size: var(--fs-14);
}
.stTabs [data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p {
  color: var(--accent) !important;
  border-bottom-color: var(--accent);
}
.stTabs [data-baseweb="tab-panel"],
[data-testid="stTabs"] [role="tabpanel"] { color: var(--text); }

/* ---- expander / details ---- */
details,
[data-testid="stExpander"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
}
details summary,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
  color: var(--text) !important;
}

/* ---- chat (AI Assistant) ---- */
[data-testid="stChatMessage"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
  color: var(--text) !important;
}
[data-testid="stChatInput"] textarea {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}

/* ---- dataframes ---- */
[data-testid="stDataFrame"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}
html.dark [data-testid="stDataFrame"] .dvn-scroller,
html[data-theme="dark"] [data-testid="stDataFrame"] .dvn-scroller,
html.dark [data-testid="stDataFrame"] .glide-data-grid,
html[data-theme="dark"] [data-testid="stDataFrame"] .glide-data-grid,
html.dark [data-testid="stDataFrame"] .gdg-header,
html[data-theme="dark"] [data-testid="stDataFrame"] .gdg-header,
html.dark [data-testid="stDataFrame"] canvas,
html[data-theme="dark"] [data-testid="stDataFrame"] canvas {
  background: var(--surface) !important;
  color: var(--text) !important;
}

/* ---- ledger: cards / badges / grids ---- */
.ledger-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 1rem 1.1rem;
  height: 100%;
}
.stat-card { display: flex; flex-direction: column; justify-content: space-between; }
.stat-card .lc-label {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.stat-card .lc-value {
  font-family: var(--font-mono);
  font-size: var(--fs-28);
  font-weight: 600;
  color: var(--text);
  margin: 0.4rem 0 0.2rem;
  line-height: 1.15;
}
.stat-card .lc-caption { color: var(--text-secondary); font-size: var(--fs-13); line-height: 1.45; }
.stat-card .lc-icon { font-size: var(--fs-16); }

.tone-neutral { border-left: 3px solid var(--border); }
.tone-success { border-left: 3px solid var(--success); }
.tone-warning { border-left: 3px solid var(--warning); }
.tone-danger { border-left: 3px solid var(--error); }
.tone-accent { border-left: 3px solid var(--accent); }

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.22rem 0.7rem;
  border-radius: 999px;
  font-size: var(--fs-13);
  font-weight: 600;
  font-family: var(--font-body);
  letter-spacing: 0.02em;
  white-space: nowrap;
  border: 1px solid var(--border);
  border-left: 3px solid currentColor;
}
.badge.tone-success { background: var(--success-soft); color: var(--success); }
.badge.tone-warning { background: var(--warning-soft); color: var(--warning); }
.badge.tone-danger  { background: var(--error-soft);  color: var(--error); }
.badge.tone-accent  { background: var(--accent-soft);  color: var(--accent); }
.badge.tone-neutral { background: var(--neutral-soft); color: var(--text-secondary); }
.badge-row { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; margin: 0.25rem 0; }

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 0.9rem 1rem;
  display: flex;
  align-items: center;
  height: 100%;
}
.feature-card .fc-label { font-size: var(--fs-14); color: var(--text); line-height: 1.4; font-weight: 600; }
.feature-card .fc-desc { font-size: var(--fs-13); color: var(--text-secondary); line-height: 1.45; margin-top: 0.15rem; }

.pipeline-step {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 0.9rem 0.75rem;
  text-align: center;
  min-height: 108px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.pipeline-step .step-icon { font-size: var(--fs-20); }
.pipeline-step .title { font-weight: 600; font-size: var(--fs-14); color: var(--text); margin-top: 0.25rem; }
.pipeline-step .desc { font-size: 12px; color: var(--text-secondary); margin-top: 0.2rem; line-height: 1.4; }

/* ---- ledger table ---- */
.ledger-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  font-family: var(--font-body);
  font-size: var(--fs-13);
}
.ledger-table thead th {
  background: var(--surface-2);
  color: var(--text-secondary);
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--border);
}
.ledger-table tbody td {
  color: var(--text);
  padding: 0.55rem 0.9rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.ledger-table tbody tr:nth-child(even) { background: var(--surface-2); }
.ledger-table tbody tr:last-child td { border-bottom: none; }
.ledger-table td.num { font-family: var(--font-mono); }

.stMarkdown table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  font-size: var(--fs-13);
}
.stMarkdown th {
  background: var(--surface-2);
  color: var(--text-secondary) !important;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--border);
}
.stMarkdown td {
  color: var(--text) !important;
  padding: 0.55rem 0.9rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.stMarkdown tr:nth-child(even) td { background: var(--surface-2); }
.stMarkdown tr:last-child td { border-bottom: none; }

/* ---- headers & rules ---- */
.page-header { margin: 0.4rem 0 0; }
.kicker {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.35rem;
}
.ledger-title {
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--fs-36);
  letter-spacing: -0.015em;
  color: var(--text);
  margin: 0;
  line-height: 1.15;
}
.ledger-subtitle { color: var(--text-secondary); font-size: var(--fs-16); margin: 0.4rem 0 0; max-width: 74ch; line-height: 1.55; }

.section-title {
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--fs-20);
  letter-spacing: -0.005em;
  color: var(--text);
  margin: 0 0 0.25rem;
}
.section-subtitle { color: var(--text-secondary); font-size: var(--fs-14); margin: 0 0 0.9rem; max-width: 74ch; }

.hairline { border: 0; border-top: 1px solid var(--border); margin: 1.25rem 0 1.75rem; }

/* ---- empty state ---- */
.empty-state {
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: 8px;
  padding: 1.6rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 1.4rem; }
.empty-state .es-title { font-weight: 600; color: var(--text); font-size: var(--fs-16); margin-top: 0.4rem; }
.empty-state .es-msg { color: var(--text-secondary); font-size: var(--fs-14); margin-top: 0.3rem; }

/* ---- legacy classes kept for compatibility ---- */
.main-header { text-align: center; padding: 0.5rem 0 0; }
.main-header h1 { font-family: var(--font-heading); font-weight: 600; font-size: var(--fs-36); margin: 0; color: var(--text); }
.main-header p { font-size: var(--fs-16); color: var(--text-secondary); }
.main-header .sub { font-size: 12px; color: var(--text-secondary); font-family: var(--font-mono); letter-spacing: 0.1em; }
.main-header .hero-prop { font-size: var(--fs-16); color: var(--text); max-width: 760px; margin: 0.5rem auto 0; line-height: 1.55; }

.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: var(--shadow);
  padding: 1rem;
  text-align: center;
  border-left: 4px solid var(--kpi-color, var(--accent));
  height: 100%;
}
.kpi-label { color: var(--text-secondary); font-size: var(--fs-13); }
.kpi-value { font-size: var(--fs-28); font-weight: 600; font-family: var(--font-mono); }
.kpi-caption { color: var(--text-secondary); font-size: 12px; margin-top: 0.25rem; line-height: 1.3; }

/* ---- sidebar brand + controls ---- */
.sidebar-brand { margin: 0.1rem 0 0.9rem; }
.sidebar-brand .sb-name { font-family: var(--font-heading); font-weight: 600; font-size: var(--fs-16); color: var(--text); }
.sidebar-brand .sb-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-top: 0.1rem;
}
.sidebar-block { padding: 0.35rem 0; }
.sidebar-block .sb-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0.6rem 0 0.35rem;
}

/* ---- ticker ---- */
.ticker-wrap {
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 8px;
  box-shadow: var(--shadow);
  margin: 0.25rem 0 1.75rem;
}
.ticker-track {
  display: flex;
  align-items: center;
  white-space: nowrap;
  width: max-content;
  animation: ticker-scroll 60s linear infinite;
}
.ticker-item {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  padding: 0.5rem 0.9rem;
  display: inline-flex;
  align-items: center;
  gap: 0.9rem;
}
.ticker-item .sep { color: var(--accent); }
@keyframes ticker-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) {
  .ticker-track { animation: none; flex-wrap: wrap; }
  .ticker-item { padding: 0.4rem 0.7rem; }
}
"""


def _tokens_css(theme: str) -> str:
    dark = theme == DARK
    tokens = _DARK_TOKENS if dark else _LIGHT_TOKENS
    scheme = "dark" if dark else "light"
    extras = _DARK_EXTRAS if dark else ""
    return (
        f"<style>\n{_FONTS}\n"
        f"html {{ color-scheme: {scheme}; {_COMMON_TOKENS}{tokens} }}\n"
        f"{_BODY_CSS}\n{extras}\n</style>"
    )


def _apply_data_theme() -> None:
    """Set a `light`/`dark` class (and `data-theme` attribute) on <html> as a
    best-effort signal for anything that reads the attribute. Styling itself is
    driven by `_tokens_css` (Python-side), so this is not load-bearing."""
    try:
        theme = get_theme()
        st.components.v1.html(
            f"<script>"
            f"var el = window.parent.document.documentElement;"
            f"el.classList.remove('light','dark');"
            f"el.classList.add('{theme}');"
            f"el.setAttribute('data-theme','{theme}');"
            f"</script>",
            height=0,
            width=0,
        )
    except Exception:
        pass


def inject_theme_css() -> None:
    """Inject fonts, tokens, component styles and apply the active theme."""
    init_theme()
    st.markdown(_tokens_css(get_theme()), unsafe_allow_html=True)
    _apply_data_theme()


# ---------------------------------------------------------------------------
# Sidebar controls (shared by every page)
# ---------------------------------------------------------------------------

def theme_sidebar() -> None:
    """Brand header + theme toggle + audience selector for the sidebar."""
    init_theme()
    st.markdown(
        "<div class='sidebar-brand'>"
        "<div class='sb-name'>ValuSense</div>"
        "<div class='sb-tag'>Ledger · IFRS 13</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='sidebar-block'>"
        "<div class='sb-label'>Theme</div></div>",
        unsafe_allow_html=True,
    )
    theme = get_theme()
    choice = st.radio(
        "Theme",
        options=["Light", "Dark"],
        index=0 if theme == LIGHT else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio",
        help="Switch the whole app (cards, charts and tables) between light and dark.",
    )
    if (choice == "Dark") != (theme == DARK):
        st.session_state.theme = DARK if choice == "Dark" else LIGHT
        st.rerun()

    st.markdown(
        "<div class='sidebar-block'>"
        "<div class='sb-label'>Audience</div></div>",
        unsafe_allow_html=True,
    )
    audience = st.radio(
        "Audience",
        options=[AUDIENCE_QUICK, AUDIENCE_FULL],
        index=0 if get_audience_mode() == AUDIENCE_QUICK else 1,
        label_visibility="collapsed",
        key="audience_radio",
        help="Quick overview hides technical detail for non-specialists. "
             "Full detail shows metrics, SHAP internals and IFRS citations.",
    )
    if audience != get_audience_mode():
        st.session_state.audience_mode = audience
        st.rerun()


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def hairline() -> None:
    st.markdown("<hr class='hairline'>", unsafe_allow_html=True)


def page_header(title: str, subtitle=None, kicker=None) -> None:
    parts = ["<div class='page-header'>"]
    if kicker:
        parts.append(f"<div class='kicker'>{kicker}</div>")
    parts.append(f"<h1 class='ledger-title'>{title}</h1>")
    if subtitle:
        parts.append(f"<p class='ledger-subtitle'>{subtitle}</p>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
    hairline()


def section_header(title: str, subtitle=None) -> None:
    html = f"<h2 class='section-title'>{title}</h2>"
    if subtitle:
        html += f"<p class='section-subtitle'>{subtitle}</p>"
    st.markdown(html, unsafe_allow_html=True)


def kpi_card(label: str, value: str, caption: str = "", tone: str = "neutral",
             icon=None) -> str:
    """KPI card: small secondary label, big JetBrains Mono number (--text),
    and a colored left border (success/warning/error/accent/neutral)."""
    cls = _tone_class(tone)
    icon_html = f"<span class='lc-icon'>{icon}</span>" if icon else ""
    return (
        f"<div class='ledger-card stat-card {cls}'>"
        f"<div class='lc-label'>{icon_html} {label}</div>"
        f"<div class='lc-value'>{value}</div>"
        f"<div class='lc-caption'>{caption}</div>"
        f"</div>"
    )


stat_card = kpi_card  # backward-compatible alias


def render_stat_cards(stats, columns: int = 4) -> None:
    """Render a row of KPI cards.

    Each stat: {"label", "value", "caption" (optional), "tone" (optional)}.
    `tone` accepts success|warning|error|accent|neutral or legacy colors.
    """
    n = len(stats)
    cols = st.columns(min(columns, n))
    for i, stat in enumerate(stats):
        with cols[i % len(cols)]:
            st.markdown(
                kpi_card(
                    stat["label"],
                    stat["value"],
                    stat.get("caption", ""),
                    tone=stat.get("tone", "neutral"),
                    icon=stat.get("icon"),
                ),
                unsafe_allow_html=True,
            )


def render_stat_strip(stats, columns=None):
    """Backward-compatible alias of render_stat_cards."""
    return render_stat_cards(stats, columns=columns or min(len(stats), 6))


def status_badge(text: str, tone: str = "neutral", icon=None) -> str:
    """Status pill with a colored soft background, used for confidence score
    and IFRS compliant/overridden status."""
    cls = _tone_class(tone)
    icon_html = f"<span>{icon}</span>" if icon else ""
    return f"<span class='badge {cls}'>{icon_html}{text}</span>"


badge = status_badge  # backward-compatible alias


def feature_card(icon=None, title="", desc="") -> str:
    """Text-only card: bold term + short description, accent left border.

    The `icon` argument is accepted for backward compatibility and ignored —
    feature cards are deliberately text-only, with a plain accent border as
    the only visual marker."""
    desc_html = f"<div class='fc-desc'>{desc}</div>" if desc else ""
    return (
        f"<div class='feature-card'>"
        f"<div class='fc-body'>"
        f"<div class='fc-label'>{title}</div>{desc_html}"
        f"</div></div>"
    )


def feature_grid(items, columns: int = 4) -> None:
    """Grid of text-only feature cards.

    Each item is a dict {"title","desc"} (or {"label","desc"}) or a
    (title, desc) tuple. Icons are ignored."""
    cols = st.columns(min(columns, len(items)))
    for i, item in enumerate(items):
        if isinstance(item, dict):
            title = item.get("title") or item.get("label", "")
            desc = item.get("desc", "")
        else:
            title = item[0]
            desc = item[1] if len(item) > 1 else ""
        with cols[i % len(cols)]:
            st.markdown(feature_card(None, title, desc), unsafe_allow_html=True)


def render_pipeline(steps, columns=None) -> None:
    """Steps: (icon, title, desc) or (title, desc)."""
    cols = st.columns(columns or min(len(steps), 6))
    for i, step in enumerate(steps):
        if len(step) == 3:
            icon, title, desc = step
        else:
            icon, title, desc = None, step[0], step[1]
        icon_html = f"<div class='step-icon'>{icon}</div>" if icon else ""
        with cols[i % len(cols)]:
            st.markdown(
                f"<div class='pipeline-step'>{icon_html}"
                f"<div class='title'>{title}</div>"
                f"<div class='desc'>{desc}</div></div>",
                unsafe_allow_html=True,
            )


def render_table(df, numeric_mono: bool = True, columns=None, mono_cols=None) -> None:
    """Styled ledger table: alternating rows, monospace numeric columns.

    Replaces bare st.dataframe for report-style tables. Pass an optional list
    of column names to render as monospace numbers (defaults to numeric dtype).
    `mono_cols` forces specific columns to monospace even when not numeric.
    """
    import html as _html

    if df is None or df.empty:
        st.info("No data to display.")
        return

    sub = df[columns] if columns else df
    num_cols = set()
    if numeric_mono:
        num_cols = set(sub.select_dtypes(include=["number"]).columns)
    if mono_cols:
        num_cols |= set(mono_cols)

    header = "".join(
        f"<th>{_html.escape(str(c))}</th>" for c in sub.columns
    )
    rows = []
    for _, row in sub.iterrows():
        cells = []
        for c in sub.columns:
            v = row[c]
            if v is None:
                cell = ""
            elif isinstance(v, float):
                cell = f"{v:,.4f}" if abs(v) < 1e6 else f"{v:,.0f}"
            else:
                cell = str(v)
            cls = "num" if c in num_cols else ""
            cells.append(f"<td class='{cls}'>{_html.escape(cell)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")

    st.markdown(
        f"<table class='ledger-table'><thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>",
        unsafe_allow_html=True,
    )


def empty_state(title: str, message: str, icon: str = "⚠️") -> None:
    """Friendly empty-state prompt (missing data / not-yet-analyzed)."""
    st.markdown(
        f"<div class='empty-state'>"
        f"<div class='es-icon'>{icon}</div>"
        f"<div class='es-title'>{title}</div>"
        f"<div class='es-msg'>{message}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Ticker (signature element, Dashboard only)
# ---------------------------------------------------------------------------

def get_ticker_content() -> list:
    """The 10 valuation methods + 6 asset classes, deduped, live from metadata."""
    mm = load_model_metadata()
    am = load_agent_metadata()
    methods = mm.get("target_classes") or []
    classes = am.get("asset_classes") or []
    if isinstance(classes, dict):
        classes = list(classes.keys())
    items = list(methods) + list(classes)
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    if not out:
        out = ["DCF", "Black-Scholes", "Monte-Carlo", "Binomial-Tree",
               "Mark-to-Market", "Relative", "DDM", "Credit-Model",
               "Cost-of-Carry", "Forward-Pricing",
               "Equity", "Bond", "Option", "Commodity", "Currency", "Derivative"]
    return out


def render_ticker() -> None:
    """Slim scrolling strip of valuation methods + asset classes."""
    items = get_ticker_content()
    cell = "".join(
        f"<span class='ticker-item'>{item}<span class='sep'>·</span></span>"
        for item in items
    )
    st.markdown(
        f"<div class='ticker-wrap'><div class='ticker-track'>{cell}{cell}</div></div>",
        unsafe_allow_html=True,
    )
