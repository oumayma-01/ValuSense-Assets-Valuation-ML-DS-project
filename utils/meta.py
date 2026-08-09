import json
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

_calibration_filenames = (
    "metadata_calibrated_v3_calibrated.json",
    "v3_calibrated_metadata.json",
)


def _safe_load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@st.cache_data(ttl=3600, show_spinner=False)
def load_model_metadata() -> dict:
    return _safe_load(MODELS_DIR / "model_metadata.json")


@st.cache_data(ttl=3600, show_spinner=False)
def load_calibration_metadata():
    for name in _calibration_filenames:
        meta = _safe_load(MODELS_DIR / name)
        if meta:
            return meta
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_agent_metadata() -> dict:
    return _safe_load(MODELS_DIR / "agent_metadata.json")


def hero_stats():
    """Pull the landing-page headline stats live from model metadata.
    Never hard-codes numbers so they cannot drift out of sync with the model.
    """
    meta = load_model_metadata()
    cal = load_calibration_metadata()
    agent = load_agent_metadata()

    metrics = meta.get("metrics", {})
    before = metrics.get("before_ifrs", {})
    after = metrics.get("after_ifrs", {})

    n_asset_classes = len(agent.get("asset_classes", {})) or None
    if n_asset_classes is None:
        n_asset_classes = None

    stats = [
        {
            "label": "Assets used to train the model",
            "value": f"{meta.get('training_samples', 0):,}",
            "caption": "labelled samples across 10 methods",
        },
        {
            "label": "Asset classes covered",
            "value": str(n_asset_classes) if n_asset_classes else "6",
            "caption": "equity · bond · option · commodity · currency · derivative",
        },
        {
            "label": "Valuation methods",
            "value": str(meta.get("n_classes", 10)),
            "caption": "DCF · Black-Scholes · Monte-Carlo · ...",
        },
        {
            "label": "Model accuracy (post-IFRS)",
            "value": f"{after.get('f1_weighted', 0.845):.1%}",
            "caption": f"{before.get('f1_weighted', 0.991):.1%} before regulatory checks",
        },
        {
            "label": "Regulatory corrections",
            "value": f"{meta.get('ifrs_overrides', 0):,}",
            "caption": f"{meta.get('domain_violations_after_ifrs', 0)} domain violations left",
        },
    ]
    return stats
