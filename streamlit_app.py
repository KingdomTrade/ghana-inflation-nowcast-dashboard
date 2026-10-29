from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# GHANA HEADLINE INFLATION NOWCAST — PUBLIC RESEARCH DASHBOARD
# Public companion dashboard for the Ghana inflation nowcasting manuscript.
# =============================================================================
#
# Research team
# -------------
# Acheampong Kwabena Joseph (Joseph Acheampong) — Bank of Ghana
# Dr Julius B. Dasah — Bank of Ghana
# Dr Albert Acheampong — Nottingham Trent University
#
# Public data DOI
# ---------------
# https://doi.org/10.5281/zenodo.22688968
#
# The dashboard reads frozen public data outputs only. It does not fit, select,
# tune, or re-estimate any forecasting model.
# =============================================================================

st.set_page_config(
    page_title="Ghana Inflation Nowcast | Research Dashboard",
    page_icon="★",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "Public research dashboard for the Ghana headline inflation nowcast. "
            "Data: Zenodo DOI 10.5281/zenodo.22688968."
        )
    },
)

PROJECT = Path(__file__).resolve().parent
DATA_DIR = PROJECT / "data"
ZENODO_DOI = "10.5281/zenodo.22688968"
ZENODO_URL = "https://doi.org/10.5281/zenodo.22688968"

# =============================================================================
# VISUAL SYSTEM — GHANA INSPIRED
# =============================================================================

GH_RED = "#CE1126"
GH_GOLD = "#FCD116"
GH_GREEN = "#006B3F"
GH_BLACK = "#111111"
INK = "#17211C"
MUTED = "#66736C"
BG = "#F7F8F4"
SURFACE = "#FFFFFF"
SURFACE_SOFT = "#F1F5F0"
BORDER = "#DDE5DF"
GRID = "#E8EEE9"
GOOD = "#087A4B"
WARN = "#B7791F"
BAD = "#B42336"
TEAL = "#0B7A75"
BLUE = "#2457A7"

TARGET_MID = 8.0
TARGET_LOW = 6.0
TARGET_HIGH = 10.0

STATE_ORDER = {
    "S1_Day7": 1,
    "S2_Day14": 2,
    "S3_Day21": 3,
    "S4_MonthEnd": 4,
}
STATE_LABEL = {
    "S1_Day7": "Day 7",
    "S2_Day14": "Day 14",
    "S3_Day21": "Day 21",
    "S4_MonthEnd": "Month-end",
}
STATES = list(STATE_ORDER)

# Frozen turning-point guardrail parameters
GAP_MIN = 0.25
MOMENTUM_FLOOR = -0.50
CURVATURE_MIN = 0.0
MAX_CORRECTION = 1.0

BASE_ARCHITECTURE = "13-component CPI nowcast + vintage-specific model map"
FINAL_ARCHITECTURE = (
    "Freshness-gated 13-component nowcast + Strict-Safe Turning-Point Guardrail "
    "+ Unified Revision Guardrail"
)

APPROVED_MODEL_MAP = {
    "S1_Day7": "Macro + News Ridge",
    "S2_Day14": "Macro Ridge",
    "S3_Day21": "Macro + News ExtraTrees",
    "S4_MonthEnd": "Macro + News ExtraTrees",
}

# Latest agreed prospective figures. These are displayed separately from the
# frozen historical-validation dataset so prospective results are not mixed
# into historical model-selection evidence.
LIVE_PROSPECTIVE = pd.DataFrame([
    {
        "target_month": "2026-09",
        "S1_Day7": 3.0056425520,
        "S2_Day14": 4.2996536175,
        "S3_Day21": 5.0288463843,
        "S4_MonthEnd": 5.0413,
        "official": 5.2,
    },
    {
        "target_month": "2026-10",
        "S1_Day7": 4.958026408121952,
        "S2_Day14": 5.927108553420735,
        "S3_Day21": 6.028945649092599,
        "S4_MonthEnd": np.nan,
        "official": np.nan,
    },
])

LATEST_OFFICIAL_MONTH = "2026-09"
LATEST_OFFICIAL_YOY = 5.2
LATEST_OFFICIAL_INDEX = 271.5
OCT_DAY7 = 4.958026408121952
OCT_DAY14 = 5.927108553420735
OCT_DAY21_RAW = 6.9927455902653035
OCT_DAY21 = 6.028945649092599
OCT_DAY14_REVISION_PP = 0.969082145298783
OCT_DAY21_REVISION_PP = 1.065637036844569
OCT_DAY21_OPERATIONAL_REVISION_PP = OCT_DAY21 - OCT_DAY14
OCT_DAY21_CONFIRMATIONS = 1
OCT_DAY21_REFERENCE = 5.927108553420735
OCT_DAY7_MACRO_SHADOW = 5.6312082442
OCT_DAY7_ANCHOR = 5.2
OCT_TRANSPORT_AGE_MONTHS = 28
OCT_FAO_AGE_MONTHS = 5
OCT_PPI_MONTH = "2026-08"
OCT_FX_LATEST_DATE = "2026-10-21"
OCT_FUEL_LATEST_DATE = "2026-09-28"
OCT_NEWS_LATEST_DATE = "2026-10-21"


st.markdown(
    f"""
    <style>
    :root {{
        --gh-red:{GH_RED}; --gh-gold:{GH_GOLD}; --gh-green:{GH_GREEN};
        --ink:{INK}; --muted:{MUTED}; --border:{BORDER};
    }}
    .stApp {{
        background:
          radial-gradient(circle at 93% 0%, rgba(252,209,22,.12), transparent 27rem),
          radial-gradient(circle at -6% 20%, rgba(0,107,63,.07), transparent 25rem),
          linear-gradient(180deg,#FAFBF8 0%,#F6F8F4 100%);
        color:var(--ink);
    }}
    .block-container {{max-width:1580px;padding-top:1rem;padding-bottom:4rem;padding-left:2rem;padding-right:2rem;}}
    header[data-testid="stHeader"] {{background:rgba(250,251,248,.90);backdrop-filter:blur(12px);border-bottom:1px solid rgba(221,229,223,.82);}}
    [data-testid="stSidebar"] {{background:#FCFDFB;border-right:1px solid var(--border);}}
    h1,h2,h3 {{color:var(--ink);letter-spacing:-.03em;}}
    .ghana-ribbon {{display:grid;grid-template-columns:1fr 1fr 1fr;height:5px;border-radius:999px;overflow:hidden;margin-bottom:.85rem;}}
    .ghana-ribbon > div:nth-child(1){{background:var(--gh-red)}}
    .ghana-ribbon > div:nth-child(2){{background:var(--gh-gold)}}
    .ghana-ribbon > div:nth-child(3){{background:var(--gh-green)}}
    .hero {{position:relative;overflow:hidden;border:1px solid rgba(17,17,17,.08);background:radial-gradient(circle at 92% 10%,rgba(252,209,22,.21),transparent 20rem),linear-gradient(128deg,#0C1F15 0%,#103421 58%,#0A2A1B 100%);border-radius:26px;padding:1.55rem 1.65rem 1.45rem;color:white;box-shadow:0 20px 55px rgba(17,52,33,.17);margin-bottom:1rem;}}
    .hero:after {{content:"★";position:absolute;right:1.5rem;top:.1rem;font-size:8rem;color:rgba(252,209,22,.12);pointer-events:none;}}
    .hero-kicker {{font-size:.72rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:#F8E88D;margin-bottom:.55rem;}}
    .hero-title {{font-size:clamp(2.1rem,4vw,4.1rem);line-height:.98;letter-spacing:-.055em;font-weight:820;max-width:1050px;color:white;}}
    .hero-sub {{margin-top:.8rem;max-width:1050px;color:#DCE8DF;font-size:1.02rem;line-height:1.55;}}
    .hero-meta {{display:flex;gap:.55rem;flex-wrap:wrap;margin-top:1rem;}}
    .hero-chip {{padding:.38rem .66rem;border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.07);border-radius:999px;color:#ECF3EE;font-size:.73rem;font-weight:650;}}
    .authors-line {{margin-top:.9rem;color:#D9E7DD;font-size:.81rem;line-height:1.5;}}
    .metric-grid {{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.78rem;margin:.8rem 0 1.15rem;}}
    .metric-card {{background:rgba(255,255,255,.96);border:1px solid var(--border);border-radius:18px;padding:.95rem 1rem;min-height:126px;box-shadow:0 9px 25px rgba(25,52,37,.045);}}
    .metric-card.highlight {{background:linear-gradient(145deg,rgba(0,107,63,.06),white 72%);border-color:rgba(0,107,63,.22);}}
    .metric-card.gold {{background:linear-gradient(145deg,rgba(252,209,22,.12),white 72%);border-color:rgba(183,121,31,.20);}}
    .metric-label {{color:#718078;font-size:.70rem;font-weight:800;letter-spacing:.072em;text-transform:uppercase;}}
    .metric-value {{color:#10251A;font-size:1.85rem;font-weight:820;letter-spacing:-.04em;margin-top:.28rem;line-height:1.08;}}
    .metric-detail {{color:#718078;font-size:.77rem;line-height:1.38;margin-top:.36rem;}}
    .metric-good{{color:{GOOD};font-weight:760}} .metric-warn{{color:{WARN};font-weight:760}} .metric-bad{{color:{BAD};font-weight:760}}
    .section-head {{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:1rem 0 .58rem;}}
    .section-title {{color:#12251A;font-size:1.18rem;font-weight:810;letter-spacing:-.026em;}}
    .section-note {{color:#758179;font-size:.80rem;max-width:820px;line-height:1.45;}}
    .panel {{background:rgba(255,255,255,.96);border:1px solid var(--border);border-radius:19px;padding:1rem 1.05rem;box-shadow:0 8px 26px rgba(25,52,37,.035);}}
    .callout {{border-left:4px solid var(--gh-green);background:linear-gradient(90deg,rgba(0,107,63,.065),rgba(255,255,255,.75));border-radius:0 16px 16px 0;padding:.95rem 1rem;color:#33433A;font-size:.87rem;line-height:1.55;margin:.4rem 0 .9rem;}}
    .callout.gold {{border-left-color:#D6A700;background:linear-gradient(90deg,rgba(252,209,22,.10),rgba(255,255,255,.75));}}
    .callout.red {{border-left-color:var(--gh-red);background:linear-gradient(90deg,rgba(206,17,38,.055),rgba(255,255,255,.75));}}
    .status-line {{display:flex;flex-wrap:wrap;gap:.55rem;margin:.45rem 0 .8rem;}}
    .status-pill {{display:inline-flex;align-items:center;gap:.36rem;padding:.34rem .58rem;border-radius:999px;border:1px solid var(--border);background:white;color:#59675F;font-size:.72rem;font-weight:650;}}
    .status-dot {{width:8px;height:8px;border-radius:50%;background:{GOOD};box-shadow:0 0 0 4px rgba(8,122,75,.08);}}
    .pipeline {{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.75rem;margin:.75rem 0 1rem;}}
    .pipeline-card {{position:relative;border:1px solid var(--border);border-radius:18px;background:white;padding:1rem .95rem;min-height:178px;overflow:hidden;}}
    .pipeline-card:before {{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--gh-red) 0 33%,var(--gh-gold) 33% 66%,var(--gh-green) 66%);}}
    .pipe-num {{display:inline-flex;width:29px;height:29px;align-items:center;justify-content:center;border-radius:50%;background:#101D16;color:white;font-size:.72rem;font-weight:800;margin-bottom:.55rem;}}
    .pipe-title {{color:#14261B;font-size:.96rem;font-weight:800;margin-bottom:.32rem;}}
    .pipe-copy {{color:#6A776F;font-size:.78rem;line-height:1.48;}}
    .gov-grid {{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin:.65rem 0 1rem;}}
    .gov-card {{border:1px solid var(--border);background:white;border-radius:17px;padding:.9rem .95rem;}}
    .gov-card b {{color:#14261B}} .gov-card div {{color:#6A776F;font-size:.79rem;line-height:1.45;margin-top:.25rem;}}
    .author-card {{height:100%;border:1px solid var(--border);background:white;border-radius:20px;padding:1.05rem 1.1rem;box-shadow:0 8px 24px rgba(25,52,37,.035);}}
    .author-role {{font-size:.70rem;color:#718078;text-transform:uppercase;font-weight:800;letter-spacing:.065em;}}
    .author-name {{font-size:1.25rem;color:#13261A;font-weight:820;margin:.25rem 0 .35rem;}}
    .author-affil {{font-size:.82rem;color:{GH_GREEN};font-weight:740;line-height:1.4;margin-bottom:.45rem;}}
    .author-bio {{font-size:.79rem;color:#66736C;line-height:1.55;}}
    .tiny {{color:#7A867F;font-size:.73rem;line-height:1.45;}}
    .footer {{margin-top:2.2rem;padding:1.1rem 1.15rem;border-top:1px solid var(--border);color:#718078;font-size:.76rem;line-height:1.55;}}
    div[data-testid="stPlotlyChart"] {{background:rgba(255,255,255,.97);border:1px solid var(--border);border-radius:20px;padding:.24rem .35rem .12rem;box-shadow:0 8px 27px rgba(25,52,37,.035);}}
    [data-testid="stDataFrame"] {{border:1px solid var(--border);border-radius:16px;overflow:hidden;}}
    @media(max-width:1200px){{.metric-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}.pipeline{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
    @media(max-width:780px){{.block-container{{padding-left:1rem;padding-right:1rem}}.metric-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.pipeline,.gov-grid{{grid-template-columns:1fr}}}}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# PUBLIC, PORTABLE FILE LOADING
# =============================================================================
# Only relative public-data locations are used. No machine-specific paths are
# displayed or required.

PUBLIC_FILES = {
    "Historical nowcasts": "combined_historical_nowcasts_through_aug2026.csv",
    "Guardrail predictions": "turning_guardrail_predictions.csv",
    "Guardrail validation": "turning_guardrail_validation_summary.csv",
    "Study I monthly data": "study1_monthly_model_dataset.csv",
    "Study I news vintages": "phase1_news_vintages.csv",
    "Study II information vintages": "study2_information_vintages.csv",
    "Study II model matrix": "study2_model_matrix.csv",
}


def public_file(filename: str) -> Optional[Path]:
    for p in (DATA_DIR / filename, PROJECT / filename):
        if p.exists():
            return p
    return None


@st.cache_data(show_spinner=False)
def read_csv_file(filename: str) -> Optional[pd.DataFrame]:
    path = public_file(filename)
    if path is None:
        return None
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception:
        return None


combined = read_csv_file(PUBLIC_FILES["Historical nowcasts"])
guardrail = read_csv_file(PUBLIC_FILES["Guardrail predictions"])
validation_summary = read_csv_file(PUBLIC_FILES["Guardrail validation"])
study1 = read_csv_file(PUBLIC_FILES["Study I monthly data"])
phase1_vintages = read_csv_file(PUBLIC_FILES["Study I news vintages"])
study2_info = read_csv_file(PUBLIC_FILES["Study II information vintages"])
study2_matrix = read_csv_file(PUBLIC_FILES["Study II model matrix"])

if combined is None or combined.empty:
    st.error(
        "Required public dataset `combined_historical_nowcasts_through_aug2026.csv` "
        "was not found. Place the CSV in a `data` folder beside this dashboard file."
    )
    st.stop()

# =============================================================================
# DATA PREPARATION
# =============================================================================


def apply_guardrail(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    x["target_month"] = x["target_month"].astype(str).str[:7]
    x["month"] = pd.PeriodIndex(x["target_month"], freq="M")
    x = x.sort_values("month").reset_index(drop=True)
    x["actual"] = pd.to_numeric(x["actual"], errors="coerce")
    for state in STATES:
        x[state] = pd.to_numeric(x[state], errors="coerce")

    x["lag2_actual"] = x["actual"].shift(2)
    x["lag3_actual"] = x["actual"].shift(3)
    x["lag4_actual"] = x["actual"].shift(4)
    x["lag2_delta"] = x["lag2_actual"] - x["lag3_actual"]
    x["lag3_delta"] = x["lag3_actual"] - x["lag4_actual"]
    x["lag_curvature"] = x["lag2_delta"] - x["lag3_delta"]

    for state in STATES:
        gap = x["lag2_actual"] - x[state]
        gate = (
            (gap >= GAP_MIN)
            & (x["lag2_delta"] >= MOMENTUM_FLOOR)
            & (x["lag_curvature"] >= CURVATURE_MIN)
        )
        correction = np.minimum(gap.clip(lower=0.0), MAX_CORRECTION)
        x[f"{state}_active"] = gate.fillna(False)
        x[f"{state}_correction"] = np.where(gate, correction, 0.0)
        x[f"{state}_corrected"] = x[state] + x[f"{state}_correction"]

    x["date"] = x["month"].dt.to_timestamp()
    return x


# Prefer the deposited, exact guardrail output. Recompute only as a transparent
# fallback if the guardrail predictions file is absent.
if guardrail is not None and not guardrail.empty:
    hist = guardrail.copy()
    hist["target_month"] = hist["target_month"].astype(str).str[:7]
    hist["month"] = pd.PeriodIndex(hist["target_month"], freq="M")
    hist["date"] = hist["month"].dt.to_timestamp()
    hist["actual"] = pd.to_numeric(hist["actual"], errors="coerce")
    for s in STATES:
        hist[s] = pd.to_numeric(hist[s], errors="coerce")
        active_source = f"{s}_guardrail_active"
        hist[f"{s}_active"] = hist[active_source].astype(str).str.lower().eq("true") if active_source in hist.columns else False
        hist[f"{s}_corrected"] = pd.to_numeric(hist[f"{s}_corrected"], errors="coerce")
        hist[f"{s}_correction"] = pd.to_numeric(hist[f"{s}_correction"], errors="coerce")
    hist = hist.sort_values("month").reset_index(drop=True)
else:
    hist = apply_guardrail(combined)

# =============================================================================
# HELPERS
# =============================================================================


def month_name(x) -> str:
    try:
        return pd.Timestamp(str(x)[:7] + "-01").strftime("%B %Y")
    except Exception:
        return str(x)


def metric_html(label, value, detail, style="", tone=""):
    tone_class = {"good": "metric-good", "bad": "metric-bad", "warn": "metric-warn"}.get(tone, "")
    return f"""
    <div class="metric-card {style}">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-detail {tone_class}">{detail}</div>
    </div>
    """


def section_head(title, note=""):
    st.markdown(
        f'<div class="section-head"><div class="section-title">{title}</div><div class="section-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def base_layout(title="", height=470, ytitle=None, xtitle=None, legend=True):
    return dict(
        height=height,
        margin=dict(l=25, r=20, t=60 if title else 25, b=82),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color=INK, size=12),
        title=dict(text=title, x=.02, y=.97, font=dict(size=16, color=INK)) if title else None,
        hoverlabel=dict(bgcolor="white", bordercolor=BORDER, font=dict(color=INK, size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(size=11)) if legend else None,
        xaxis=dict(title=xtitle, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED)),
        yaxis=dict(title=ytitle, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED)),
    )


def monthly_axis(fig: go.Figure, range_slider: bool = False):
    """Force explicit monthly ticks so readers can see months without hovering."""
    fig.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y",
        tickangle=-50,
        ticklabelmode="period",
        showgrid=True,
        gridcolor=GRID,
        rangeslider=dict(visible=range_slider),
    )


def add_target_band(fig: go.Figure):
    fig.add_hrect(
        y0=TARGET_LOW,
        y1=TARGET_HIGH,
        fillcolor="rgba(252,209,22,.09)",
        line_width=0,
        layer="below",
        annotation_text="BoG medium-term target band 6–10%",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#8A6B00"),
    )
    fig.add_hline(y=TARGET_MID, line_dash="dot", line_color="rgba(138,107,0,.45)", line_width=1)


def state_metrics(frame: pd.DataFrame, state: str, corrected: bool) -> Dict[str, float]:
    pred_col = f"{state}_corrected" if corrected else state
    e = pd.to_numeric(frame[pred_col], errors="coerce") - pd.to_numeric(frame["actual"], errors="coerce")
    e = e.dropna()
    if e.empty:
        return {"n": 0, "mae": np.nan, "rmse": np.nan, "bias": np.nan, "corr": np.nan}
    p = pd.to_numeric(frame.loc[e.index, pred_col], errors="coerce")
    a = pd.to_numeric(frame.loc[e.index, "actual"], errors="coerce")
    return {
        "n": int(len(e)),
        "mae": float(np.abs(e).mean()),
        "rmse": float(np.sqrt(np.mean(e ** 2))),
        "bias": float(e.mean()),
        "corr": float(p.corr(a)) if len(e) > 2 else np.nan,
    }


def overall_metrics(frame: pd.DataFrame, corrected: bool) -> Dict[str, float]:
    errors = []
    for s in STATES:
        pred_col = f"{s}_corrected" if corrected else s
        e = pd.to_numeric(frame[pred_col], errors="coerce") - pd.to_numeric(frame["actual"], errors="coerce")
        errors.extend(e.dropna().tolist())
    e = np.asarray(errors, dtype=float)
    if len(e) == 0:
        return {"n": 0, "mae": np.nan, "rmse": np.nan, "bias": np.nan}
    return {
        "n": int(len(e)),
        "mae": float(np.mean(np.abs(e))),
        "rmse": float(np.sqrt(np.mean(e ** 2))),
        "bias": float(np.mean(e)),
    }


def display_window(frame: pd.DataFrame, window: str) -> pd.DataFrame:
    frame = frame.sort_values("date")
    if window == "Last 12 months":
        return frame.tail(12).copy()
    if window == "Last 24 months":
        return frame.tail(24).copy()
    if window == "Last 36 months":
        return frame.tail(36).copy()
    return frame.copy()


# Metrics
base_2026 = overall_metrics(hist[hist["month"].dt.year == 2026], corrected=False)
corrected_2026 = overall_metrics(hist[hist["month"].dt.year == 2026], corrected=True)
mae_gain_2026 = 100 * (1 - corrected_2026["mae"] / base_2026["mae"]) if base_2026["mae"] else np.nan
rmse_gain_2026 = 100 * (1 - corrected_2026["rmse"] / base_2026["rmse"]) if base_2026["rmse"] else np.nan
latest_row = hist.sort_values("month").iloc[-1]
latest_month = str(latest_row["month"])
latest_actual = float(latest_row["actual"])

confirmation_base_mae = np.nan
confirmation_corrected_mae = np.nan
confirmation_gain = np.nan
if validation_summary is not None and not validation_summary.empty:
    q = validation_summary[validation_summary["scope"].astype(str).eq("CONFIRMATION_2023_2025")]
    if not q.empty:
        confirmation_base_mae = float(q.iloc[0]["base_mae"])
        confirmation_corrected_mae = float(q.iloc[0]["corrected_mae"])
        confirmation_gain = float(q.iloc[0]["mae_gain_pct"])

activation_2026 = int(sum(hist.loc[hist["month"].dt.year == 2026, f"{s}_active"].sum() for s in STATES))

# =============================================================================
# ANALYTICAL VIEW DATA
# =============================================================================

# Extend the frozen historical evidence with the completed September prospective
# month and the current October live path. Historical selection/validation data
# remain unchanged; these rows are used for dashboard display only.
live_display_rows = []

sep_live = LIVE_PROSPECTIVE[LIVE_PROSPECTIVE["target_month"].eq("2026-09")].iloc[0]
live_display_rows.append({
    "target_month": "2026-09",
    "month": pd.Period("2026-09", freq="M"),
    "date": pd.Timestamp("2026-09-01"),
    "actual": float(sep_live["official"]),
    "S1_Day7": float(sep_live["S1_Day7"]),
    "S2_Day14": float(sep_live["S2_Day14"]),
    "S3_Day21": float(sep_live["S3_Day21"]),
    "S4_MonthEnd": float(sep_live["S4_MonthEnd"]),
    "S1_Day7_corrected": float(sep_live["S1_Day7"]),
    "S2_Day14_corrected": float(sep_live["S2_Day14"]),
    "S3_Day21_corrected": float(sep_live["S3_Day21"]),
    "S4_MonthEnd_corrected": float(sep_live["S4_MonthEnd"]),
    "S1_Day7_active": False,
    "S2_Day14_active": False,
    "S3_Day21_active": False,
    "S4_MonthEnd_active": False,
    "S1_Day7_correction": 0.0,
    "S2_Day14_correction": 0.0,
    "S3_Day21_correction": 0.0,
    "S4_MonthEnd_correction": 0.0,
    "evidence_layer": "Completed prospective",
})

live_display_rows.append({
    "target_month": "2026-10",
    "month": pd.Period("2026-10", freq="M"),
    "date": pd.Timestamp("2026-10-01"),
    "actual": np.nan,
    "S1_Day7": OCT_DAY7,
    "S2_Day14": OCT_DAY14,
    # Raw Day21 is retained as the base diagnostic; corrected is operational.
    "S3_Day21": OCT_DAY21_RAW,
    "S4_MonthEnd": np.nan,
    "S1_Day7_corrected": OCT_DAY7,
    "S2_Day14_corrected": OCT_DAY14,
    "S3_Day21_corrected": OCT_DAY21,
    "S4_MonthEnd_corrected": np.nan,
    "S1_Day7_active": False,
    "S2_Day14_active": False,
    "S3_Day21_active": True,
    "S4_MonthEnd_active": False,
    "S1_Day7_correction": 0.0,
    "S2_Day14_correction": 0.0,
    "S3_Day21_correction": OCT_DAY21 - OCT_DAY21_RAW,
    "S4_MonthEnd_correction": np.nan,
    "evidence_layer": "Live prospective",
})

hist_display = hist.copy()
hist_display["evidence_layer"] = "Frozen historical"
for row in live_display_rows:
    hist_display = pd.concat([hist_display, pd.DataFrame([row])], ignore_index=True, sort=False)
hist_display = (
    hist_display
    .sort_values("date")
    .drop_duplicates(subset=["target_month"], keep="last")
    .reset_index(drop=True)
)

# Analysis sample shown by default: Jan-2025 onward plus the live months.
hist_2025plus = hist_display[hist_display["date"] >= pd.Timestamp("2025-01-01")].copy()

PLOT_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "scrollZoom": False,
    "responsive": True,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "ghana_inflation_nowcast_chart",
        "scale": 2,
    },
}

STATE_COLORS = {
    "S1_Day7": GH_RED,
    "S2_Day14": "#C49300",
    "S3_Day21": TEAL,
    "S4_MonthEnd": GH_GREEN,
}


def analysis_window(frame: pd.DataFrame, choice: str) -> pd.DataFrame:
    frame = frame.sort_values("date")
    if choice == "Jan 2025 onward":
        return frame[frame["date"] >= pd.Timestamp("2025-01-01")].copy()
    return display_window(frame, choice)


def available_error_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[pd.to_numeric(frame["actual"], errors="coerce").notna()].copy()


def state_summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    f = available_error_frame(frame)
    for s in STATES:
        m = state_metrics(f, s, True)
        rows.append({
            "Vintage": STATE_LABEL[s],
            "N": m["n"],
            "MAE": m["mae"],
            "RMSE": m["rmse"],
            "Bias": m["bias"],
            "Correlation": m["corr"],
        })
    return pd.DataFrame(rows)


def make_error_matrix(frame: pd.DataFrame):
    f = available_error_frame(frame).copy()
    if f.empty:
        return None, None
    z = []
    for _, r in f.iterrows():
        z.append([
            abs(float(r[f"{s}_corrected"]) - float(r["actual"]))
            if pd.notna(r.get(f"{s}_corrected")) else np.nan
            for s in STATES
        ])
    labels = [month_name(x) for x in f["target_month"]]
    return np.asarray(z, dtype=float), labels


# =============================================================================
# COMPACT HERO
# =============================================================================

st.markdown(
    """
    <style>
    .hero {padding:1.05rem 1.25rem 1rem; border-radius:20px; margin-bottom:.75rem;}
    .hero-title {font-size:clamp(1.75rem,3vw,3rem); line-height:1.02;}
    .hero-sub {margin-top:.55rem; font-size:.91rem; max-width:1200px;}
    .hero-meta {margin-top:.7rem;}
    .hero-chip {font-size:.68rem; padding:.30rem .55rem;}
    .authors-line {margin-top:.6rem;}
    .analysis-note {font-size:.77rem;color:#68766e;line-height:1.45;}
    .small-status {font-size:.73rem;font-weight:750;letter-spacing:.03em;text-transform:uppercase;color:#64726a;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="ghana-ribbon"><div></div><div></div><div></div></div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">★ Ghana macroeconomic intelligence • interactive research monitor</div>
      <div class="hero-title">Headline Inflation Nowcast</div>
      <div class="hero-sub">
        Explore the historical nowcast path, compare Day 7–Month-end information vintages, inspect forecast errors,
        and audit the live October 2026 revision decision. Historical validation stays frozen; live prospective results
        are displayed as a separate evidence layer.
      </div>
      <div class="hero-meta">
        <span class="hero-chip">Latest official CPI: September 2026 • 5.2%</span>
        <span class="hero-chip">October Day 21 operational: {OCT_DAY21:.2f}%</span>
        <span class="hero-chip">Day 21 raw: {OCT_DAY21_RAW:.2f}%</span>
        <span class="hero-chip">Month-end: pending</span>
        <span class="hero-chip">Target-month outcome excluded</span>
      </div>
      <div class="authors-line"><b>Research team:</b> Acheampong Kwabena Joseph • Dr Julius B. Dasah • Dr Albert Acheampong</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# SIDEBAR CONTROLS
# =============================================================================

PAGES = [
    "Overview",
    "Historical Explorer",
    "Live October",
    "Accuracy & Errors",
    "Governance",
    "Methodology",
    "Data & Authors",
]

with st.sidebar:
    st.markdown("### ★ Nowcast workspace")
    page = st.radio("View", PAGES, index=0)
    st.divider()
    state = st.selectbox(
        "Focus vintage",
        STATES,
        index=2,
        format_func=lambda x: STATE_LABEL[x],
    )
    chart_window = st.selectbox(
        "Historical window",
        ["Last 12 months", "Last 24 months", "Last 36 months", "Jan 2025 onward", "Full history"],
        index=3,
    )
    show_states = st.multiselect(
        "Historical lines",
        STATES,
        default=STATES,
        format_func=lambda x: STATE_LABEL[x],
    )
    st.divider()
    st.markdown("#### Current live state")
    st.metric("October Day 21", f"{OCT_DAY21:.2f}%", delta=f"{OCT_DAY21_OPERATIONAL_REVISION_PP:+.2f} pp vs Day 14")
    st.caption(f"Raw model: {OCT_DAY21_RAW:.2f}% • governed after 1/3 confirmations")
    st.metric("Latest official CPI", f"{LATEST_OFFICIAL_YOY:.1f}%")
    st.caption("September 2026 • Ghana Statistical Service")
    st.divider()
    st.markdown("#### Approved model map")
    for s in STATES:
        st.caption(f"{STATE_LABEL[s]} — {APPROVED_MODEL_MAP[s]}")
    st.caption("Month-end remains pending until 31 October 2026.")


# =============================================================================
# OVERVIEW
# =============================================================================

if page == "Overview":
    display = analysis_window(hist_display, chart_window)
    focus_metric = state_metrics(available_error_frame(hist_2025plus), state, True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Latest official", f"{LATEST_OFFICIAL_YOY:.1f}%", "Sep 2026")
    m2.metric("October Day 7", f"{OCT_DAY7:.2f}%")
    m3.metric("October Day 14", f"{OCT_DAY14:.2f}%", f"{OCT_DAY14_REVISION_PP:+.2f} pp")
    m4.metric("October Day 21", f"{OCT_DAY21:.2f}%", f"{OCT_DAY21_OPERATIONAL_REVISION_PP:+.2f} pp")
    m5.metric(f"{STATE_LABEL[state]} MAE", f"{focus_metric['mae']:.2f} pp" if pd.notna(focus_metric['mae']) else "—")

    left, right = st.columns([1.65, 1])
    with left:
        section_head("Historical nowcast monitor", "Actual inflation and operational nowcasts. Use the sidebar to change the history window and visible vintages.")
        fig = go.Figure()
        add_target_band(fig)
        actual_display = display[pd.to_numeric(display["actual"], errors="coerce").notna()]
        fig.add_trace(go.Scatter(
            x=actual_display["date"], y=actual_display["actual"],
            mode="lines+markers", name="Actual inflation",
            line=dict(color=GH_BLACK, width=3.2), marker=dict(size=7),
            hovertemplate="%{x|%b %Y}<br><b>Actual</b> %{y:.2f}%<extra></extra>",
        ))
        for s in show_states:
            width = 3.2 if s == state else 1.8
            opacity = 1.0 if s == state else .60
            fig.add_trace(go.Scatter(
                x=display["date"], y=display[f"{s}_corrected"],
                mode="lines+markers", name=STATE_LABEL[s],
                line=dict(color=STATE_COLORS[s], width=width),
                marker=dict(size=6 if s == state else 4), opacity=opacity,
                hovertemplate=f"%{{x|%b %Y}}<br><b>{STATE_LABEL[s]}</b> %{{y:.2f}}%<extra></extra>",
            ))
        fig.add_vrect(
            x0=pd.Timestamp("2026-09-01"), x1=pd.Timestamp("2026-10-31"),
            fillcolor="rgba(11,122,117,.045)", line_width=0,
            annotation_text="Prospective", annotation_position="top left",
        )
        fig.update_layout(**base_layout(
            title=f"Actual vs operational nowcasts • focus: {STATE_LABEL[state]}",
            height=590, ytitle="Headline inflation (YoY %)", xtitle="Month"
        ))
        monthly_axis(fig, range_slider=True)
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    with right:
        section_head("October live path", "Raw model and governed operational path are shown separately.")
        oct_fig = go.Figure()
        oct_fig.add_trace(go.Scatter(
            x=["Day 7", "Day 14", "Day 21", "Month-end"],
            y=[OCT_DAY7, OCT_DAY14, OCT_DAY21, None],
            mode="lines+markers+text", name="Operational",
            text=[f"{OCT_DAY7:.2f}%", f"{OCT_DAY14:.2f}%", f"{OCT_DAY21:.2f}%", "Pending"],
            textposition="top center",
            line=dict(color=GH_GREEN, width=3.4), marker=dict(size=10),
        ))
        oct_fig.add_trace(go.Scatter(
            x=["Day 21"], y=[OCT_DAY21_RAW], mode="markers+text",
            text=[f"Raw {OCT_DAY21_RAW:.2f}%"], textposition="top center",
            name="Raw Day 21", marker=dict(size=15, color=GH_GOLD, symbol="diamond", line=dict(color=GH_BLACK,width=1)),
        ))
        oct_fig.add_hline(y=OCT_DAY7_ANCHOR, line_dash="dot", line_color=GH_BLACK,
                          annotation_text="Sep official 5.2%", annotation_position="bottom right")
        oct_fig.update_layout(**base_layout(title="October 2026 vintage path", height=420, ytitle="YoY %"))
        st.plotly_chart(oct_fig, use_container_width=True, config=PLOT_CONFIG)

        rev = pd.DataFrame({
            "Transition": ["Day7 → Day14", "Day14 → Day21 raw", "Day14 → Day21 operational"],
            "Revision": [OCT_DAY14_REVISION_PP, OCT_DAY21_REVISION_PP, OCT_DAY21_OPERATIONAL_REVISION_PP],
        })
        rev_fig = go.Figure(go.Bar(
            x=rev["Revision"], y=rev["Transition"], orientation="h",
            marker_color=["#C49300", GH_RED, GH_GREEN],
            text=[f"{x:+.2f} pp" for x in rev["Revision"]], textposition="outside",
        ))
        rev_fig.add_vline(x=1.0, line_dash="dash", line_color=GH_RED, annotation_text="1.0 pp trigger")
        rev_fig.update_layout(**base_layout(title="Vintage-to-vintage revision", height=300, ytitle=None, xtitle="Percentage points", legend=False))
        st.plotly_chart(rev_fig, use_container_width=True, config=PLOT_CONFIG)

    hleft, hright = st.columns([1.45, 1])
    with hleft:
        section_head("Forecast-error heatmap", "Absolute error by month and information vintage; darker cells indicate larger misses.")
        heat_frame = hist_2025plus[hist_2025plus["target_month"].le("2026-09")].copy()
        z, labels = make_error_matrix(heat_frame)
        if z is not None:
            heat = go.Figure(go.Heatmap(
                z=z.T,
                x=labels,
                y=[STATE_LABEL[s] for s in STATES],
                colorbar=dict(title="Abs error<br>(pp)"),
                colorscale=[[0,"#F7FAF8"],[0.35,"#FCD116"],[1,"#CE1126"]],
                hovertemplate="%{y}<br>%{x}<br>Absolute error %{z:.2f} pp<extra></extra>",
            ))
            heat.update_layout(**base_layout(title="Absolute forecast error • Jan 2025–Sep 2026", height=390, ytitle=None, xtitle="Target month", legend=False))
            heat.update_xaxes(tickangle=-45)
            st.plotly_chart(heat, use_container_width=True, config=PLOT_CONFIG)

    with hright:
        section_head("Latest completed month", "September 2026 prospective path against the official outcome.")
        sep_table = pd.DataFrame({
            "Vintage": [STATE_LABEL[s] for s in STATES],
            "Nowcast": [float(sep_live[s]) for s in STATES],
            "Official": [float(sep_live["official"])] * 4,
        })
        sep_table["Error (pp)"] = sep_table["Nowcast"] - sep_table["Official"]
        sep_fig = go.Figure()
        sep_fig.add_trace(go.Bar(x=sep_table["Vintage"], y=sep_table["Nowcast"], marker_color=[STATE_COLORS[s] for s in STATES], name="Nowcast"))
        sep_fig.add_hline(y=float(sep_live["official"]), line_color=GH_BLACK, line_width=2.5, annotation_text="Official 5.2%")
        sep_fig.update_layout(**base_layout(title="September 2026 information path", height=310, ytitle="YoY %", legend=False))
        st.plotly_chart(sep_fig, use_container_width=True, config=PLOT_CONFIG)
        st.dataframe(sep_table.round(3), hide_index=True, use_container_width=True)


# =============================================================================
# HISTORICAL EXPLORER
# =============================================================================

elif page == "Historical Explorer":
    section_head("Historical explorer", "Explore the full nowcast record, then drill into any target month and its four information vintages.")
    display = analysis_window(hist_display, chart_window)

    chart_tab, table_tab = st.tabs(["Interactive chart", "Data table"])
    with chart_tab:
        fig = go.Figure()
        add_target_band(fig)
        actual_display = display[pd.to_numeric(display["actual"], errors="coerce").notna()]
        fig.add_trace(go.Scatter(
            x=actual_display["date"], y=actual_display["actual"], mode="lines+markers",
            name="Actual", line=dict(color=GH_BLACK,width=3.3), marker=dict(size=6),
            hovertemplate="%{x|%B %Y}<br>Actual %{y:.2f}%<extra></extra>",
        ))
        for s in show_states:
            fig.add_trace(go.Scatter(
                x=display["date"], y=display[f"{s}_corrected"], mode="lines+markers",
                name=STATE_LABEL[s], line=dict(color=STATE_COLORS[s],width=2.2), marker=dict(size=4),
                hovertemplate=f"%{{x|%B %Y}}<br>{STATE_LABEL[s]} %{{y:.2f}}%<extra></extra>",
            ))
        fig.update_layout(**base_layout(title="Historical actual vs four operational nowcast vintages", height=650, ytitle="Headline inflation (YoY %)", xtitle="Month"))
        monthly_axis(fig, range_slider=True)
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
    with table_tab:
        cols = ["target_month", "actual"] + [f"{s}_corrected" for s in STATES] + ["evidence_layer"]
        st.dataframe(display[cols].rename(columns={f"{s}_corrected": STATE_LABEL[s] for s in STATES}).round(4), hide_index=True, use_container_width=True)

    month_options = hist_2025plus["target_month"].tolist()
    selected_month = st.select_slider(
        "Inspect target month",
        options=month_options,
        value=month_options[-1],
        format_func=month_name,
    )
    row = hist_2025plus[hist_2025plus["target_month"].eq(selected_month)].iloc[0]

    left, right = st.columns([1.35, 1])
    with left:
        cats = [STATE_LABEL[s] for s in STATES]
        vals = [row[f"{s}_corrected"] for s in STATES]
        profile = go.Figure()
        profile.add_trace(go.Scatter(
            x=cats, y=vals, mode="lines+markers+text", text=[f"{v:.2f}%" if pd.notna(v) else "Pending" for v in vals],
            textposition="top center", line=dict(color=GH_GREEN,width=3), marker=dict(size=10), name="Operational",
        ))
        if pd.notna(row.get("actual")):
            profile.add_hline(y=float(row["actual"]), line_color=GH_BLACK, line_width=2.5,
                              annotation_text=f"Actual {float(row['actual']):.2f}%")
        if selected_month == "2026-10":
            profile.add_trace(go.Scatter(
                x=["Day 21"], y=[OCT_DAY21_RAW], mode="markers+text", text=[f"Raw {OCT_DAY21_RAW:.2f}%"],
                textposition="top center", marker=dict(size=14,color=GH_GOLD,symbol="diamond",line=dict(color=GH_BLACK,width=1)), name="Raw Day 21",
            ))
        profile.update_layout(**base_layout(title=f"Vintage profile • {month_name(selected_month)}", height=455, ytitle="YoY %"))
        st.plotly_chart(profile, use_container_width=True, config=PLOT_CONFIG)

    with right:
        detail_rows = []
        for s in STATES:
            v = row.get(f"{s}_corrected")
            err = (float(v)-float(row["actual"])) if pd.notna(v) and pd.notna(row.get("actual")) else np.nan
            detail_rows.append({"Vintage":STATE_LABEL[s], "Operational":v, "Error (pp)":err})
        st.dataframe(pd.DataFrame(detail_rows).round(4), hide_index=True, use_container_width=True)
        st.markdown(f"**Evidence layer:** {row.get('evidence_layer','—')}")
        if selected_month == "2026-10":
            st.info(f"Day 21 raw {OCT_DAY21_RAW:.2f}% was governed to {OCT_DAY21:.2f}% after only {OCT_DAY21_CONFIRMATIONS}/3 confirmations. Month-end remains pending.")


# =============================================================================
# LIVE OCTOBER
# =============================================================================

elif page == "Live October":
    section_head("October 2026 live prospective monitor", "Track how the forecast changes as information accumulates. Raw model output remains visible when governance changes the operational figure.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Day 7", f"{OCT_DAY7:.3f}%", "Macro + News Ridge")
    c2.metric("Day 14", f"{OCT_DAY14:.3f}%", f"{OCT_DAY14_REVISION_PP:+.3f} pp vs Day 7")
    c3.metric("Day 21 operational", f"{OCT_DAY21:.3f}%", f"{OCT_DAY21_OPERATIONAL_REVISION_PP:+.3f} pp vs Day 14")
    c4.metric("Month-end", "PENDING", "31 Oct cutoff")

    left, right = st.columns([1.55, 1])
    with left:
        live = go.Figure()
        live.add_trace(go.Scatter(
            x=["Day 7", "Day 14", "Day 21", "Month-end"],
            y=[OCT_DAY7, OCT_DAY14, OCT_DAY21, None], mode="lines+markers+text",
            text=[f"{OCT_DAY7:.2f}%", f"{OCT_DAY14:.2f}%", f"{OCT_DAY21:.2f}%", "Pending"],
            textposition="top center", name="Operational", line=dict(color=GH_GREEN,width=4), marker=dict(size=12),
        ))
        live.add_trace(go.Scatter(
            x=["Day 21"], y=[OCT_DAY21_RAW], mode="markers+text", text=[f"Raw {OCT_DAY21_RAW:.2f}%"], textposition="top center",
            name="Raw model", marker=dict(size=18,color=GH_GOLD,symbol="diamond",line=dict(color=GH_BLACK,width=1.2)),
        ))
        live.add_hline(y=LATEST_OFFICIAL_YOY, line_dash="dot", line_color=GH_BLACK, annotation_text="Sep official 5.2%")
        live.update_layout(**base_layout(title="Live information-vintage path", height=500, ytitle="Headline inflation (YoY %)"))
        st.plotly_chart(live, use_container_width=True, config=PLOT_CONFIG)

    with right:
        section_head("Day 21 governance decision", "The raw move crossed the significant-revision threshold but did not receive enough independent confirmations.")
        st.metric("Raw Day 21", f"{OCT_DAY21_RAW:.3f}%", f"{OCT_DAY21_REVISION_PP:+.3f} pp vs Day 14")
        st.metric("Operational Day 21", f"{OCT_DAY21:.3f}%", f"{OCT_DAY21_OPERATIONAL_REVISION_PP:+.3f} pp vs Day 14")
        st.metric("Confirmations", f"{OCT_DAY21_CONFIRMATIONS} / 3")
        st.markdown(
            '<div class="callout gold"><b>Action:</b> SIGNIFICANT_REVISION_UNCONFIRMED_ROBUST_CONSENSUS. The 6.99% raw forecast is retained for audit; 6.03% is the governed operational nowcast.</div>',
            unsafe_allow_html=True,
        )

    section_head("Information freshness at Day 21", "The live row uses only information available by the 21 October cutoff. Stale targeted overlays fall back to the baseline model.")
    freshness = pd.DataFrame([
        ["Official CPI anchor", "Sep 2026 / released 7 Oct", 1, "SAFE ANCHOR"],
        ["PPI", OCT_PPI_MONTH, 2, "ELIGIBLE"],
        ["BoG USD/GHS FX", OCT_FX_LATEST_DATE, 0, "CURRENT"],
        ["NPA fuel", OCT_FUEL_LATEST_DATE, 1, "CARRY FORWARD"],
        ["Economic news", OCT_NEWS_LATEST_DATE, 0, "CURRENT"],
        ["FAO food", "May 2026", OCT_FAO_AGE_MONTHS, "STALE → BASELINE"],
        ["Transport", "Jun 2024", OCT_TRANSPORT_AGE_MONTHS, "STALE → BLOCKED"],
    ], columns=["Source", "Latest information", "Approx. age (months)", "Operational treatment"])

    fleft, fright = st.columns([1.2, 1])
    with fleft:
        ff = go.Figure(go.Bar(
            x=freshness["Approx. age (months)"], y=freshness["Source"], orientation="h",
            marker_color=[GH_GREEN,GH_GREEN,GH_GREEN,"#C49300",GH_GREEN,GH_RED,GH_RED],
            text=freshness["Operational treatment"], textposition="auto",
        ))
        ff.update_layout(**base_layout(title="Source-age discipline", height=430, ytitle=None, xtitle="Approximate age in months", legend=False))
        st.plotly_chart(ff, use_container_width=True, config=PLOT_CONFIG)
    with fright:
        st.dataframe(freshness, hide_index=True, use_container_width=True)


# =============================================================================
# ACCURACY & ERRORS
# =============================================================================

elif page == "Accuracy & Errors":
    section_head("Accuracy and error diagnostics", "Historical performance only: realised outcomes are used here for ex-post evaluation, never as contemporaneous live-model inputs.")
    eval_frame = hist_2025plus[hist_2025plus["target_month"].le("2026-09")].copy()
    metrics = state_summary_table(eval_frame)

    left, right = st.columns([1.15, 1])
    with left:
        perf = go.Figure()
        perf.add_trace(go.Bar(x=metrics["Vintage"], y=metrics["MAE"], name="MAE", marker_color=GH_GREEN))
        perf.add_trace(go.Bar(x=metrics["Vintage"], y=metrics["RMSE"], name="RMSE", marker_color=GH_GOLD))
        perf.update_layout(**base_layout(title="Error by information vintage • Jan 2025–Sep 2026", height=420, ytitle="Percentage points"))
        perf.update_layout(barmode="group")
        st.plotly_chart(perf, use_container_width=True, config=PLOT_CONFIG)
    with right:
        st.dataframe(metrics.round(4), hide_index=True, use_container_width=True)

    z, labels = make_error_matrix(eval_frame)
    if z is not None:
        heat = go.Figure(go.Heatmap(
            z=z.T, x=labels, y=[STATE_LABEL[s] for s in STATES],
            colorscale=[[0,"#F7FAF8"],[0.35,"#FCD116"],[1,"#CE1126"]],
            colorbar=dict(title="Abs error<br>(pp)"),
            hovertemplate="%{y}<br>%{x}<br>Absolute error %{z:.2f} pp<extra></extra>",
        ))
        heat.update_layout(**base_layout(title="Monthly absolute-error heatmap", height=420, ytitle=None, xtitle="Target month", legend=False))
        heat.update_xaxes(tickangle=-45)
        st.plotly_chart(heat, use_container_width=True, config=PLOT_CONFIG)

    left, right = st.columns([1.25, 1])
    with left:
        scatter_frame = available_error_frame(eval_frame)
        pcol = f"{state}_corrected"
        scatter = go.Figure()
        scatter.add_trace(go.Scatter(
            x=scatter_frame["actual"], y=scatter_frame[pcol], mode="markers",
            marker=dict(size=9, color=STATE_COLORS[state], opacity=.75),
            text=[month_name(x) for x in scatter_frame["target_month"]],
            hovertemplate="%{text}<br>Actual %{x:.2f}%<br>Nowcast %{y:.2f}%<extra></extra>",
        ))
        valid_vals = pd.concat([pd.to_numeric(scatter_frame["actual"],errors="coerce"), pd.to_numeric(scatter_frame[pcol],errors="coerce")]).dropna()
        if not valid_vals.empty:
            lo, hi = float(valid_vals.min()), float(valid_vals.max())
            scatter.add_trace(go.Scatter(x=[lo,hi], y=[lo,hi], mode="lines", line=dict(color=GH_BLACK,dash="dash"), name="45° line"))
        scatter.update_layout(**base_layout(title=f"Actual vs {STATE_LABEL[state]} operational nowcast", height=430, ytitle="Nowcast (%)", xtitle="Actual (%)"))
        st.plotly_chart(scatter, use_container_width=True, config=PLOT_CONFIG)
    with right:
        monthly = []
        for _, r in eval_frame.iterrows():
            errs = [abs(float(r[f"{s}_corrected"])-float(r["actual"])) for s in STATES if pd.notna(r.get(f"{s}_corrected"))]
            monthly.append({"target_month":r["target_month"], "Mean absolute error":np.mean(errs) if errs else np.nan})
        md = pd.DataFrame(monthly)
        mf = go.Figure(go.Bar(x=pd.to_datetime(md["target_month"]+"-01"), y=md["Mean absolute error"], marker_color=TEAL))
        mf.update_layout(**base_layout(title="Average error across four vintages", height=430, ytitle="Mean absolute error (pp)", xtitle="Month", legend=False))
        monthly_axis(mf)
        st.plotly_chart(mf, use_container_width=True, config=PLOT_CONFIG)


# =============================================================================
# GOVERNANCE
# =============================================================================

elif page == "Governance":
    section_head("Forecast governance", "Raw model output, operational intervention and historical turning-point corrections are visible rather than hidden.")

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Day21 raw", f"{OCT_DAY21_RAW:.2f}%")
    g2.metric("Day21 operational", f"{OCT_DAY21:.2f}%")
    g3.metric("Raw revision", f"{OCT_DAY21_REVISION_PP:+.2f} pp")
    g4.metric("Confirmations", f"{OCT_DAY21_CONFIRMATIONS}/3")

    left, right = st.columns([1.3, 1])
    with left:
        gov = go.Figure()
        gov.add_trace(go.Bar(
            x=["Day 7", "Day 14", "Day 21 raw", "Day 21 operational"],
            y=[OCT_DAY7, OCT_DAY14, OCT_DAY21_RAW, OCT_DAY21],
            marker_color=[STATE_COLORS["S1_Day7"], STATE_COLORS["S2_Day14"], GH_GOLD, GH_GREEN],
            text=[f"{OCT_DAY7:.2f}%", f"{OCT_DAY14:.2f}%", f"{OCT_DAY21_RAW:.2f}%", f"{OCT_DAY21:.2f}%"],
            textposition="outside",
        ))
        gov.add_hline(y=LATEST_OFFICIAL_YOY, line_dash="dot", line_color=GH_BLACK, annotation_text="Latest safe anchor 5.2%")
        gov.update_layout(**base_layout(title="Raw vs governed October path", height=440, ytitle="YoY %", legend=False))
        st.plotly_chart(gov, use_container_width=True, config=PLOT_CONFIG)
    with right:
        st.markdown(
            """
            <div class="gov-grid" style="grid-template-columns:1fr;">
              <div class="gov-card"><b>Significant revision trigger</b><div>Day 7/14/21: 1.0 pp. Month-end: 0.5 pp floor.</div></div>
              <div class="gov-card"><b>Independent confirmations</b><div>Challenger direction, safe-anchor direction and component breadth. At least 2 of 3 are required.</div></div>
              <div class="gov-card"><b>Day 21 outcome</b><div>The raw +1.07 pp move received only 1 of 3 confirmations, so robust consensus became operational while the raw 6.99% output was preserved.</div></div>
              <div class="gov-card"><b>Outcome isolation</b><div>October realised headline CPI is not used as a contemporaneous model input.</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    section_head("Historical turning-point guardrail", "The historical correction layer is evaluated separately from the newer prospective revision guardrail.")
    y26 = hist[hist["month"].dt.year == 2026].copy()
    month_stats = []
    for _, r in y26.iterrows():
        if pd.isna(r.get("actual")):
            continue
        base_err = [abs(float(r[s]) - float(r["actual"])) for s in STATES if pd.notna(r.get(s))]
        final_err = [abs(float(r[f"{s}_corrected"]) - float(r["actual"])) for s in STATES if pd.notna(r.get(f"{s}_corrected"))]
        month_stats.append({
            "month": r["target_month"],
            "Base MAE": np.mean(base_err) if base_err else np.nan,
            "Final MAE": np.mean(final_err) if final_err else np.nan,
            "Activations": int(sum(bool(r[f"{s}_active"]) for s in STATES)),
        })
    ms = pd.DataFrame(month_stats)
    if not ms.empty:
        gf = go.Figure()
        gf.add_trace(go.Bar(x=pd.to_datetime(ms["month"]+"-01"), y=ms["Base MAE"], name="Base MAE", marker_color="#C2CBC5"))
        gf.add_trace(go.Bar(x=pd.to_datetime(ms["month"]+"-01"), y=ms["Final MAE"], name="Final MAE", marker_color=GH_GREEN))
        gf.update_layout(**base_layout(title="2026 error before and after historical guardrail", height=430, ytitle="MAE (pp)", xtitle="Month"))
        gf.update_layout(barmode="group")
        monthly_axis(gf)
        st.plotly_chart(gf, use_container_width=True, config=PLOT_CONFIG)
        st.dataframe(ms.round(3), hide_index=True, use_container_width=True)

# =============================================================================
# METHODOLOGY
# =============================================================================

elif page == "Methodology":
    section_head("Methodology", "A reader-facing summary of how information becomes a leakage-controlled headline-inflation nowcast.")
    st.markdown(
        """
        <div class="pipeline">
          <div class="pipeline-card"><div class="pipe-num">1</div><div class="pipe-title">Signal discovery</div><div class="pipe-copy">Ghana economic news, official macro data and high-frequency price signals are screened for inflation relevance, timing and usable history.</div></div>
          <div class="pipeline-card"><div class="pipe-num">2</div><div class="pipe-title">Official CPI structure</div><div class="pipe-copy">GSS CPI information is organised around the 13 COICOP divisions used to reconstruct and validate headline CPI.</div></div>
          <div class="pipeline-card"><div class="pipe-num">3</div><div class="pipe-title">Pseudo-real-time vintages</div><div class="pipe-copy">Every target month is reconstructed at Day 7, Day 14, Day 21 and month-end. Only information observable by each cutoff is admitted.</div></div>
          <div class="pipeline-card"><div class="pipe-num">4</div><div class="pipe-title">Mixed-frequency information</div><div class="pipe-copy">BoG FX, NPA fuel, GSS PPI, economic news, food-price information and safe CPI anchors are aligned to each vintage.</div></div>
          <div class="pipeline-card"><div class="pipe-num">5</div><div class="pipe-title">Component nowcasting</div><div class="pipe-copy">Targeted component models translate contemporaneous signals into CPI-component nowcasts rather than treating headline inflation as one undifferentiated series.</div></div>
          <div class="pipeline-card"><div class="pipe-num">6</div><div class="pipe-title">Headline aggregation</div><div class="pipe-copy">Predicted component indices are combined using CPI weights and translated into headline year-on-year inflation.</div></div>
          <div class="pipeline-card"><div class="pipe-num">7</div><div class="pipe-title">Governance</div><div class="pipe-copy">Freshness gates, the turning-point rule and the prospective revision guardrail control stale or unexplained signals without hiding raw model output.</div></div>
          <div class="pipeline-card"><div class="pipe-num">8</div><div class="pipe-title">Evaluation</div><div class="pipe-copy">Selection, independent confirmation and the 2026 extension are reported separately. The public dashboard performs no model selection or tuning.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_head("Approved state-model map", "Prospective state models are fixed from October 2026 unless new evidence supports a documented change.")
    st.dataframe(pd.DataFrame([
        ["Day 7", "Macro + News Ridge"],
        ["Day 14", "Macro Ridge"],
        ["Day 21", "Macro + News ExtraTrees"],
        ["Month-end", "Macro + News ExtraTrees"],
    ], columns=["Information vintage", "Approved model"]), hide_index=True, use_container_width=True)

    section_head("Freshness and revision governance", "September 2026 showed that source age, path provenance and unexplained forecast jumps must be treated as model-governance variables.")
    st.markdown(
        """
        <div class="callout"><b>Freshness:</b> stale targeted overlays are blocked and the component reverts to its baseline model. <b>Revision control:</b> large vintage-to-vintage moves require 2-of-3 confirmation from a challenger model, the safe CPI anchor and component breadth. <b>Audit:</b> raw and operational forecasts remain separate.</div>
        """,
        unsafe_allow_html=True,
    )

    section_head("Headline aggregation", "The target is Ghana realised headline inflation, year-on-year.")
    e1, e2 = st.columns(2)
    with e1:
        st.latex(r"\hat I_t^{headline}=\sum_{j=1}^{13} w_j\hat I_{j,t}")
        st.caption("Weighted aggregation of predicted CPI component indices.")
    with e2:
        st.latex(r"\hat\pi_t=100\left(\frac{\hat I_t^{headline}}{I_{t-12}^{headline}}-1\right)")
        st.caption("Predicted headline year-on-year inflation from the current predicted index and known year-ago index.")

    data_sources = pd.DataFrame([
        ["Ghana Statistical Service", "CPI / COICOP", "Headline target, component indices and weights", "Official statistical source"],
        ["Bank of Ghana", "USD/GHS interbank FX", "Exchange-rate pressure", "Dated observations"],
        ["National Petroleum Authority", "Ex-pump fuel prices", "Fuel and transport pressure", "Market-date availability"],
        ["Ghana Statistical Service", "PPI", "Producer-price pressure", "Admitted by information availability"],
        ["Ghana economic news", "Derived article indicators", "Direction, uncertainty and economic channels", "Publication timing"],
        ["FAO food-price information", "Food-price signals", "Food component information", "Source-age discipline"],
    ], columns=["Source", "Data", "Role", "Timing discipline"])
    st.dataframe(data_sources, hide_index=True, use_container_width=True)

    section_head("Turning-point guardrail", "A narrow correction layer rather than a second unrestricted model.")
    st.latex(r"Gap_t = \pi_{t-2}-\hat\pi^{base}_t")
    st.latex(r"Gate_t = 1\{Gap_t\ge0.25,\ \Delta\pi_{t-2}\ge-0.50,\ \Delta\pi_{t-2}-\Delta\pi_{t-3}\ge0\}")
    st.latex(r"Correction_t = \min(\max(Gap_t,0),1.0)")
    st.latex(r"\hat\pi^{final}_t = \hat\pi^{base}_t + Gate_t\times Correction_t")

# =============================================================================
# DATA & AUTHORS
# =============================================================================

elif page == "Data & Authors":
    section_head("Open data and reproducibility", "The public dashboard exposes data provenance and availability without displaying any user's local computer paths.")

    st.markdown(
        f"""
        <div class="callout">
          <b>Public research data:</b> processed model-ready datasets, pseudo-real-time information vintages,
          historical nowcast outputs and guardrail results are archived on Zenodo.<br><br>
          <b>DOI:</b> {ZENODO_DOI}<br>
          <b>Repository version:</b> Public historical data v1.0 • live prospective dashboard updated through October Day 21, 2026<br>
          <b>Target:</b> Ghana headline CPI inflation, year-on-year (%)<br>
          <b>Information vintages:</b> Day 7, Day 14, Day 21 and month-end
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("Open the public dataset on Zenodo", ZENODO_URL)

    # Public manifest: names, availability, row counts and roles only. No local paths.
    resource_frames = {
        "Historical nowcasts": combined,
        "Guardrail predictions": guardrail,
        "Guardrail validation": validation_summary,
        "Study I monthly data": study1,
        "Study I news vintages": phase1_vintages,
        "Study II information vintages": study2_info,
        "Study II model matrix": study2_matrix,
    }
    resource_roles = {
        "Historical nowcasts": "Actual inflation and four within-month nowcast paths",
        "Guardrail predictions": "Base/final predictions, activation flags and corrections",
        "Guardrail validation": "Selection, confirmation and extension accuracy summary",
        "Study I monthly data": "Long-sample monthly Study I model-ready data",
        "Study I news vintages": "Day 7/14/21/month-end Study I news states",
        "Study II information vintages": "Leakage-controlled macro information states",
        "Study II model matrix": "Final Study II model-ready information matrix",
    }
    manifest_rows = []
    for label, filename in PUBLIC_FILES.items():
        df = resource_frames.get(label)
        manifest_rows.append({
            "Public resource": label,
            "Filename": filename,
            "Available": "Yes" if df is not None and not df.empty else "Optional / not loaded",
            "Rows": len(df) if df is not None else None,
            "Purpose": resource_roles[label],
        })
    st.dataframe(pd.DataFrame(manifest_rows), hide_index=True, use_container_width=True)
    st.caption("No absolute paths, usernames, working directories, environment files, API keys, or machine-specific locations are displayed in the public manifest.")

    section_head("Research team", "Brief biographies combine current institutional information supplied by the authors with publicly verifiable professional and research records.")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown(
            """
            <div class="author-card">
              <div class="author-role">Researcher • Bank of Ghana</div>
              <div class="author-name">Acheampong Kwabena Joseph<br><span style="font-size:.82rem;font-weight:650;color:#718078;">(Joseph Acheampong)</span></div>
              <div class="author-affil">Data Analytics and Artificial Intelligence Office, Bank of Ghana<br>The Bank Square, 42 Castle Road, Ridge, Accra</div>
              <div class="author-bio">Joseph Acheampong is a Bank of Ghana researcher with experience in macroeconomic and statistical analysis. His public research record includes work on short-term GDP forecasting for Ghana using leading real-sector indicators and factor-model methods. Public IMF statistical metadata has also listed him as a Bank of Ghana contact for balance-of-payments statistics. His current Data Analytics and Artificial Intelligence Office affiliation is the authors' current institutional information.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Public research record", "https://ideas.repec.org/a/ijr/journl/v1y2013i8p90-98.html", use_container_width=True)
    with a2:
        st.markdown(
            """
            <div class="author-card">
              <div class="author-role">Director / Head • Bank of Ghana</div>
              <div class="author-name">Dr Julius B. Dasah</div>
              <div class="author-affil">Data Analytics and Artificial Intelligence Office, Bank of Ghana<br>The Bank Square, 42 Castle Road, Ridge, Accra</div>
              <div class="author-bio">Dr Julius B. Dasah leads the Bank of Ghana's Data Analytics and Artificial Intelligence Office. His published research spans monetary and fiscal interactions, exchange-market pressures, banking profitability and credit risk, and banking-service research in Ghana. This combination of policy and empirical experience is directly relevant to the study's real-time macroeconomic and data-analytics focus.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Bank of Ghana organisational structure", "https://www.bog.gov.gh/organisational-structure/", use_container_width=True)
    with a3:
        st.markdown(
            """
            <div class="author-card">
              <div class="author-role">Senior Lecturer • Nottingham Trent University</div>
              <div class="author-name">Dr Albert Acheampong, PhD, MSc, FHEA</div>
              <div class="author-affil">Department of Accounting and Finance, Nottingham Business School, Nottingham Trent University, United Kingdom</div>
              <div class="author-bio">Albert Acheampong is a Senior Lecturer in Accounting whose teaching and research span accounting, finance, financial reporting, corporate disclosure, textual analysis, risk, sustainability and emerging technologies. His research increasingly applies machine learning, natural-language and alternative-data methods to financial and economic questions. He teaches at undergraduate and postgraduate levels, supervises research and contributes to work on artificial intelligence in corporate financial reporting.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("NTU staff profile", "https://www.ntu.ac.uk/staff-profiles/business/albert-acheampong", use_container_width=True)

    section_head("Governance and interpretation")
    st.markdown(
        """
        <div class="gov-grid">
          <div class="gov-card"><b>Outcome isolation</b><div>Realised target-month headline inflation is used for ex-post evaluation and is not contemporaneous model information.</div></div>
          <div class="gov-card"><b>Vintage discipline</b><div>Every state is tied to a defined within-month cutoff so later information cannot leak backwards into earlier nowcasts.</div></div>
          <div class="gov-card"><b>Frozen outputs</b><div>The public dashboard reads deposited results. It performs no parameter tuning, feature selection or model fitting.</div></div>
          <div class="gov-card"><b>News copyright</b><div>Full copyrighted article text is not redistributed in the public data deposit; derived research indicators are used instead.</div></div>
          <div class="gov-card"><b>Institutional disclaimer</b><div>Author affiliations identify the researchers. They do not imply institutional endorsement of the dashboard or its forecasts.</div></div>
          <div class="gov-card"><b>Persistent archive</b><div>The public data record is identified by Zenodo DOI 10.5281/zenodo.22688968.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown(
    f"""
    <div class="footer">
      <b>Ghana Headline Inflation Nowcast — Public Research Dashboard</b><br>
      Research team: Acheampong Kwabena Joseph • Dr Julius B. Dasah • Dr Albert Acheampong.<br>
      Public data: Zenodo DOI {ZENODO_DOI}.<br>
      Ghana Statistical Service CPI remains the official inflation measure. The Bank of Ghana target band is shown for policy context.
      This independent research dashboard is an analytical communication and validation tool and is not an official forecast or publication of the Bank of Ghana, Ghana Statistical Service, Nottingham Trent University, or any other institution.
    </div>
    """,
    unsafe_allow_html=True,
)
