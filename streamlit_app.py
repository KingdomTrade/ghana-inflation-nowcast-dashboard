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

BASE_ARCHITECTURE = "Transport LAST_2 + FAO Food ExtraTrees FULL_PATH"
FINAL_ARCHITECTURE = (
    "Transport LAST_2 + FAO Food ExtraTrees FULL_PATH "
    "+ Strict-Safe Turning-Point Guardrail"
)

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
    "September 2026 prospective nowcasts": "sep2026_prospective_nowcasts.csv",
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
sep2026_live = read_csv_file(PUBLIC_FILES["September 2026 prospective nowcasts"])

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

# Prepare the optional September-2026 prospective file. Keeping this separate
# from the evaluated historical panel ensures that incomplete live vintages do
# not enter MAE/RMSE calculations before the official GSS outcome is released.
if sep2026_live is not None and not sep2026_live.empty:
    sep2026_live = sep2026_live.copy()
    sep2026_live["state_order"] = pd.to_numeric(sep2026_live["state_order"], errors="coerce")
    sep2026_live["base_nowcast_yoy_pct"] = pd.to_numeric(sep2026_live["base_nowcast_yoy_pct"], errors="coerce")
    sep2026_live["guardrail_correction_pp"] = pd.to_numeric(sep2026_live["guardrail_correction_pp"], errors="coerce")
    sep2026_live["final_nowcast_yoy_pct"] = pd.to_numeric(sep2026_live["final_nowcast_yoy_pct"], errors="coerce")
    sep2026_live["generated"] = sep2026_live["status"].astype(str).str.upper().eq("GENERATED")
    sep2026_live = sep2026_live.sort_values("state_order").reset_index(drop=True)
else:
    sep2026_live = pd.DataFrame()

# Build a display-only panel that extends the evaluated history with the current
# prospective month.  This row is NEVER used for MAE/RMSE or model evaluation;
# it exists only so the live month appears naturally in the dashboard charts
# and Nowcast Explorer while the official target remains unknown.
def build_display_panel(history: pd.DataFrame, live: pd.DataFrame) -> pd.DataFrame:
    out = history.copy()
    if live is None or live.empty:
        return out

    live_month = str(live.iloc[0].get("target_month", "2026-09"))[:7]
    if live_month in set(out["target_month"].astype(str)):
        return out

    row = {
        "target_month": live_month,
        "month": pd.Period(live_month, freq="M"),
        "date": pd.Period(live_month, freq="M").to_timestamp(),
        "actual": np.nan,
    }

    for s in STATES:
        q = live[live["state"].astype(str).eq(s)]
        if q.empty:
            base = np.nan
            final = np.nan
            correction = 0.0
            active = False
        else:
            r = q.iloc[0]
            generated = bool(r.get("generated", False))
            base = float(r["base_nowcast_yoy_pct"]) if generated and pd.notna(r["base_nowcast_yoy_pct"]) else np.nan
            final = float(r["final_nowcast_yoy_pct"]) if generated and pd.notna(r["final_nowcast_yoy_pct"]) else np.nan
            correction = float(r["guardrail_correction_pp"]) if generated and pd.notna(r["guardrail_correction_pp"]) else 0.0
            active = str(r.get("guardrail_active", "False")).strip().lower() == "true" if generated else False

        row[s] = base
        row[f"{s}_corrected"] = final
        row[f"{s}_correction"] = correction
        row[f"{s}_active"] = active

    live_row = pd.DataFrame([row])
    out = pd.concat([out, live_row], ignore_index=True, sort=False)
    return out.sort_values("month").reset_index(drop=True)


hist_display = build_display_panel(hist, sep2026_live)

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

# Latest prospective September state (if packaged).
live_target_month = "2026-09"
live_generated = sep2026_live[sep2026_live["generated"]].copy() if not sep2026_live.empty else pd.DataFrame()
if not live_generated.empty:
    live_latest = live_generated.sort_values("state_order").iloc[-1]
    live_latest_state = str(live_latest["state"])
    live_latest_label = STATE_LABEL.get(live_latest_state, live_latest_state)
    live_latest_value = float(live_latest["final_nowcast_yoy_pct"])
else:
    live_latest = None
    live_latest_state = None
    live_latest_label = "Pending"
    live_latest_value = np.nan

# =============================================================================
# HERO
# =============================================================================

st.markdown('<div class="ghana-ribbon"><div></div><div></div><div></div></div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">★ Ghana macroeconomic intelligence • public research dashboard</div>
      <div class="hero-title">Headline Inflation Nowcast<br>Research Dashboard</div>
      <div class="hero-sub">
        Leakage-controlled, pseudo-real-time monitoring of Ghana headline inflation across Day 7, Day 14,
        Day 21 and month-end information vintages. The dashboard displays frozen research outputs and a
        transparent turning-point guardrail; it does not re-train or tune the underlying models.
      </div>
      <div class="hero-meta">
        <span class="hero-chip">Public data: Zenodo {ZENODO_DOI}</span>
        <span class="hero-chip">Day 7 • Day 14 • Day 21 • Month-end</span>
        <span class="hero-chip">13 CPI components</span>
        <span class="hero-chip">Target-month outcome excluded from model inputs</span>
        <span class="hero-chip">Latest evaluated month: {month_name(latest_month)}</span>
        <span class="hero-chip">Live target: September 2026 • latest completed {live_latest_label}</span>
      </div>
      <div class="authors-line">
        <b>Research team:</b> Acheampong Kwabena Joseph • Dr Julius B. Dasah • Dr Albert Acheampong
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("### ★ Research monitor")
    st.caption("Public frozen-results dashboard")
    state = st.selectbox(
        "Information vintage",
        STATES,
        index=1,
        format_func=lambda x: STATE_LABEL[x],
        help="Choose the within-month information cutoff shown in the charts.",
    )
    chart_window = st.selectbox(
        "Chart window",
        ["Last 12 months", "Last 24 months", "Last 36 months", "Full history"],
        index=1,
        help="Monthly labels are displayed explicitly. A shorter window improves readability.",
    )
    st.divider()
    st.markdown("#### Final architecture")
    st.caption(BASE_ARCHITECTURE)
    st.caption("+ Strict-Safe Turning-Point Guardrail")
    st.metric("2026 final MAE", f"{corrected_2026['mae']:.3f}")
    st.metric("2026 MAE improvement", f"{mae_gain_2026:.1f}%")
    if pd.notna(live_latest_value):
        st.metric("Sep 2026 live nowcast", f"{live_latest_value:.3f}%", live_latest_label)
        st.caption("Prospective output. Day 21 and month-end remain pending until their cutoffs close.")
    st.divider()
    st.markdown("#### Open research data")
    st.link_button("View dataset on Zenodo", ZENODO_URL, use_container_width=True)
    st.caption(f"DOI: {ZENODO_DOI}")
    st.divider()
    st.caption(
        "Research dashboard only. Ghana Statistical Service headline CPI remains the official inflation measure. "
        "The dashboard is not an official forecast or publication of the Bank of Ghana or Ghana Statistical Service."
    )

latest_state_final = float(latest_row[f"{state}_corrected"])
latest_state_error = latest_state_final - latest_actual

# The headline nowcast card follows the CURRENT prospective month whenever the
# selected information vintage has been completed; otherwise it shows Pending.
live_selected = sep2026_live[sep2026_live["state"].astype(str).eq(state)] if not sep2026_live.empty else pd.DataFrame()
if not live_selected.empty and bool(live_selected.iloc[0].get("generated", False)) and pd.notna(live_selected.iloc[0].get("final_nowcast_yoy_pct")):
    selected_live_value = f"{float(live_selected.iloc[0]['final_nowcast_yoy_pct']):.3f}%"
    selected_live_detail = f"September 2026 • prospective • cutoff {str(live_selected.iloc[0]['cutoff_date'])[:10]}"
    selected_live_tone = "good"
else:
    selected_live_value = "Pending"
    if not live_selected.empty:
        selected_live_detail = f"September 2026 • available after {str(live_selected.iloc[0]['cutoff_date'])[:10]} cutoff"
    else:
        selected_live_detail = "September 2026 • prospective output not yet packaged"
    selected_live_tone = "warn"

st.markdown(
    f"""
    <div class="metric-grid">
      {metric_html("Latest actual headline inflation", f"{latest_actual:.1f}%", month_name(latest_month), "gold")}
      {metric_html(f"Current {STATE_LABEL[state]} nowcast", selected_live_value, selected_live_detail, "highlight", selected_live_tone)}
      {metric_html("2026 final MAE", f"{corrected_2026['mae']:.3f}", f"Evaluated through {month_name(latest_month)} • Base MAE {base_2026['mae']:.3f}", "highlight", "good")}
      {metric_html("2026 MAE improvement", f"{mae_gain_2026:.1f}%", f"RMSE improvement {rmse_gain_2026:.1f}%", "gold", "good")}
      {metric_html("Independent confirmation", f"{confirmation_corrected_mae:.3f}" if pd.notna(confirmation_corrected_mae) else "Available", f"2023–2025 final MAE • {confirmation_gain:+.1f}% vs base" if pd.notna(confirmation_gain) else "Guardrail validation", "", "good")}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="status-line">
      <span class="status-pill"><span class="status-dot"></span> Public data DOI registered</span>
      <span class="status-pill"><span class="status-dot"></span> Target-month actual used in model: NO</span>
      <span class="status-pill"><span class="status-dot"></span> 2026 guardrail activations: {activation_2026}</span>
      <span class="status-pill"><span class="status-dot"></span> Four within-month information states</span>
      <span class="status-pill"><span class="status-dot"></span> September 2026 live through {live_latest_label}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# SEPTEMBER 2026 LIVE PROSPECTIVE PANEL
# =============================================================================

if not sep2026_live.empty:
    section_head(
        "September 2026 live prospective nowcast",
        "Frozen prospective architecture. September realised inflation is not used; incomplete vintages remain pending until their exact cutoff closes.",
    )

    live_cards = []
    for s in STATES:
        q = sep2026_live[sep2026_live["state"].astype(str).eq(s)]
        if q.empty:
            value = "Pending"
            detail = "No prospective row packaged"
            style = ""
            tone = "warn"
        else:
            r = q.iloc[0]
            if bool(r["generated"]) and pd.notna(r["final_nowcast_yoy_pct"]):
                value = f"{float(r['final_nowcast_yoy_pct']):.3f}%"
                active = str(r.get("guardrail_active", "False")).strip().lower() == "true"
                detail = f"Cutoff {str(r['cutoff_date'])[:10]} • guardrail {'active' if active else 'inactive'}"
                style = "highlight" if s == live_latest_state else ""
                tone = "good"
            else:
                value = "Pending"
                detail = f"Available after {str(r['cutoff_date'])[:10]} cutoff"
                style = ""
                tone = "warn"
        live_cards.append(metric_html(STATE_LABEL[s], value, detail, style, tone))

    # Render each live-vintage card separately.  Streamlit's Markdown parser can
    # expose raw HTML when several multi-line card fragments are concatenated
    # inside one HTML wrapper, so use native columns while preserving the same
    # metric-card styling.
    live_cols = st.columns(4)
    for col, card in zip(live_cols, live_cards):
        with col:
            st.markdown(card, unsafe_allow_html=True)

    if len(live_generated) >= 2:
        first = live_generated.sort_values("state_order").iloc[0]
        last = live_generated.sort_values("state_order").iloc[-1]
        revision = float(last["final_nowcast_yoy_pct"] - first["final_nowcast_yoy_pct"])
        live_note = (
            '<div class="callout gold"><b>Live revision:</b> the September nowcast moved from '
            f'<b>{float(first["final_nowcast_yoy_pct"]):.3f}%</b> at {STATE_LABEL.get(str(first["state"]), str(first["state"]))} '
            f'to <b>{float(last["final_nowcast_yoy_pct"]):.3f}%</b> at {STATE_LABEL.get(str(last["state"]), str(last["state"]))} '
            f'({revision:+.3f} percentage points). The strict-safe guardrail is inactive for the completed September vintages currently shown.</div>'
        )
        st.markdown(live_note, unsafe_allow_html=True)

        live_fig = go.Figure()
        live_fig.add_trace(go.Scatter(
            x=[STATE_LABEL.get(str(s), str(s)) for s in live_generated["state"]],
            y=live_generated["final_nowcast_yoy_pct"],
            mode="lines+markers+text",
            text=[f"{v:.3f}%" for v in live_generated["final_nowcast_yoy_pct"]],
            textposition="top center",
            name="Final prospective nowcast",
            line=dict(color=GH_GREEN, width=3),
            marker=dict(size=9),
            hovertemplate="%{x}<br>September nowcast %{y:.3f}%<extra></extra>",
        ))
        live_fig.update_layout(**base_layout(
            title="September 2026 prospective revision path",
            height=360,
            ytitle="Headline inflation nowcast (YoY %)",
            xtitle="Information vintage",
            legend=False,
        ))
        st.plotly_chart(live_fig, use_container_width=True, config={"displayModeBar": False})

PAGES = ["Executive", "Nowcast Explorer", "Turning Points", "Validation", "Methodology", "Data & Authors"]
page = st.radio("Dashboard section", PAGES, horizontal=True, label_visibility="collapsed")

# =============================================================================
# EXECUTIVE
# =============================================================================

if page == "Executive":
    section_head(
        "Executive view",
        "Monthly labels are displayed directly on the horizontal axis; use the sidebar window selector to focus the chart.",
    )
    display = display_window(hist_display, chart_window)
    fig = go.Figure()
    add_target_band(fig)
    if not sep2026_live.empty:
        fig.add_vrect(
            x0="2026-09-01", x1="2026-10-01",
            fillcolor="rgba(0,107,63,.045)", line_width=0, layer="below",
            annotation_text="Sep 2026 live • actual pending",
            annotation_position="top right",
            annotation_font=dict(size=10, color=GH_GREEN),
        )
    fig.add_trace(go.Scatter(
        x=display["date"], y=display["actual"], mode="lines+markers", name="Actual headline inflation",
        line=dict(color=GH_BLACK, width=3), marker=dict(size=6),
        hovertemplate="%{x|%B %Y}<br>Actual %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=display["date"], y=display[state], mode="lines+markers", name=f"Base • {STATE_LABEL[state]}",
        line=dict(color="#98A39D", width=1.7, dash="dot"), marker=dict(size=4),
        hovertemplate="%{x|%B %Y}<br>Base %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=display["date"], y=display[f"{state}_corrected"], mode="lines+markers", name=f"Final • {STATE_LABEL[state]}",
        line=dict(color=GH_GREEN, width=2.7), marker=dict(size=5),
        hovertemplate="%{x|%B %Y}<br>Final %{y:.2f}%<extra></extra>",
    ))
    active = display[display[f"{state}_active"]]
    if not active.empty:
        fig.add_trace(go.Scatter(
            x=active["date"], y=active[f"{state}_corrected"], mode="markers", name="Guardrail active",
            marker=dict(size=12, color=GH_GOLD, line=dict(color=GH_BLACK, width=1.2), symbol="star"),
            hovertemplate="%{x|%B %Y}<br>Guardrail activated<extra></extra>",
        ))
    fig.update_layout(**base_layout(title=f"Actual inflation vs {STATE_LABEL[state]} nowcast", height=560, ytitle="Headline inflation (YoY %)", xtitle="Month"))
    monthly_axis(fig, range_slider=chart_window == "Full history")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    left, right = st.columns([1.45, 1])
    with left:
        section_head("2026 information journey", "Each target month is estimated at four increasingly informed checkpoints.")
        y26 = hist_display[hist_display["month"].dt.year == 2026].copy()
        f = go.Figure()
        if not sep2026_live.empty:
            f.add_vrect(
                x0="2026-09-01", x1="2026-10-01",
                fillcolor="rgba(0,107,63,.045)", line_width=0, layer="below",
                annotation_text="Live month", annotation_position="top right",
                annotation_font=dict(size=10, color=GH_GREEN),
            )
        f.add_trace(go.Scatter(x=y26["date"], y=y26["actual"], name="Actual", mode="lines+markers", line=dict(color=GH_BLACK, width=3), marker=dict(size=8), hovertemplate="%{x|%B %Y}<br>Actual %{y:.2f}%<extra></extra>"))
        for s, color in zip(STATES, [GH_RED, "#C49300", TEAL, GH_GREEN]):
            f.add_trace(go.Scatter(x=y26["date"], y=y26[f"{s}_corrected"], name=STATE_LABEL[s], mode="lines+markers", line=dict(width=1.9, color=color), marker=dict(size=5), hovertemplate=f"%{{x|%B %Y}}<br>{STATE_LABEL[s]} %{{y:.2f}}%<extra></extra>"))
        f.update_layout(**base_layout(title="Final nowcasts across the four vintages", height=455, ytitle="YoY %", xtitle="Month"))
        monthly_axis(f)
        st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})

    with right:
        section_head("Turning-point response", "The guardrail stays dormant unless the strict gate is satisfied.")
        apr = hist[hist["target_month"].eq("2026-04")]
        may = hist[hist["target_month"].eq("2026-05")]
        if not apr.empty and not may.empty:
            st.markdown(
                f"""
                <div class="callout"><b>April 2026:</b> actual inflation was <b>{float(apr.iloc[0]['actual']):.1f}%</b>. The guardrail activated across all four vintages because the base path satisfied the pre-specified turning-point gate.</div>
                <div class="callout gold"><b>May 2026:</b> the guardrail again activated across all four states, applying a capped upward correction using only safely lagged realised inflation.</div>
                <div class="callout red"><b>June–August 2026:</b> the guardrail remained inactive. The final system therefore retained the base nowcasts unchanged.</div>
                """,
                unsafe_allow_html=True,
            )
        if validation_summary is not None:
            st.dataframe(validation_summary.round(4), hide_index=True, use_container_width=True)

# =============================================================================
# NOWCAST EXPLORER
# =============================================================================

elif page == "Nowcast Explorer":
    section_head("Nowcast explorer", "Inspect any target month and compare the four information vintages. The current prospective month is included even before the official outcome is released.")
    months = hist_display["target_month"].astype(str).tolist()
    selected_month = st.selectbox("Target month", months, index=len(months)-1, format_func=month_name)
    row = hist_display[hist_display["target_month"].astype(str).eq(selected_month)].iloc[0]

    actual_value = pd.to_numeric(pd.Series([row.get("actual", np.nan)]), errors="coerce").iloc[0]
    actual_available = pd.notna(actual_value)

    cards = []
    for s in STATES:
        base = pd.to_numeric(pd.Series([row.get(s, np.nan)]), errors="coerce").iloc[0]
        final = pd.to_numeric(pd.Series([row.get(f"{s}_corrected", np.nan)]), errors="coerce").iloc[0]
        active_flag = bool(row.get(f"{s}_active", False))

        if pd.isna(final):
            value = "Pending"
            q = sep2026_live[sep2026_live["state"].astype(str).eq(s)] if selected_month == "2026-09" and not sep2026_live.empty else pd.DataFrame()
            detail = f"Available after {str(q.iloc[0]['cutoff_date'])[:10]} cutoff" if not q.empty else "No nowcast available"
            tone = "warn"
        elif actual_available:
            err = float(final - actual_value)
            value = f"{float(final):.2f}%"
            detail = f"Base {float(base):.2f}% • Error {err:+.2f} pp" + (" • guardrail active" if active_flag else "")
            tone = "good" if abs(err) <= .5 else "warn" if abs(err) <= 1 else "bad"
        else:
            value = f"{float(final):.3f}%"
            detail = f"Base {float(base):.3f}% • prospective • actual pending" + (" • guardrail active" if active_flag else "")
            tone = "good"

        cards.append(metric_html(STATE_LABEL[s], value, detail, "highlight" if s == state else "", tone))

    st.markdown(f'<div class="metric-grid" style="grid-template-columns:repeat(4,minmax(0,1fr));">{"".join(cards)}</div>', unsafe_allow_html=True)

    cats = [STATE_LABEL[s] for s in STATES]
    b = go.Figure()
    if actual_available:
        b.add_hline(y=float(actual_value), line=dict(color=GH_BLACK, width=2.5), annotation_text=f"Actual {float(actual_value):.1f}%", annotation_position="top left")
    else:
        b.add_annotation(
            x=.02, y=.98, xref="paper", yref="paper", showarrow=False,
            text="Official realised CPI: pending",
            font=dict(size=11, color=MUTED), bgcolor="rgba(255,255,255,.82)",
        )
    b.add_trace(go.Bar(x=cats, y=[row.get(s, np.nan) for s in STATES], name="Base", marker_color="#BFC8C2", opacity=.72, hovertemplate="%{x}<br>Base %{y:.3f}%<extra></extra>"))
    b.add_trace(go.Bar(x=cats, y=[row.get(f"{s}_corrected", np.nan) for s in STATES], name="Final", marker_color=[GH_GOLD if bool(row.get(f"{s}_active", False)) else GH_GREEN for s in STATES], hovertemplate="%{x}<br>Final %{y:.3f}%<extra></extra>"))
    b.update_layout(**base_layout(title=f"Information-vintage profile • {month_name(selected_month)}", height=445, ytitle="Headline inflation (YoY %)"))
    b.update_layout(barmode="group", margin=dict(l=25,r=20,t=60,b=45))
    st.plotly_chart(b, use_container_width=True, config={"displayModeBar": False})

    section_head("Historical + live monthly path", "Evaluated history is extended with the current prospective month; the September actual remains blank until GSS releases it.")
    display = display_window(hist_display, chart_window)
    h = go.Figure()
    add_target_band(h)
    if not sep2026_live.empty:
        h.add_vrect(
            x0="2026-09-01", x1="2026-10-01",
            fillcolor="rgba(0,107,63,.045)", line_width=0, layer="below",
            annotation_text="Sep 2026 live", annotation_position="top right",
            annotation_font=dict(size=10, color=GH_GREEN),
        )
    h.add_trace(go.Scatter(x=display["date"], y=display["actual"], name="Actual", mode="lines+markers", line=dict(color=GH_BLACK, width=3), marker=dict(size=5), hovertemplate="%{x|%B %Y}<br>Actual %{y:.2f}%<extra></extra>"))
    h.add_trace(go.Scatter(x=display["date"], y=display[f"{state}_corrected"], name="Final", mode="lines+markers", line=dict(color=GH_GREEN, width=2.5), marker=dict(size=4), hovertemplate="%{x|%B %Y}<br>Final %{y:.2f}%<extra></extra>"))
    h.update_layout(**base_layout(title=f"{STATE_LABEL[state]} historical nowcast path", height=540, ytitle="YoY %", xtitle="Month"))
    monthly_axis(h, range_slider=chart_window == "Full history")
    st.plotly_chart(h, use_container_width=True, config={"displayModeBar": False})

# =============================================================================
# TURNING POINTS
# =============================================================================

elif page == "Turning Points":
    section_head("Turning-point diagnostics", "The final guardrail is a sparse safety layer, not a replacement forecasting model.")
    st.markdown(
        """
        <div class="callout">In 2026 the guardrail activates only in <b>April and May</b>, across the four within-month vintages, then switches off. The design is intentionally selective: it intervenes when the base path satisfies the pre-specified reversal conditions and otherwise leaves the component nowcast untouched.</div>
        """,
        unsafe_allow_html=True,
    )

    y26 = hist[hist["month"].dt.year == 2026].copy()
    month_stats = []
    for _, r in y26.iterrows():
        base_mae = float(np.mean([abs(float(r[s]) - float(r["actual"])) for s in STATES]))
        final_mae = float(np.mean([abs(float(r[f"{s}_corrected"]) - float(r["actual"])) for s in STATES]))
        month_stats.append({"month": r["target_month"], "Base MAE": base_mae, "Final MAE": final_mae, "Activations": int(sum(bool(r[f"{s}_active"]) for s in STATES))})
    ms = pd.DataFrame(month_stats)

    left, right = st.columns([1.35, 1])
    with left:
        mfig = go.Figure()
        mfig.add_trace(go.Bar(x=pd.to_datetime(ms["month"] + "-01"), y=ms["Base MAE"], name="Base MAE", marker_color="#C2CBC5"))
        mfig.add_trace(go.Bar(x=pd.to_datetime(ms["month"] + "-01"), y=ms["Final MAE"], name="Final MAE", marker_color=GH_GREEN))
        mfig.update_layout(**base_layout(title="Monthly error before and after guardrail", height=455, ytitle="MAE (percentage points)", xtitle="Month"))
        mfig.update_layout(barmode="group")
        monthly_axis(mfig)
        st.plotly_chart(mfig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.dataframe(ms.round(3), hide_index=True, use_container_width=True)

    section_head("Why the guardrail fires", "Only t−2 and older realised inflation are used in the gate; the target month's realised inflation is never an input.")
    c1, c2 = st.columns(2)
    with c1:
        st.latex(r"Gap_t = \pi_{t-2} - \hat{\pi}^{base}_t")
        st.latex(r"Gate_t = 1\{Gap_t \ge 0.25,\ \Delta\pi_{t-2}\ge -0.50,\ \Delta\pi_{t-2}-\Delta\pi_{t-3}\ge0\}")
    with c2:
        st.latex(r"Correction_t = \min(\max(Gap_t,0),1.0)")
        st.latex(r"\hat{\pi}^{final}_t=\hat{\pi}^{base}_t+Gate_t\times Correction_t")

# =============================================================================
# VALIDATION
# =============================================================================

elif page == "Validation":
    section_head("Validation", "Selection, independent confirmation and the 2026 extension are shown separately.")
    if validation_summary is None or validation_summary.empty:
        st.info("Guardrail validation summary is not available in the public data folder.")
    else:
        vs = validation_summary.copy()
        label_map = {"SELECTION_2022":"Selection • 2022", "CONFIRMATION_2023_2025":"Independent confirmation • 2023–2025", "EXTENSION_2026":"Extension • 2026"}
        vs["sample"] = vs["scope"].map(label_map).fillna(vs["scope"])
        c1, c2 = st.columns(2)
        with c1:
            f = go.Figure()
            f.add_trace(go.Bar(x=vs["sample"], y=vs["base_mae"], name="Base MAE", marker_color="#BFC8C2"))
            f.add_trace(go.Bar(x=vs["sample"], y=vs["corrected_mae"], name="Final MAE", marker_color=GH_GREEN))
            f.update_layout(**base_layout(title="MAE by evidence sample", height=440, ytitle="MAE", xtitle=""))
            f.update_layout(barmode="group", margin=dict(l=25,r=20,t=60,b=80))
            st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})
        with c2:
            f = go.Figure(go.Bar(x=vs["sample"], y=vs["mae_gain_pct"], marker_color=[GH_GOLD, GH_GREEN, GH_RED]))
            f.update_layout(**base_layout(title="MAE improvement from guardrail", height=440, ytitle="Improvement (%)", legend=False))
            f.update_layout(margin=dict(l=25,r=20,t=60,b=80))
            st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})
        st.dataframe(vs[["sample","base_mae","corrected_mae","mae_gain_pct","base_rmse","corrected_rmse","rmse_gain_pct","activated_states"]].round(4), hide_index=True, use_container_width=True)

    section_head("2026 accuracy by information vintage", "Base and final performance are calculated from the deposited state-level predictions.")
    y26 = hist[hist["month"].dt.year == 2026]
    rows = []
    for s in STATES:
        bm = state_metrics(y26, s, False); fm = state_metrics(y26, s, True)
        rows.append({"Vintage":STATE_LABEL[s], "Base MAE":bm["mae"], "Final MAE":fm["mae"], "Base RMSE":bm["rmse"], "Final RMSE":fm["rmse"], "Final bias":fm["bias"], "Correlation":fm["corr"]})
    vint = pd.DataFrame(rows)
    vf = go.Figure()
    vf.add_trace(go.Bar(x=vint["Vintage"], y=vint["Base MAE"], name="Base", marker_color="#C6CEC9"))
    vf.add_trace(go.Bar(x=vint["Vintage"], y=vint["Final MAE"], name="Final", marker_color=GH_GREEN))
    vf.update_layout(**base_layout(title="2026 MAE by vintage", height=420, ytitle="MAE")); vf.update_layout(barmode="group", margin=dict(l=25,r=20,t=60,b=45))
    st.plotly_chart(vf, use_container_width=True, config={"displayModeBar": False})
    st.dataframe(vint.round(4), hide_index=True, use_container_width=True)

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
          <div class="pipeline-card"><div class="pipe-num">7</div><div class="pipe-title">Turning-point guardrail</div><div class="pipe-copy">A capped, lagged-information rule intervenes only when the base path satisfies pre-specified turning-point conditions.</div></div>
          <div class="pipeline-card"><div class="pipe-num">8</div><div class="pipe-title">Evaluation</div><div class="pipe-copy">Selection, independent confirmation and the 2026 extension are reported separately. The public dashboard performs no model selection or tuning.</div></div>
        </div>
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
          <b>Repository version:</b> Public Data and Results v1.0 • September 2026<br>
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
        "September 2026 prospective nowcasts": sep2026_live,
    }
    resource_roles = {
        "Historical nowcasts": "Actual inflation and four within-month nowcast paths",
        "Guardrail predictions": "Base/final predictions, activation flags and corrections",
        "Guardrail validation": "Selection, confirmation and extension accuracy summary",
        "Study I monthly data": "Long-sample monthly Study I model-ready data",
        "Study I news vintages": "Day 7/14/21/month-end Study I news states",
        "Study II information vintages": "Leakage-controlled macro information states",
        "Study II model matrix": "Final Study II model-ready information matrix",
        "September 2026 prospective nowcasts": "Live frozen prospective Day 7/14/21/month-end status and nowcasts",
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
