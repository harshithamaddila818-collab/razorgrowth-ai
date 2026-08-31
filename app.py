# -*- coding: utf-8 -*-

import os
import json
import textwrap
from pathlib import Path
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai

from agent.growth_agent import analyze_growth_opportunities
from backend.approval_gate import validate_opportunity
from backend.razorpay_client import create_test_payment_link
from audit.audit_logger import log_opportunity


# ============================================================
# RazorGrowth AI
# Merchant Growth Command Center
# ============================================================


BASE_DIR = Path(__file__).resolve().parent

TRANSACTIONS_FILE = BASE_DIR / "data" / "transactions.csv"
AUDIT_FILE = BASE_DIR / "audit" / "audit_log.json"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="RazorGrowth AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# MARKDOWN HTML-RENDERING PATCH  (BUG FIX)
# ------------------------------------------------------------
# Every st.markdown(...) call below builds multi-line HTML using
# indented triple-quoted strings for readability, e.g.:
#
#     st.markdown(
#         """
#         <div class="hero">
#
#             <div class="hero-label">
#                 ...
#             </div>
#
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
#
# Two separate CommonMark rules combine to break this:
#
#   1. Any line indented 4+ spaces is treated as a preformatted code
#      block instead of being parsed as HTML/markdown.
#   2. An HTML block ends at the first BLANK line. So even after
#      dedenting the outermost tag, the blank line right after
#      "<div class='hero'>" closes that HTML block - and the next
#      indented inner <div> starts a brand new block, immediately
#      re-triggering rule #1. This is exactly what produced the
#      "code block with a copy button showing raw <div> tags"
#      symptom in the screenshot.
#
# Rather than manually reformatting 40+ call sites (and needing every
# single one to have zero indentation AND zero blank lines forever),
# we patch st.markdown once: when a call passes unsafe_allow_html=True,
# we collapse the string to a single line (strip per-line whitespace,
# drop blank lines, join with a space). That removes both the
# indentation and the blank-line HTML-block terminator, so the HTML
# always renders as intended. Plain-text markdown calls (no
# unsafe_allow_html) are only dedented, since those intentionally rely
# on blank lines to create separate paragraphs (e.g. the sidebar
# bullet lists).
# ============================================================

_original_markdown = st.markdown


def _patched_markdown(body="", *args, **kwargs):
    if isinstance(body, str):
        if kwargs.get("unsafe_allow_html"):
            lines = [line.strip() for line in body.splitlines()]
            body = " ".join(line for line in lines if line)
        else:
            body = textwrap.dedent(body).strip("\n")
    return _original_markdown(body, *args, **kwargs)


st.markdown = _patched_markdown


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in .env")
    st.stop()


# ============================================================
# GEMINI CLIENT
# ============================================================

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    GEMINI_CONNECTED = True
except Exception as error:
    client = None
    GEMINI_CONNECTED = False
    GEMINI_ERROR = str(error)


# ============================================================
# DARK PROFESSIONAL UI
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   GLOBAL
   ========================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 15% 0%,
            rgba(99, 102, 241, 0.12),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 5%,
            rgba(16, 185, 129, 0.08),
            transparent 28%
        ),
        #070b14 !important;

    color: #e5e7eb !important;
}

.main {
    background: transparent !important;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}


/* ==========================================================
   STREAMLIT 1.51 DARK SURFACE + TEXT OVERRIDES
   Targeted selectors prevent widgets from inheriting bad colors.
   ========================================================== */

html, body {
    background: #070b14 !important;
    color: #e5e7eb !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background: #070b14 !important;
    color: #e5e7eb !important;
}

[data-testid="stHeader"] {
    background: rgba(7, 11, 20, 0.92) !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: transparent !important;
}

[data-testid="stMarkdownContainer"] {
    color: #e5e7eb !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #cbd5e1 !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6 {
    color: #ffffff !important;
}

[data-testid="stMarkdownContainer"] a {
    color: #93c5fd !important;
}

[data-testid="stSidebar"] > div {
    background: transparent !important;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #0b1020 0%,
            #080c16 100%
        ) !important;
    border-right: 1px solid #1e293b !important;
}

[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

[data-testid="stSidebar"] hr {
    border-color: #1e293b !important;
}


/* ==========================================================
   HERO
   ========================================================== */

.hero {
    position: relative;
    overflow: hidden;

    padding: 38px 42px;
    margin-bottom: 28px;

    border-radius: 24px;

    background:
        radial-gradient(
            circle at 85% 20%,
            rgba(99, 102, 241, 0.22),
            transparent 30%
        ),
        radial-gradient(
            circle at 10% 100%,
            rgba(16, 185, 129, 0.12),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #111827,
            #0b1220
        );

    border: 1px solid #263247;

    box-shadow:
        0 25px 70px rgba(0, 0, 0, 0.28);
}

.hero-label {
    display: inline-block;

    padding: 7px 12px;

    border-radius: 999px;

    background: rgba(16, 185, 129, 0.10);

    border: 1px solid rgba(16, 185, 129, 0.28);

    color: #4ade80 !important;

    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.2px;

    margin-bottom: 15px;
}

.hero-title {
    font-size: 48px;
    line-height: 1.05;

    font-weight: 900;

    letter-spacing: -2px;

    color: #ffffff !important;

    margin-bottom: 12px;
}

.hero-text {
    max-width: 720px;

    color: #94a3b8 !important;

    font-size: 17px;
    line-height: 1.6;
}

.hero-status {
    display: inline-block;

    margin-top: 22px;

    padding: 8px 13px;

    border-radius: 999px;

    background: rgba(34, 197, 94, 0.08);

    border: 1px solid rgba(74, 222, 128, 0.20);

    color: #4ade80 !important;

    font-size: 12px;
    font-weight: 800;
}


/* ==========================================================
   SECTION HEADERS
   ========================================================== */

.section-header {
    margin-top: 30px;
    margin-bottom: 16px;
}

.section-title {
    color: #ffffff !important;

    font-size: 25px;
    font-weight: 850;

    letter-spacing: -0.5px;
}

.section-description {
    color: #64748b !important;

    font-size: 13px;

    margin-top: 3px;
}


/* ==========================================================
   KPI CARDS
   ========================================================== */

.kpi-card {
    min-height: 155px;

    padding: 22px;

    border-radius: 18px;

    background:
        linear-gradient(
            145deg,
            rgba(20, 29, 45, 0.96),
            rgba(12, 18, 30, 0.96)
        );

    border: 1px solid #243047;

    box-shadow:
        0 12px 35px rgba(0, 0, 0, 0.18);

    transition:
        transform 0.2s ease,
        border-color 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-3px);
    border-color: #3b4b68;
}

.kpi-icon {
    font-size: 25px;
    margin-bottom: 15px;
}

.kpi-label {
    color: #94a3b8 !important;

    font-size: 12px;
    font-weight: 750;

    text-transform: uppercase;

    letter-spacing: 0.6px;
}

.kpi-value {
    color: #ffffff !important;

    font-size: 29px;
    font-weight: 900;

    margin-top: 5px;
}

.kpi-sub {
    color: #64748b !important;

    font-size: 12px;

    margin-top: 4px;
}


/* ==========================================================
   PIPELINE
   ========================================================== */

.pipeline-wrapper {
    display: flex;
    align-items: stretch;

    gap: 8px;

    margin-top: 16px;
}

.pipeline-step {
    flex: 1;

    min-height: 125px;

    padding: 20px 10px;

    text-align: center;

    border-radius: 17px;

    background:
        linear-gradient(
            145deg,
            #111827,
            #0d1422
        );

    border: 1px solid #263247;

    display: flex;
    flex-direction: column;
    justify-content: center;
}

.pipeline-icon {
    font-size: 28px;

    margin-bottom: 8px;
}

.pipeline-name {
    color: #ffffff !important;

    font-size: 13px;
    font-weight: 850;

    text-transform: uppercase;
}

.pipeline-sub {
    color: #64748b !important;

    font-size: 11px;

    margin-top: 4px;
}

.pipeline-arrow {
    display: flex;

    align-items: center;
    justify-content: center;

    color: #475569 !important;

    font-size: 20px;

    padding: 0 2px;
}


/* ==========================================================
   STATUS CARDS
   ========================================================== */

.status-card {
    min-height: 130px;

    padding: 20px;

    border-radius: 17px;

    background: #0d1422;

    border: 1px solid #263247;

    text-align: center;
}

.status-icon {
    font-size: 25px;

    margin-bottom: 8px;
}

.status-name {
    color: #e2e8f0 !important;

    font-size: 13px;
    font-weight: 800;
}

.status-ready {
    color: #4ade80 !important;

    font-size: 12px;
    font-weight: 800;

    margin-top: 7px;
}


/* ==========================================================
   PRIORITY CARDS
   ========================================================== */

.priority-card {
    padding: 23px;

    border-radius: 17px;

    background: #0d1422;

    border: 1px solid #263247;
}

.priority-icon {
    font-size: 24px;
}

.priority-number {
    color: #ffffff !important;

    font-size: 32px;
    font-weight: 900;

    margin-top: 5px;
}

.priority-name {
    color: #94a3b8 !important;

    font-size: 11px;
    font-weight: 800;

    letter-spacing: 0.8px;
}


/* ==========================================================
   OPPORTUNITY CARDS
   ========================================================== */

.opportunity-card {
    padding: 22px;

    margin-bottom: 14px;

    border-radius: 18px;

    background:
        linear-gradient(
            145deg,
            #111827,
            #0c1320
        );

    border: 1px solid #263247;

    box-shadow:
        0 8px 25px rgba(0, 0, 0, 0.14);
}

.customer-name {
    color: #ffffff !important;

    font-size: 16px;
    font-weight: 850;
}

.product-flow {
    color: #94a3b8 !important;

    font-size: 14px;

    margin-top: 7px;
}

.product-flow strong {
    color: #818cf8 !important;

    padding: 0 6px;
}

.metric-label-small {
    color: #64748b !important;

    font-size: 10px;
    font-weight: 800;

    letter-spacing: 0.7px;

    text-transform: uppercase;
}

.metric-value-small {
    color: #ffffff !important;

    font-size: 18px;
    font-weight: 850;

    margin-top: 4px;
}

.muted {
    color: #64748b !important;

    font-size: 12px;
}


/* ==========================================================
   BADGES
   ========================================================== */

.badge {
    display: inline-block;

    padding: 7px 11px;

    border-radius: 999px;

    font-size: 10px;
    font-weight: 850;

    letter-spacing: 0.4px;
}

.badge-high {
    color: #fca5a5 !important;

    background: rgba(239, 68, 68, 0.12);

    border: 1px solid rgba(239, 68, 68, 0.22);
}

.badge-medium {
    color: #fdba74 !important;

    background: rgba(249, 115, 22, 0.12);

    border: 1px solid rgba(249, 115, 22, 0.22);
}

.badge-low {
    color: #86efac !important;

    background: rgba(34, 197, 94, 0.10);

    border: 1px solid rgba(34, 197, 94, 0.20);
}


/* ==========================================================
   AI CARD
   ========================================================== */

.ai-card {
    padding: 24px;

    border-radius: 19px;

    background:
        radial-gradient(
            circle at 90% 10%,
            rgba(99, 102, 241, 0.14),
            transparent 35%
        ),
        #0d1422;

    border: 1px solid #303c59;
}

.ai-title {
    color: #ffffff !important;

    font-size: 18px;
    font-weight: 850;
}

.ai-text {
    color: #94a3b8 !important;

    font-size: 13px;

    line-height: 1.6;

    margin-top: 8px;
}


/* ==========================================================
   PAYMENT CARDS
   ========================================================== */

.payment-card {
    padding: 20px;

    border-radius: 17px;

    background: #0d1422;

    border: 1px solid #263247;

    margin-bottom: 12px;
}

.payment-label {
    color: #64748b !important;

    font-size: 10px;
    font-weight: 800;

    letter-spacing: 0.7px;

    text-transform: uppercase;
}

.payment-value {
    color: #ffffff !important;

    font-size: 15px;
    font-weight: 800;

    margin-top: 4px;
}


/* ==========================================================
   STREAMLIT INPUTS
   ========================================================== */

div[data-baseweb="select"] > div {
    background-color: #0d1422 !important;

    border-color: #263247 !important;
}

div[data-baseweb="select"] span {
    color: #e5e7eb !important;
}

div[data-baseweb="popover"] {
    background-color: #0d1422 !important;
}

input {
    color: #e5e7eb !important;

    background-color: #0d1422 !important;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {
    background: #111827 !important;

    color: #e5e7eb !important;

    border: 1px solid #334155 !important;

    border-radius: 10px !important;

    font-weight: 750 !important;

    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: #6366f1 !important;

    color: #ffffff !important;

    background: #172033 !important;
}


/* ==========================================================
   EXPANDERS
   ========================================================== */

[data-testid="stExpander"] {
    background: #0d1422 !important;

    border: 1px solid #263247 !important;

    border-radius: 13px !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    color: #e5e7eb !important;
}


/* ==========================================================
   DATAFRAME
   ========================================================== */

[data-testid="stDataFrame"] {
    border: 1px solid #263247;

    border-radius: 12px;
}


/* ==========================================================
   ALERTS
   ========================================================== */

[data-testid="stAlert"] {
    border-radius: 12px !important;
}


/* ==========================================================
   DIVIDER
   ========================================================== */

hr {
    border-color: #1e293b !important;
}


/* ==========================================================
   FOOTER
   ========================================================== */

.footer {
    text-align: center;

    padding: 35px 10px 10px;

    color: #475569 !important;

    font-size: 12px;
}

.footer strong {
    color: #94a3b8 !important;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 900px) {

    .hero-title {
        font-size: 36px;
    }

    .pipeline-wrapper {
        flex-direction: column;
    }

    .pipeline-arrow {
        transform: rotate(90deg);
    }
}


/* FINAL DARK MODE OVERRIDES */
html, body, #root {
    background: #070b14 !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background: #070b14 !important;
}
[data-testid="stHeader"] {
    background: rgba(7, 11, 20, 0.96) !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background: #080c16 !important;
}
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #cbd5e1 !important;
}
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6 {
    color: #ffffff !important;
}
[data-testid="stMetric"] {
    background: #0d1422 !important;
    border: 1px solid #263247 !important;
    border-radius: 14px !important;
    padding: 12px !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
}
[data-testid="stSelectbox"] label {
    color: #94a3b8 !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #0d1422 !important;
    color: #e5e7eb !important;
    border-color: #263247 !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: #e5e7eb !important;
}
[data-baseweb="popover"],
[role="option"] {
    background: #0d1422 !important;
    color: #e5e7eb !important;
}
[role="option"]:hover {
    background: #172033 !important;
}
[data-testid="stExpander"],
[data-testid="stExpander"] details,
[data-testid="stExpander"] summary {
    background: #0d1422 !important;
    border-color: #263247 !important;
}
[data-testid="stExpander"] summary p {
    color: #e5e7eb !important;
}
[data-testid="stCaptionContainer"] {
    color: #64748b !important;
}
.stButton > button,
.stDownloadButton > button,
[data-testid="stLinkButton"] {
    background: #111827 !important;
    color: #e5e7eb !important;
    border: 1px solid #334155 !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stLinkButton"]:hover {
    background: #172033 !important;
    color: #ffffff !important;
    border-color: #6366f1 !important;
}
.stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    color: #ffffff !important;
    border-color: #6366f1 !important;
}
[data-testid="stAlert"] {
    background: #0d1422 !important;
    color: #e5e7eb !important;
}
.stApp::before,
.stApp::after,
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
    background: transparent !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default

        return int(value)

    except (TypeError, ValueError):
        return default


def safe_html(value, default=""):
    """Convert a value to safe text for custom HTML blocks."""
    if value is None:
        value = default
    return escape(str(value))


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

def load_transactions():

    if not TRANSACTIONS_FILE.exists():
        return pd.DataFrame()

    try:

        return pd.read_csv(
            TRANSACTIONS_FILE
        )

    except Exception:
        return pd.DataFrame()


# ============================================================
# LOAD AUDIT LOGS
# ============================================================

def load_audit_logs():

    if not AUDIT_FILE.exists():
        return []

    try:

        with open(
            AUDIT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read().strip()

        if not content:
            return []

        data = json.loads(content)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


# ============================================================
# FIND EXISTING PAYMENT LINK
# ============================================================

def find_existing_payment_link(
    customer_id,
    product
):

    logs = load_audit_logs()

    for log in logs:

        same_customer = (
            str(log.get("customer_id"))
            == str(customer_id)
        )

        same_product = (
            str(log.get("product"))
            == str(product)
        )

        created = (
            log.get("action_status")
            == "PAYMENT_LINK_CREATED"
        )

        url_exists = bool(
            log.get("payment_link_url")
        )

        if (
            same_customer
            and same_product
            and created
            and url_exists
        ):
            return log

    return None


# ============================================================
# GEMINI BATCH ANALYSIS
# ============================================================

def generate_batch_recommendations(
    opportunities
):

    if not opportunities:
        return []

    if client is None:
        raise RuntimeError(
            "Gemini client is not configured."
        )

    opportunity_data = []

    for opportunity in opportunities:

        opportunity_data.append(
            {
                "customer_id":
                    opportunity.get(
                        "customer_id"
                    ),

                "trigger_product":
                    opportunity.get(
                        "trigger_product"
                    ),

                "product":
                    opportunity.get(
                        "recommendation"
                    ),

                "potential_revenue":
                    safe_float(
                        opportunity.get(
                            "potential_revenue",
                            0
                        )
                    ),

                "rule_confidence":
                    safe_float(
                        opportunity.get(
                            "confidence",
                            0
                        )
                    ),

                "opportunity_score":
                    safe_float(
                        opportunity.get(
                            "opportunity_score",
                            0
                        )
                    ),

                "priority":
                    opportunity.get(
                        "priority",
                        "N/A"
                    ),

                "evidence":
                    opportunity.get(
                        "reason",
                        ""
                    ),
            }
        )


    prompt = f"""
You are RazorGrowth AI, an AI merchant growth
decision engine.

You are an advisory layer only.

Use ONLY the provided opportunity information.

Never invent customer information.
Never invent transaction history.
Never claim a customer will definitely purchase.
Never execute payments.
Never create payment links.
Never modify deterministic opportunity scores.
Never modify deterministic priority.
Every external action requires merchant approval.

For each opportunity return:

{{
    "customer_id": "...",
    "product": "...",
    "decision": "PURSUE or SKIP",
    "reason": "...",
    "suggested_action": "...",
    "risk": "...",
    "expected_revenue": number,
    "requires_merchant_approval": true
}}

Rules for expected_revenue:

- It must be >= 0.
- It must never exceed potential_revenue.
- It must be conservative.
- Use potential_revenue * rule_confidence
  as the maximum deterministic estimate.
- If evidence is insufficient, choose SKIP.
- requires_merchant_approval must always be true.

Return ONLY a valid JSON array.

Qualified opportunities:

{json.dumps(
    opportunity_data,
    indent=2
)}
"""


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = (
        response.text
        if response.text
        else ""
    ).strip()

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )


    # Remove accidental markdown fences.

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()


    try:

        results = json.loads(text)

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Gemini returned invalid JSON: {error}"
        )


    if not isinstance(results, list):

        raise ValueError(
            "Gemini response is not a JSON array."
        )


    normalized_results = []


    for result in results:

        if not isinstance(result, dict):
            continue


        customer_id = result.get(
            "customer_id",
            ""
        )

        product = result.get(
            "product",
            ""
        )


        matching_opportunity = None


        for opportunity in opportunities:

            same_customer = (
                str(
                    opportunity.get(
                        "customer_id"
                    )
                )
                ==
                str(customer_id)
            )

            same_product = (
                str(
                    opportunity.get(
                        "recommendation"
                    )
                )
                ==
                str(product)
            )

            if (
                same_customer
                and same_product
            ):

                matching_opportunity = (
                    opportunity
                )

                break


        if matching_opportunity:

            potential = safe_float(
                matching_opportunity.get(
                    "potential_revenue",
                    0
                )
            )

            confidence = safe_float(
                matching_opportunity.get(
                    "confidence",
                    0
                )
            )

            expected = safe_float(
                result.get(
                    "expected_revenue",
                    0
                )
            )

            expected = max(
                0.0,
                expected
            )

            deterministic_max = (
                potential * confidence
            )

            expected = min(
                expected,
                potential
            )

            expected = min(
                expected,
                deterministic_max
            )

        else:

            expected = 0.0


        decision = str(
            result.get(
                "decision",
                "SKIP"
            )
        ).upper().strip()


        if decision not in {
            "PURSUE",
            "SKIP"
        }:

            decision = "SKIP"


        normalized_result = {

            "customer_id":
                customer_id,

            "product":
                product,

            "decision":
                decision,

            "reason":
                str(
                    result.get(
                        "reason",
                        ""
                    )
                ),

            "suggested_action":
                str(
                    result.get(
                        "suggested_action",
                        ""
                    )
                ),

            "risk":
                str(
                    result.get(
                        "risk",
                        ""
                    )
                ),

            "expected_revenue":
                round(
                    expected,
                    2
                ),

            "requires_merchant_approval":
                True,
        }


        normalized_results.append(
            normalized_result
        )


    return normalized_results


# ============================================================
# SESSION STATE
# ============================================================

if "ai_results" not in st.session_state:
    st.session_state.ai_results = None

if "processed" not in st.session_state:
    st.session_state.processed = set()

if "gemini_error" not in st.session_state:
    st.session_state.gemini_error = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:26px;
            font-weight:850;
            color:#ffffff !important;
            line-height:1.2;
        ">
            🚀 RazorGrowth AI
        </div>

        <div style="
            color:#94a3b8 !important;
            font-size:12px;
            margin-top:5px;
        ">
            Merchant Growth Command Center
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown("---")


    st.markdown(
        """
        <div style="
            color:#64748b !important;
            font-size:10px;
            font-weight:850;
            letter-spacing:1px;
            margin-bottom:10px;
        ">
            INTELLIGENCE
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        """
        📊 Agent 1 — Opportunity Engine

        🤖 Agent 2 — Gemini Advisory

        🎯 Smart Cross-Sell
        """
    )


    st.markdown(
        """
        <div style="
            color:#64748b !important;
            font-size:10px;
            font-weight:850;
            letter-spacing:1px;
            margin-top:24px;
            margin-bottom:10px;
        ">
            GOVERNANCE
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        """
        🛡️ Safety Gate

        👤 Merchant Approval

        🔒 Duplicate Prevention
        """
    )


    st.markdown(
        """
        <div style="
            color:#64748b !important;
            font-size:10px;
            font-weight:850;
            letter-spacing:1px;
            margin-top:24px;
            margin-bottom:10px;
        ">
            EXECUTION
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.markdown(
        """
        💳 Razorpay TEST

        📝 Audit Trail
        """
    )


    st.markdown("---")


    if GEMINI_CONNECTED:

        st.success(
            "🟢 Gemini CONNECTED"
        )

    else:

        st.error(
            "🔴 Gemini NOT CONFIGURED"
        )


    st.markdown("---")


    if st.button(
        "🔄 Refresh Dashboard",
        width="stretch",
    ):

        st.session_state.ai_results = None
        st.session_state.gemini_error = None

        st.rerun()


# ============================================================
# LOAD DATA
# ============================================================

transactions = load_transactions()

audit_logs = load_audit_logs()


# ============================================================
# DETECT OPPORTUNITIES - CACHED
# ============================================================

@st.cache_data(show_spinner=False)
def get_opportunities(transaction_file, file_mtime):
    """Run Agent 1 only when the transaction file changes."""
    try:
        result = analyze_growth_opportunities(transaction_file)
        if not isinstance(result, list):
            return []
        return result
    except Exception as error:
        st.error("Agent 1 opportunity detection failed.")
        st.code(str(error))
        return []


if not transactions.empty:
    opportunities = get_opportunities(
        str(TRANSACTIONS_FILE),
        TRANSACTIONS_FILE.stat().st_mtime,
    )
else:
    opportunities = []


# ============================================================
# STATISTICS
# ============================================================

high_priority = sum(
    1
    for opportunity in opportunities
    if str(
        opportunity.get(
            "priority",
            ""
        )
    ).upper()
    == "HIGH"
)


medium_priority = sum(
    1
    for opportunity in opportunities
    if str(
        opportunity.get(
            "priority",
            ""
        )
    ).upper()
    == "MEDIUM"
)


low_priority = sum(
    1
    for opportunity in opportunities
    if str(
        opportunity.get(
            "priority",
            ""
        )
    ).upper()
    == "LOW"
)


payment_links = [
    log
    for log in audit_logs
    if log.get(
        "action_status"
    )
    == "PAYMENT_LINK_CREATED"
]


approved = [
    log
    for log in audit_logs
    if log.get(
        "merchant_approval"
    )
    == "APPROVED"
]


rejected = [
    log
    for log in audit_logs
    if log.get(
        "merchant_approval"
    )
    == "REJECTED"
]


# ============================================================
# REVENUE
# ============================================================

potential_revenue = sum(
    safe_float(
        opportunity.get(
            "potential_revenue",
            0
        )
    )
    for opportunity in opportunities
)
ai_expected_revenue = 0.0


if st.session_state.ai_results:

    for index, result in enumerate(
        st.session_state.ai_results
    ):

        decision = str(
            result.get(
                "decision",
                "SKIP"
            )
        ).upper()


        customer_id = str(
            result.get(
                "customer_id",
                ""
            )
        )


        product = str(
            result.get(
                "product",
                ""
            )
        )


        opportunity_key = (
            f"{customer_id}_{product}_{index}"
        )


        merchant_decision = (
            st.session_state.merchant_decisions.get(
                opportunity_key
            )
        )


        # Only merchant-approved opportunities
        # contribute to AI Expected Revenue.

        if (
            decision == "PURSUE"
            and
            merchant_decision == "APPROVED"
        ):

            ai_expected_revenue += safe_float(
                result.get(
                    "expected_revenue",
                    0
                )
            )

# ============================================================
# HERO
# ============================================================

hero_status = (
    "● GEMINI CONNECTED"
    if GEMINI_CONNECTED
    else "● GEMINI NOT CONFIGURED"
)


st.markdown(
    f"""
    <div class="hero">

        <div class="hero-label">
            MERCHANT INTELLIGENCE PLATFORM
        </div>

        <div class="hero-title">
            🚀 RazorGrowth AI
        </div>

        <div class="hero-text">
            Turn transaction intelligence into
            responsible, measurable merchant growth.
        </div>

        <div class="hero-status">
            {hero_status}
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GROWTH COMMAND CENTER
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            Growth Command Center
        </div>

        <div class="section-description">
            Live overview of your merchant growth engine.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


unique_customers = 0


if not transactions.empty:

    possible_customer_columns = [
        "customer_id",
        "customer",
        "customerId",
        "Customer",
    ]

    customer_column = None

    for column in possible_customer_columns:

        if column in transactions.columns:

            customer_column = column
            break

    if customer_column:

        unique_customers = (
            transactions[
                customer_column
            ]
            .astype(str)
            .nunique()
        )

    else:

        unique_customers = len(
            transactions
        )


kpi_columns = st.columns(
    5,
    gap="medium"
)


kpis = [

    (
        "👥",
        "Customers",
        f"{unique_customers:,}",
        "Unique customers",
    ),

    (
        "🎯",
        "Opportunities",
        f"{len(opportunities):,}",
        "Qualified opportunities",
    ),

    (
        "💰",
        "Potential Revenue",
        f"Rs. {potential_revenue:,.0f}",
        "Across opportunities",
    ),

    (
        "🤖",
        "AI Expected Revenue",
        f"Rs. {ai_expected_revenue:,.0f}",
        "PURSUE decisions",
    ),

    (
        "💳",
        "Payment Links",
        f"{len(payment_links):,}",
        "TEST links",
    ),
]


for column, kpi in zip(
    kpi_columns,
    kpis
):

    icon, label, value, subtitle = kpi

    with column:

        st.markdown(
            f"""
            <div class="kpi-card">

                <div class="kpi-icon">
                    {icon}
                </div>

                <div class="kpi-label">
                    {label}
                </div>

                <div class="kpi-value">
                    {value}
                </div>

                <div class="kpi-sub">
                    {subtitle}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# RESPONSIBLE AI PIPELINE
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            🔐 Responsible AI Pipeline
        </div>

        <div class="section-description">
            Every growth action passes through intelligence,
            governance and human approval.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


pipeline = [

    ("🔎", "DETECT", "Agent 1"),

    ("📊", "RANK", "Deterministic"),

    ("🤖", "ANALYZE", "Gemini"),

    ("👤", "APPROVE", "Merchant"),

    ("💳", "EXECUTE", "Razorpay TEST"),

    ("📝", "AUDIT", "Trail"),
]


pipeline_html = (
    '<div class="pipeline-wrapper">'
)


for index, step in enumerate(
    pipeline
):

    icon, name, subtitle = step

    pipeline_html += f"""
        <div class="pipeline-step">

            <div class="pipeline-icon">
                {icon}
            </div>

            <div class="pipeline-name">
                {name}
            </div>

            <div class="pipeline-sub">
                {subtitle}
            </div>

        </div>
    """

    if index < len(pipeline) - 1:

        pipeline_html += """
            <div class="pipeline-arrow">
                →
            </div>
        """


pipeline_html += "</div>"


st.markdown(
    pipeline_html,
    unsafe_allow_html=True,
)


# ============================================================
# SYSTEM STATUS
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            🟢 System Status
        </div>

        <div class="section-description">
            Core services and governance controls.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


status_columns = st.columns(
    4,
    gap="medium"
)


statuses = [

    (
        "🤖",
        "Agent 1",
        "● Ready",
    ),

    (
        "🛡️",
        "Safety Gate",
        "● Active",
    ),

    (
        "📝",
        "Audit Logging",
        "● Active",
    ),

    (
        "💳",
        "Razorpay",
        "● TEST Ready",
    ),
]


for column, status in zip(
    status_columns,
    statuses
):

    icon, name, state = status

    with column:

        st.markdown(
            f"""
            <div class="status-card">

                <div class="status-icon">
                    {icon}
                </div>

                <div class="status-name">
                    {name}
                </div>

                <div class="status-ready">
                    {state}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# OPPORTUNITY PRIORITIES
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            🎯 Opportunity Priorities
        </div>

        <div class="section-description">
            Distribution of deterministic growth opportunities.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


priority_columns = st.columns(
    3,
    gap="medium"
)


priority_data = [

    (
        "🔴",
        high_priority,
        "HIGH PRIORITY",
    ),

    (
        "🟠",
        medium_priority,
        "MEDIUM PRIORITY",
    ),

    (
        "🟢",
        low_priority,
        "LOW PRIORITY",
    ),
]


for column, priority in zip(
    priority_columns,
    priority_data
):

    icon, number, name = priority

    with column:

        st.markdown(
            f"""
            <div class="priority-card">

                <div class="priority-icon">
                    {icon}
                </div>

                <div class="priority-number">
                    {number:,}
                </div>

                <div class="priority-name">
                    {name}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# TRANSACTION INTELLIGENCE
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            📊 Transaction Intelligence
        </div>

        <div class="section-description">
            Source transaction data used by Agent 1.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


with st.expander(
    "📂 View transaction dataset"
):

    if transactions.empty:

        st.warning(
            "No transaction data found."
        )

    else:

        st.dataframe(
            transactions,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# GROWTH OPPORTUNITIES
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            🎯 Growth Opportunities
        </div>

        <div class="section-description">
            Evidence-based cross-sell opportunities
            identified by the deterministic growth engine.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


filter_col1, filter_col2, filter_col3 = st.columns(
    [1, 1, 2]
)


priority_options = [
    "ALL",
    "HIGH",
    "MEDIUM",
    "LOW",
]


with filter_col1:

    selected_priority = st.selectbox(
        "Priority",
        priority_options,
        key="priority_filter",
    )


customer_values = ["ALL"]


for opportunity in opportunities:

    customer = opportunity.get(
        "customer_id"
    )

    if customer is not None:

        customer_string = str(
            customer
        )

        if customer_string not in customer_values:

            customer_values.append(
                customer_string
            )


with filter_col2:

    selected_customer = st.selectbox(
        "Customer",
        customer_values,
        key="customer_filter",
    )


with filter_col3:

    st.markdown(
        f"""
        <div style="
            margin-top:31px;
            color:#64748b;
            font-size:12px;
        ">
            Showing {len(opportunities):,} qualified opportunities
        </div>
        """,
        unsafe_allow_html=True,
    )


filtered_opportunities = []


for opportunity in opportunities:

    opportunity_priority = str(
        opportunity.get(
            "priority",
            ""
        )
    ).upper()


    opportunity_customer = str(
        opportunity.get(
            "customer_id",
            ""
        )
    )


    if (
        selected_priority != "ALL"
        and opportunity_priority
        != selected_priority
    ):
        continue


    if (
        selected_customer != "ALL"
        and opportunity_customer
        != selected_customer
    ):
        continue


    filtered_opportunities.append(
        opportunity
    )


DISPLAY_LIMIT = 20

display_opportunities = (
    filtered_opportunities[
        :DISPLAY_LIMIT
    ]
)


st.caption(
    f"Showing {len(display_opportunities):,} of "
    f"{len(filtered_opportunities):,} matching opportunities."
)


# ============================================================
# OPPORTUNITY RENDERING
# ============================================================

for index, opportunity in enumerate(
    display_opportunities
):

    customer_id = opportunity.get(
        "customer_id",
        "Unknown"
    )

    trigger_product = opportunity.get(
        "trigger_product",
        "Unknown"
    )

    recommendation = opportunity.get(
        "recommendation",
        "Unknown"
    )

    priority = str(
        opportunity.get(
            "priority",
            "N/A"
        )
    ).upper()


    score = safe_float(
        opportunity.get(
            "opportunity_score",
            0
        )
    )


    confidence = safe_float(
        opportunity.get(
            "confidence",
            0
        )
    )


    potential = safe_float(
        opportunity.get(
            "potential_revenue",
            0
        )
    )


    reason = opportunity.get(
        "reason",
        "No reasoning available."
    )


    if priority == "HIGH":

        badge_class = "badge-high"
        badge_text = "🔴 HIGH"

    elif priority == "LOW":

        badge_class = "badge-low"
        badge_text = "🟢 LOW"

    else:

        badge_class = "badge-medium"
        badge_text = "🟠 MEDIUM"


    st.markdown(
        f"""
        <div class="opportunity-card">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:15px;
            ">

                <div>

                    <div class="customer-name">
                        👤 Customer {safe_html(customer_id)}
                    </div>

                    <div class="product-flow">
                        {safe_html(trigger_product)}
                        <strong>→</strong>
                        {safe_html(recommendation)}
                    </div>

                </div>

                <div>
                    <span class="badge {badge_class}">
                        {badge_text}
                    </span>
                </div>

            </div>


            <div style="
                display:grid;
                grid-template-columns:
                    repeat(3, 1fr);
                gap:20px;
                margin-top:22px;
            ">

                <div>

                    <div class="metric-label-small">
                        OPPORTUNITY SCORE
                    </div>

                    <div class="metric-value-small">
                        {score:.2f}
                    </div>

                </div>


                <div>

                    <div class="metric-label-small">
                        CONFIDENCE
                    </div>

                    <div class="metric-value-small">
                        {confidence * 100:.0f}%
                    </div>

                </div>


                <div>

                    <div class="metric-label-small">
                        POTENTIAL REVENUE
                    </div>

                    <div class="metric-value-small">
                        Rs. {potential:,.0f}
                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    with st.expander(
        f"🔍 View reasoning — Customer {safe_html(customer_id)}"
    ):

        st.write(
            reason
        )


if len(filtered_opportunities) > DISPLAY_LIMIT:

    st.info(
        f"{len(filtered_opportunities) - DISPLAY_LIMIT:,} "
        "additional opportunities are available "
        "through the filters."
    )
# ============================================================
# GEMINI GROWTH ADVISOR
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-title">
            🤖 Gemini Growth Advisor
        </div>
        <div class="section-description">
            AI reviews deterministic opportunities and provides
            advisory decisions. Gemini never executes payments.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ai-card">
        <div class="ai-title">
            🧠 Agent 2 — Advisory Intelligence
        </div>
        <div class="ai-text">
            Gemini evaluates qualified opportunities and recommends
            whether an opportunity should be pursued.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GEMINI CONNECTION
# ============================================================

if GEMINI_CONNECTED:

    st.success("Gemini API configured and ready.")

else:

    st.error("Gemini API is not available.")


# ============================================================
# RUN GEMINI ANALYSIS
# ============================================================

if st.button(
    "🤖 Run Gemini Analysis",
    type="primary",
    width="stretch",
):

    if not GEMINI_CONNECTED:

        st.error("Gemini is not configured.")

    elif not opportunities:

        st.warning("No qualified opportunities available.")

    else:

        with st.spinner(
            "Gemini is reviewing qualified opportunities..."
        ):

            try:

                results = generate_batch_recommendations(
                    display_opportunities
                )

                st.session_state.ai_results = results
                st.session_state.gemini_error = None

            except Exception as error:

                st.session_state.ai_results = None
                st.session_state.gemini_error = str(error)


# ============================================================
# GEMINI ERROR
# ============================================================

if st.session_state.gemini_error:

    st.error("Gemini analysis failed.")

    st.code(
        st.session_state.gemini_error
    )
# ============================================================
# GEMINI RESULTS + MERCHANT APPROVAL
# ============================================================

if st.session_state.ai_results:

    pursue_count = sum(
        1
        for result in st.session_state.ai_results
        if result.get("decision") == "PURSUE"
    )

    skip_count = sum(
        1
        for result in st.session_state.ai_results
        if result.get("decision") == "SKIP"
    )

    st.markdown(
        "### 📈 Gemini Analysis Results"
    )

    result_columns = st.columns(3)

    with result_columns[0]:
        st.metric(
            "Analyzed",
            len(st.session_state.ai_results)
        )

    with result_columns[1]:
        st.metric(
            "PURSUE",
            pursue_count
        )

    with result_columns[2]:
        st.metric(
            "SKIP",
            skip_count
        )


    # --------------------------------------------------------
    # SESSION STATE
    # --------------------------------------------------------

    if "merchant_decisions" not in st.session_state:
        st.session_state.merchant_decisions = {}


    # ========================================================
    # SAVE AUDIT RECORD
    # ========================================================

    def save_audit_record(record):

        audit_directory = AUDIT_FILE.parent

        audit_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        existing_logs = []

        if AUDIT_FILE.exists():

            try:

                with open(
                    AUDIT_FILE,
                    "r",
                    encoding="utf-8"
                ) as file:

                    content = file.read().strip()

                if content:

                    loaded = json.loads(content)

                    if isinstance(loaded, list):
                        existing_logs = loaded

            except Exception:

                existing_logs = []


        existing_logs.append(record)


        with open(
            AUDIT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                existing_logs,
                file,
                indent=2,
                ensure_ascii=False
            )


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    for index, result in enumerate(
        st.session_state.ai_results[:20]
    ):

        decision = str(
            result.get(
                "decision",
                "SKIP"
            )
        ).upper()


        customer_id = result.get(
            "customer_id",
            "Unknown"
        )


        product = result.get(
            "product",
            "Unknown"
        )


        expected = safe_float(
            result.get(
                "expected_revenue",
                0
            )
        )


        confidence = safe_float(
            result.get(
                "confidence",
                0
            )
        )


        opportunity_key = (
            f"{customer_id}_{product}_{index}"
        )


        merchant_decision = (
            st.session_state.merchant_decisions.get(
                opportunity_key
            )
        )


        # ====================================================
        # CARD
        # ====================================================

        with st.container(border=True):

            st.markdown(
                f"**👤 Customer {safe_html(customer_id)}**"
            )


            st.write(
                f"🎯 Recommended Product: "
                f"**{safe_html(product)}**"
            )


            st.write(
                f"🤖 Gemini Recommendation: "
                f"**{decision}**"
            )


            st.write(
                f"💰 Expected Revenue: "
                f"**Rs. {expected:,.2f}**"
            )


            if confidence:

                st.write(
                    f"📊 Confidence: "
                    f"**{confidence:.0%}**"
                )


            # =================================================
            # ALREADY APPROVED
            # =================================================

            if merchant_decision == "APPROVED":

                st.success(
                    "✅ Merchant APPROVED"
                )


            # =================================================
            # ALREADY DECLINED
            # =================================================

            elif merchant_decision == "DECLINED":

                st.error(
                    "❌ Merchant DECLINED"
                )


            # =================================================
            # PENDING
            # =================================================

            else:

                button_col1, button_col2 = st.columns(2)


                # =================================================
                # APPROVE
                # =================================================

                with button_col1:

                    if st.button(
                        "✅ APPROVE",
                        key=f"approve_{opportunity_key}",
                        width="stretch",
                    ):

                        # -----------------------------------------
                        # Merchant decision
                        # -----------------------------------------

                        st.session_state.merchant_decisions[
                            opportunity_key
                        ] = "APPROVED"


                        # -----------------------------------------
                        # Duplicate prevention
                        # -----------------------------------------

                        existing_payment = (
                            find_existing_payment_link(
                                customer_id,
                                product
                            )
                        )


                        if existing_payment:

                            st.warning(
                                "⚠️ Duplicate prevented. "
                                "Payment link already exists."
                            )

                            # Do NOT create another payment link.
                            # Do NOT add another audit record.


                        else:

                            # -------------------------------------
                            # Razorpay TEST
                            # -------------------------------------

                            try:

                                payment_result = (
                                    create_test_payment_link(
                                        customer_id,
                                        product
                                    )
                                )


                                if payment_result:

                                    # ---------------------------------
                                    # Extract Razorpay information
                                    # ---------------------------------

                                    if isinstance(
                                        payment_result,
                                        dict
                                    ):

                                        payment_link_id = (
                                            payment_result.get(
                                                "id",
                                                ""
                                            )
                                        )

                                        payment_link_url = (
                                            payment_result.get(
                                                "short_url",
                                                ""
                                            )
                                        )

                                    else:

                                        payment_link_id = str(
                                            payment_result
                                        )

                                        payment_link_url = ""


                                    # ---------------------------------
                                    # Save AUDIT record
                                    # ---------------------------------

                                    audit_record = {

                                        "timestamp":
                                            datetime.now().isoformat(),

                                        "customer_id":
                                            customer_id,

                                        "product":
                                            product,

                                        "merchant_approval":
                                            "APPROVED",

                                        "action_status":
                                            "PAYMENT_LINK_CREATED",

                                        "expected_revenue":
                                            expected,

                                        "payment_link_id":
                                            payment_link_id,

                                        "payment_link_url":
                                            payment_link_url,

                                        "decision":
                                            decision,

                                        "source":
                                            "Gemini",

                                    }


                                    save_audit_record(
                                        audit_record
                                    )


                                    # ---------------------------------
                                    # Show success
                                    # ---------------------------------

                                    st.success(
                                        "✅ Merchant approved — "
                                        "Razorpay TEST payment link created."
                                    )


                                    if payment_link_id:

                                        st.write(
                                            f"💳 Payment Link ID: "
                                            f"**{safe_html(payment_link_id)}**"
                                        )


                                    if payment_link_url:

                                        st.link_button(
                                            "🔗 Open TEST Payment Link",
                                            payment_link_url,
                                            width="content",
                                        )


                                    # ---------------------------------
                                    # Refresh dashboard
                                    # ---------------------------------

                                    st.rerun()


                                else:

                                    st.error(
                                        "❌ Razorpay TEST payment link "
                                        "was not created."
                                    )


                            except Exception as error:

                                st.error(
                                    "❌ Payment link creation failed."
                                )

                                st.code(
                                    str(error)
                                )


                # =================================================
                # DECLINE
                # =================================================

                with button_col2:

                    if st.button(
                        "❌ DECLINE",
                        key=f"decline_{opportunity_key}",
                        width="stretch",
                    ):

                        # -----------------------------------------
                        # Merchant decision
                        # -----------------------------------------

                        st.session_state.merchant_decisions[
                            opportunity_key
                        ] = "DECLINED"


                        # -----------------------------------------
                        # Save rejected audit record
                        # -----------------------------------------

                        audit_record = {

                            "timestamp":
                                datetime.now().isoformat(),

                            "customer_id":
                                customer_id,

                            "product":
                                product,

                            "merchant_approval":
                                "REJECTED",

                            "action_status":
                                "MERCHANT_DECLINED",

                            "expected_revenue":
                                expected,

                            "payment_link_id":
                                "",

                            "payment_link_url":
                                "",

                            "decision":
                                decision,

                            "source":
                                "Gemini",

                        }


                        save_audit_record(
                            audit_record
                        )


                        st.warning(
                            f"❌ Merchant declined — "
                            f"Customer {customer_id} → {product}"
                        )


                        # Refresh so analytics update
                        st.rerun()


# ============================================================
# MERCHANT APPROVAL ANALYTICS
# ============================================================

st.markdown(
    """
    <div class="section-header">
        <div class="section-title">
            👤 Merchant Approval Analytics
        </div>
        <div class="section-description">
            Human governance activity across growth actions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


approval_total = (
    len(approved)
    + len(rejected)
)


approval_rate = (
    (
        len(approved)
        / approval_total
        * 100
    )
    if approval_total
    else 0
)


approval_columns = st.columns(3)


with approval_columns[0]:

    st.metric(
        "Approved",
        len(approved)
    )


with approval_columns[1]:

    st.metric(
        "Rejected",
        len(rejected)
    )


with approval_columns[2]:

    st.metric(
        "Approval Rate",
        f"{approval_rate:.0f}%"
    )


# ============================================================
# PAYMENT LINKS
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            💳 Razorpay TEST Payment Links
        </div>

        <div class="section-description">
            Payment links created only after merchant approval.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


if not payment_links:

    st.info(
        "No TEST payment links have been created yet."
    )

else:

    for log in reversed(
        payment_links
    ):

        customer_id = log.get(
            "customer_id",
            "Unknown"
        )

        product = log.get(
            "product",
            "Unknown"
        )

        expected_revenue = safe_float(
            log.get(
                "expected_revenue",
                0
            )
        )

        payment_link_id = log.get(
            "payment_link_id",
            "N/A"
        )

        payment_link_url = log.get(
            "payment_link_url",
            ""
        )

        st.markdown(
            f"""
            <div class="payment-card">

                <div class="payment-label">
                    CUSTOMER
                </div>

                <div class="payment-value">
                    {safe_html(customer_id)}
                </div>

                <br>

                <div class="payment-label">
                    PRODUCT
                </div>

                <div class="payment-value">
                    {safe_html(product)}
                </div>

                <br>

                <div class="payment-label">
                    EXPECTED REVENUE
                </div>

                <div class="payment-value">
                    Rs. {expected_revenue:,.0f}
                </div>

                <br>

                <div class="payment-label">
                    PAYMENT LINK ID
                </div>

                <div class="payment-value">
                    {safe_html(payment_link_id)}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if payment_link_url:

            st.link_button(
                "🔗 Open TEST Payment Link",
                payment_link_url,
                width="content",
            )


# ============================================================
# AUDIT HISTORY
# ============================================================

st.markdown(
    """
    <div class="section-header">

        <div class="section-title">
            📝 Audit History
        </div>

        <div class="section-description">
            Transparent record of merchant decisions and actions.
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


with st.expander(
    "📋 View audit history"
):

    if not audit_logs:

        st.info(
            "No audit records found."
        )

    else:

        audit_dataframe = pd.DataFrame(
            audit_logs
        )

        st.dataframe(
            audit_dataframe,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        <strong>
            🚀 RazorGrowth AI
        </strong>

        <br><br>

        Responsible merchant growth powered by
        deterministic intelligence, AI advisory,
        human approval, duplicate prevention,
        Razorpay TEST execution and auditability.

    </div>
    """,
    unsafe_allow_html=True,
)