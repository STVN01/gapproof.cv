# ════════════════════════════════════════════════════════════════════════
# GAPPROOF — Premium SaaS redesign
# Presentation layer: page config · theme tokens · CSS · sidebar
# All business logic (Groq calls, rubric scoring, annotated CV) is unchanged
# below the GROQ CLIENT marker.
# ════════════════════════════════════════════════════════════════════════

# ─── IMPORTS ────────────────────────────────────────────────────────────
import streamlit as st        # Web framework — renders the whole UI
import json                   # Parses the AI's JSON responses
import pdfplumber             # Extracts text from uploaded PDF CVs
from groq import Groq         # AI client — sends prompts, returns analysis

# ─── PAGE CONFIG ────────────────────────────────────────────────────────
# Must be the first Streamlit call. Sets the browser tab + base layout.
st.set_page_config(
    page_title="GapProof",
    layout="wide",
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# ─── SESSION STATE ──────────────────────────────────────────────────────
# session_state is Streamlit's memory that survives reruns (every click
# reruns the whole script). We seed defaults on first load only.
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"          # start in dark mode
if "nav_expanded" not in st.session_state:
    st.session_state.nav_expanded = True     # sidebar starts open
if "page" not in st.session_state:
    st.session_state.page = "📋 Resume Auditor"  # default section
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None       # holds the last analysis
if "cv_full" not in st.session_state:
    st.session_state.cv_full = ""            # full CV text for annotation

# ─── THEME TOKENS ───────────────────────────────────────────────────────
# A "design token" is a named colour/value used everywhere instead of
# hard-coded hex. Define once here, reference by name in the CSS. Swapping
# the theme = swapping this one dictionary. This is why light mode now
# works: EVERY colour (including all text) comes from these tokens, so
# nothing can be left as an un-themed dark value on a light background.
if st.session_state.theme == "Dark":
    T = {
        "bg":        "#070b14",   # app background — near-black navy
        "bg2":       "#0c1220",   # secondary background (hero glow base)
        "surface":   "#0f1626",   # cards / panels
        "surface2":  "#141d30",   # raised elements (inputs, hover)
        "border":    "#1e2a42",   # hairline borders
        "border2":   "#2a3a58",   # stronger borders (focus)
        "text":      "#eef2f9",   # primary text — must be light on dark
        "text2":     "#aab4c8",   # secondary text
        "muted":     "#6b7890",   # captions, placeholders
        "accent":    "#5b8cff",   # primary brand — periwinkle blue
        "accent2":   "#8b5cf6",   # gradient partner — violet
        "accentText":"#ffffff",   # text on top of accent fills
        "accentSoft":"rgba(91,140,255,0.10)",   # tinted backgrounds
        "accentLine":"rgba(91,140,255,0.30)",   # tinted borders
        "green":     "#3ddc97",
        "greenSoft": "rgba(61,220,151,0.12)",
        "amber":     "#f5b544",
        "amberSoft": "rgba(245,181,68,0.12)",
        "red":       "#ff6b7d",
        "redSoft":   "rgba(255,107,125,0.12)",
        "glow":      "0 8px 30px rgba(91,140,255,0.25)",  # button glow
        "cardShadow":"0 4px 24px rgba(0,0,0,0.4)",
        "gridLine":  "rgba(91,140,255,0.04)",  # blueprint grid opacity
    }
else:
    T = {
        "bg":        "#f7f9fc",   # app background — soft cool white
        "bg2":       "#eef2f9",
        "surface":   "#ffffff",   # cards pop white
        "surface2":  "#f2f5fb",
        "border":    "#e3e9f2",
        "border2":   "#cfd8e8",
        "text":      "#0d1526",   # primary text — near-black (visible!)
        "text2":     "#3f4b60",   # secondary — dark slate (visible!)
        "muted":     "#7a869c",   # captions — mid slate (visible!)
        "accent":    "#4f6ef7",   # indigo-blue
        "accent2":   "#7c5cf0",   # violet
        "accentText":"#ffffff",
        "accentSoft":"rgba(79,110,247,0.08)",
        "accentLine":"rgba(79,110,247,0.22)",
        "green":     "#0ea770",
        "greenSoft": "rgba(14,167,112,0.10)",
        "amber":     "#c77f14",
        "amberSoft": "rgba(199,127,20,0.10)",
        "red":       "#e0455e",
        "redSoft":   "rgba(224,69,94,0.09)",
        "glow":      "0 8px 24px rgba(79,110,247,0.20)",
        "cardShadow":"0 2px 16px rgba(20,40,80,0.06)",
        "gridLine":  "rgba(79,110,247,0.05)",
    }

# ─── BACKWARD-COMPAT ALIASES ────────────────────────────────────────────
# The logic section (below) references these older variable names.
# Mapping them to the new token dict means the business code needs
# ZERO changes — it keeps working while the look is fully new.
BG        = T["bg"]
SURFACE   = T["surface"]
BORDER    = T["border"]
TEXT      = T["text"]
MUTED     = T["muted"]
ACCENT    = T["accent"]
ACCENT_2  = T["accent2"]
ACCENT_DIM= T["accentSoft"]
GREEN     = T["green"]
AMBER     = T["amber"]
RED       = T["red"]
CARD_BG   = T["surface2"]
GLOW      = T["glow"]

# Sidebar width driven by the collapse toggle
SIDEBAR_W = "260px" if st.session_state.nav_expanded else "84px"

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────
# One big stylesheet. f-string slots the tokens in. Every colour is a
# token, so both themes are fully covered — no orphaned dark values.
css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {{ font-family:'Inter',sans-serif; }}
.stApp {{
    background:
        radial-gradient(1200px 600px at 80% -10%, {T['accentSoft']}, transparent 60%),
        linear-gradient({T['gridLine']} 1px, transparent 1px),
        linear-gradient(90deg, {T['gridLine']} 1px, transparent 1px),
        {T['bg']};
    background-size: auto, 48px 48px, 48px 48px, auto;
    color: {T['text']};
}}
/* Hide Streamlit chrome we replace ourselves */
#MainMenu, footer {{ visibility:hidden; }}
[data-testid="stDecoration"] {{ display:none !important; }}
[data-testid="stToolbar"] {{ display:none !important; }}
header[data-testid="stHeader"] {{ background:transparent !important; height:0 !important; }}
.block-container {{ padding-top:2.5rem !important; max-width:1280px; }}

/* ── EVERY text element inherits a themed colour (light-mode fix) ── */
p, span, div, label, li, td, th, h1, h2, h3, h4, h5, h6 {{ color:{T['text']}; }}
.stMarkdown, .stMarkdown p {{ color:{T['text']}; }}
small, .stCaption, [data-testid="stCaptionContainer"] {{ color:{T['muted']} !important; }}
[data-testid="stCaptionContainer"] p {{ color:{T['muted']} !important; }}

/* ── Headings ── */
h1,h2,h3 {{ font-family:'Space Grotesk',sans-serif !important; letter-spacing:-0.02em; color:{T['text']} !important; }}

/* ── Hero band ── */
.hero {{
    background: linear-gradient(135deg, {T['surface']}, {T['bg2']});
    border:1px solid {T['border']};
    border-radius:20px;
    padding:2rem 2.25rem;
    margin-bottom:1.75rem;
    box-shadow:{T['cardShadow']};
    position:relative;
    overflow:hidden;
}}
.hero::before {{
    content:''; position:absolute; top:-40%; right:-10%;
    width:340px; height:340px; border-radius:50%;
    background:radial-gradient(circle, {T['accentSoft']}, transparent 70%);
    pointer-events:none;
}}
.hero-badge {{
    display:inline-block; font-size:11px; font-weight:700; letter-spacing:0.14em;
    text-transform:uppercase; color:{T['accent']};
    background:{T['accentSoft']}; border:1px solid {T['accentLine']};
    padding:5px 14px; border-radius:100px; margin-bottom:0.9rem;
}}
.hero-title {{
    font-family:'Space Grotesk',sans-serif; font-size:2.4rem; font-weight:700;
    line-height:1.1; margin:0 0 0.5rem 0; color:{T['text']};
}}
.hero-title .grad {{
    background:linear-gradient(120deg, {T['accent']}, {T['accent2']});
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
.hero-sub {{ font-size:1rem; color:{T['text2']}; max-width:640px; line-height:1.6; }}

/* ── Cards / panels ── */
.panel, .result-section {{
    background:{T['surface']};
    border:1px solid {T['border']};
    border-radius:16px;
    padding:1.4rem 1.5rem;
    margin-bottom:1rem;
    box-shadow:{T['cardShadow']};
}}
.panel-title {{
    font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:600;
    color:{T['text']}; margin:0 0 0.35rem 0;
}}
.panel-sub {{ font-size:0.82rem; color:{T['muted']}; margin-bottom:0.75rem; }}
.result-section-title {{
    font-family:'Space Grotesk',sans-serif; font-size:0.98rem; font-weight:600;
    color:{T['text']}; margin-bottom:0.9rem;
}}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {{
    background:{T['surface2']} !important;
    border:1px solid {T['border']} !important;
    border-radius:12px !important;
    color:{T['text']} !important;
    font-size:0.9rem !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color:{T['muted']} !important; opacity:1 !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color:{T['accent']} !important;
    box-shadow:0 0 0 3px {T['accentSoft']} !important;
}}
.stSelectbox div[data-baseweb="select"] > div {{
    background:{T['surface2']} !important;
    border:1px solid {T['border']} !important;
    border-radius:12px !important;
    color:{T['text']} !important;
}}
.stSelectbox div[data-baseweb="select"] span {{ color:{T['text']} !important; }}
div[data-baseweb="popover"] li {{ background:{T['surface']} !important; color:{T['text']} !important; }}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    background:{T['surface2']} !important;
    border:1.5px dashed {T['border2']} !important;
    border-radius:12px !important;
    padding:0.5rem !important;
}}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small {{ color:{T['text2']} !important; }}
[data-testid="stFileUploader"] button {{
    background:{T['surface']} !important;
    border:1px solid {T['border2']} !important;
    color:{T['text']} !important;
    border-radius:9px !important;
}}

/* ── Buttons ── */
.stButton button {{
    border-radius:12px !important; font-weight:600 !important;
    transition:transform .12s ease, filter .12s ease !important;
}}
.stButton button[kind="primary"] {{
    background:linear-gradient(120deg, {T['accent']}, {T['accent2']}) !important;
    border:none !important; color:{T['accentText']} !important;
    box-shadow:{T['glow']} !important; padding:0.7rem 2rem !important;
    font-size:0.95rem !important;
}}
.stButton button[kind="primary"]:hover {{ transform:translateY(-1px); filter:brightness(1.08); }}
.stButton button[kind="secondary"] {{
    background:{T['surface2']} !important;
    border:1px solid {T['border2']} !important;
    color:{T['text']} !important;
}}
.stButton button[kind="secondary"]:hover {{ border-color:{T['accent']} !important; }}

/* ── Score card ── */
.score-card {{
    background:linear-gradient(135deg, {T['surface']}, {T['surface2']});
    border:1px solid {T['border']}; border-radius:18px;
    padding:1.6rem; display:flex; align-items:center; gap:1.75rem;
    margin-bottom:1.25rem; box-shadow:{T['cardShadow']};
}}
.score-ring {{
    min-width:104px; height:104px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-family:'Space Grotesk',sans-serif; font-size:2.1rem; font-weight:700;
    position:relative;
}}
.score-label {{ font-family:'Space Grotesk'; font-size:1.05rem; font-weight:600; color:{T['text']}; }}
.score-verdict {{ font-size:0.9rem; color:{T['text2']}; margin-top:2px; }}

/* ── Badges ── */
.badge-row {{ display:flex; gap:0.75rem; margin-bottom:1.5rem; }}
.badge {{
    flex:1; padding:0.65rem 1rem; border-radius:12px;
    font-size:0.85rem; font-weight:600; text-align:center;
}}
.badge-red   {{ background:{T['redSoft']};   border:1px solid {T['red']};   color:{T['red']}; }}
.badge-amber {{ background:{T['amberSoft']}; border:1px solid {T['amber']}; color:{T['amber']}; }}
.badge-green {{ background:{T['greenSoft']}; border:1px solid {T['green']}; color:{T['green']}; }}

/* ── Keyword chips ── */
.kw-found {{ display:inline-block; background:{T['greenSoft']}; border:1px solid {T['green']};
            color:{T['green']}; font-size:0.76rem; font-weight:500; padding:4px 11px;
            border-radius:100px; margin:3px; }}
.kw-missing {{ display:inline-block; background:{T['redSoft']}; border:1px solid {T['red']};
            color:{T['red']}; font-size:0.76rem; font-weight:500; padding:4px 11px;
            border-radius:100px; margin:3px; }}

/* ── Annotated CV document ── */
.cv-doc {{
    background:{T['surface2']}; border:1px solid {T['border']}; border-radius:14px;
    padding:1.2rem 1.4rem; max-height:480px; overflow-y:auto;
    font-family:'JetBrains Mono',monospace; font-size:0.82rem; line-height:1.9;
    color:{T['text2']}; white-space:pre-wrap;
}}
.hl-good {{ background:{T['greenSoft']}; border-bottom:2px solid {T['green']}; border-radius:3px; padding:0 2px; color:{T['text']}; }}
.hl-bad  {{ background:{T['redSoft']};  border-bottom:2px dashed {T['red']}; border-radius:3px; padding:0 2px; color:{T['text']}; }}
.legend-chip {{ display:inline-block; font-size:0.74rem; padding:3px 11px; border-radius:100px; margin-right:8px; margin-bottom:8px; }}

/* ── Skill coverage bars ── */
.cov-row {{ margin-bottom:0.7rem; }}
.cov-head {{ display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.84rem; }}
.cov-name {{ font-weight:600; color:{T['text']}; }}
.cov-pct  {{ color:{T['muted']}; font-family:'JetBrains Mono'; }}
.cov-track {{ background:{T['border']}; border-radius:100px; height:8px; overflow:hidden; }}
.cov-fill  {{ height:8px; border-radius:100px; transition:width .5s ease; }}

/* ── Callout ── */
.callout {{
    background:{T['accentSoft']}; border:1px solid {T['accentLine']};
    border-radius:12px; padding:0.9rem 1.15rem; font-size:0.86rem; color:{T['accent']};
    margin-bottom:1rem;
}}

/* ── Info / success / warning / error boxes ── */
.stAlert {{ border-radius:12px !important; }}
.stAlert p {{ color:{T['text']} !important; }}

/* ── Tabs ── */
button[data-baseweb="tab"] {{ color:{T['muted']} !important; background:transparent !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color:{T['accent']} !important; }}
[data-baseweb="tab-highlight"] {{ background:{T['accent']} !important; }}

/* ── Expander ── */
div[data-testid="stExpander"] {{
    background:{T['surface']} !important; border:1px solid {T['border']} !important;
    border-radius:14px !important;
}}
div[data-testid="stExpander"] summary {{ color:{T['text']} !important; }}
div[data-testid="stExpander"] p {{ color:{T['text2']} !important; }}

/* ── Sliders ── */
.stSlider label {{ color:{T['text']} !important; }}
.stSlider [data-baseweb="slider"] div[role="slider"] {{ background:{T['accent']} !important; }}

/* ── Dividers ── */
hr {{ border-color:{T['border']} !important; }}

/* ── Help tooltips (the `?`/hover text on buttons) ──
   Streamlit renders these as a floating popover. Its default text
   colour is set for dark mode, so on a light background it was
   near-invisible. Force BOTH the popover box and its text to
   themed values so it reads in either mode. */
[data-testid="stTooltipContent"] {{
    background:{T['surface2']} !important;
    border:1px solid {T['border2']} !important;
    color:{T['text']} !important;
    border-radius:8px !important;
    box-shadow:{T['cardShadow']} !important;
}}
[data-testid="stTooltipContent"] * {{ color:{T['text']} !important; }}
/* Some Streamlit versions use a baseweb tooltip instead — cover both */
div[data-baseweb="tooltip"], div[data-baseweb="tooltip"] * {{
    background:{T['surface2']} !important;
    color:{T['text']} !important;
    border-radius:8px !important;
}}

/* ═══════════════════ SIDEBAR ═══════════════════════════════════════ */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"][aria-expanded="true"],
section[data-testid="stSidebar"][aria-expanded="false"] {{
    min-width:{SIDEBAR_W} !important; max-width:{SIDEBAR_W} !important; width:{SIDEBAR_W} !important;
    transform:none !important; margin-left:0 !important; visibility:visible !important;
    background:{T['surface']} !important; border-right:1px solid {T['border']} !important;
    transition:min-width .2s ease, max-width .2s ease !important;
}}
[data-testid="stSidebar"] > div:first-child {{ padding:1rem 0.6rem !important; }}
/* Kill Streamlit's native collapse arrows — our own button replaces them */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebar"] button[kind="header"] {{ display:none !important; }}

/* Brand mark */
.brand {{ text-align:center; padding:0.4rem 0 0.9rem 0; }}
.brand-full {{ font-family:'Space Grotesk'; font-weight:700; font-size:1.25rem;
    background:linear-gradient(120deg,{T['accent']},{T['accent2']});
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
.brand-mark {{ font-size:1.6rem; }}

/* Kill the radio's own "Navigate" label (prevents the cramped "N av ig" wrap) */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] .stRadio > label:first-child {{
    display:none !important; height:0 !important; visibility:hidden !important;
}}
/* Radio → vertical nav tiles */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
    display:flex !important; flex-direction:column !important; gap:0.4rem !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
    display:flex !important; align-items:center !important;
    justify-content:{("flex-start" if st.session_state.nav_expanded else "center")} !important;
    gap:0.6rem !important;
    width:100% !important; min-height:46px !important;
    padding:{("0 0.9rem" if st.session_state.nav_expanded else "0")} !important;
    border-radius:12px !important; border:1px solid transparent !important;
    cursor:pointer !important; color:{T['text2']} !important;
    font-size:{("0.92rem" if st.session_state.nav_expanded else "1.3rem")} !important;
    font-weight:500 !important; transition:all .14s ease !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label > div:first-child {{ display:none !important; }}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {{
    background:{T['surface2']} !important; color:{T['text']} !important;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {{
    background:{T['accentSoft']} !important; border:1px solid {T['accentLine']} !important;
    color:{T['accent']} !important; box-shadow:{T['glow']} !important;
}}
/* Sidebar buttons (toggle + theme) */
[data-testid="stSidebar"] .stButton button {{
    width:100% !important; min-height:44px !important;
    background:{T['surface2']} !important; border:1px solid {T['border']} !important;
    color:{T['text']} !important; border-radius:12px !important; font-size:1.1rem !important;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    border-color:{T['accent']} !important; color:{T['accent']} !important;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ─── SIDEBAR ────────────────────────────────────────────────────────────
NAV_FULL = ["📋 Resume Auditor", "🛠 Project Architect",
            "💬 Interview Coach", "📚 Learning Path"]

with st.sidebar:
    # Brand — full wordmark when expanded, just the mark when slim
    if st.session_state.nav_expanded:
        st.markdown('<div class="brand"><span class="brand-full">🎯 GapProof</span></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="brand"><span class="brand-mark">🎯</span></div>',
                    unsafe_allow_html=True)

    # Collapse / expand toggle (‹ when open, ☰ when slim)
    toggle_icon = "‹  Collapse" if st.session_state.nav_expanded else "☰"
    if st.button(toggle_icon, key="nav_toggle", use_container_width=True,
                 help="Expand / collapse navigation"):
        st.session_state.nav_expanded = not st.session_state.nav_expanded
        st.rerun()

    st.markdown(f"<hr style='margin:0.6rem 0;border-color:{T['border']}'>", unsafe_allow_html=True)

    # Navigation labels adapt to width: full text vs icon only
    if st.session_state.nav_expanded:
        display_opts = NAV_FULL
    else:
        display_opts = [o.split()[0] for o in NAV_FULL]

    cur_idx = NAV_FULL.index(st.session_state.page)
    nav_choice = st.radio(
        "Navigate", display_opts, index=cur_idx,
        label_visibility="collapsed",
        key=f"nav_{st.session_state.nav_expanded}",
    )
    st.session_state.page = NAV_FULL[display_opts.index(nav_choice)]
    app_mode = st.session_state.page

    st.markdown(f"<hr style='margin:0.6rem 0;border-color:{T['border']}'>", unsafe_allow_html=True)

    # Theme toggle
    theme_label = ("☀️  Light mode" if st.session_state.theme == "Dark" else "🌙  Dark mode") \
                  if st.session_state.nav_expanded else \
                  ("☀️" if st.session_state.theme == "Dark" else "🌙")
    if st.button(theme_label, key="theme_toggle", use_container_width=True, help="Switch theme"):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
        st.rerun()

# ─── API KEY (main area, not the narrow rail) ───────────────────────────
def read_secret(name):
    # st.secrets raises an error (not just "missing") when there is no
    # secrets file at all — e.g. running locally. try/except turns that
    # into a plain None so the app falls back to the input box instead.
    try:
        return st.secrets[name]
    except Exception:
        return None

api_key = read_secret("GROQ_API_KEY")
if not api_key:
    st.markdown(
        f"<div class='callout'>🔑 <b>Groq API key required.</b> "
        f"Get a free key at console.groq.com/keys, then paste it below.</div>",
        unsafe_allow_html=True)
    api_key = st.text_input("Groq API Key", type="password", label_visibility="collapsed",
                            placeholder="gsk_...")
if not api_key:
    st.stop()

# ─── GROQ CLIENT ────────────────────────────────────────────────────────
# Create the Groq "phone line" — a connection object we'll use to send prompts.
# Think of it like opening a phone app before making a call.
client = Groq(api_key=api_key)

# ─── AI SETTINGS — change models in ONE place ───────────────────────────
# Every AI call in the app goes through ask_ai() below. When Groq retires
# a model (it happened to llama-3.1-8b-instant), you edit ONE line here
# instead of hunting through five separate calls.
PRIMARY_MODEL  = "openai/gpt-oss-20b"       # reasoning model, strict JSON support
FALLBACK_MODEL = "llama-3.3-70b-versatile"  # non-reasoning backup if the primary fails


class AIError(Exception):
    """An AI failure, already rewritten as a plain-English message."""


def explain_error(err):
    # Turn raw API errors into a sentence the user can act on.
    status = getattr(err, "status_code", None)
    text = str(err)
    if status == 401:
        return "Groq rejected the API key. Check GROQ_API_KEY in your secrets."
    if status == 429:
        return "Groq's free-tier rate limit was reached. Wait a minute and try again."
    if "model_not_found" in text or "decommissioned" in text:
        return "That AI model has been retired by Groq. Update PRIMARY_MODEL in app.py."
    if "json_validate_failed" in text:
        return "The AI couldn't produce a valid answer this time. Please try again."
    return f"The AI request failed: {text[:300]}"


def ask_ai(prompt, *, temperature=0.3, max_tokens=4096, json_schema=None):
    """Send one prompt to Groq and return the reply text.

    Tries PRIMARY_MODEL first, then FALLBACK_MODEL, so one retired or
    overloaded model doesn't take the whole app down.
    """
    last_err = None
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        is_reasoning = model.startswith("openai/gpt-oss")
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            # THE BUG FIX: without this, Groq's default limit is 1,024 tokens.
            # Reasoning models spend that budget "thinking", run out before
            # writing the answer, and return an EMPTY reply — which is exactly
            # the json_validate_failed / failed_generation '' error.
            "max_completion_tokens": max_tokens,
        }
        if is_reasoning:
            kwargs["reasoning_effort"] = "low"    # think briefly, answer fully
            kwargs["include_reasoning"] = False   # we only need the answer
        if json_schema is not None:
            if is_reasoning:
                # Strict schema = constrained decoding: the model physically
                # cannot emit JSON that breaks the shape we define below.
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": "cv_audit", "strict": True,
                                    "schema": json_schema},
                }
            else:
                kwargs["response_format"] = {"type": "json_object"}
        try:
            resp = client.chat.completions.create(**kwargs)
            text = (resp.choices[0].message.content or "").strip()
            if text:
                return text
            last_err = AIError(f"{model} returned an empty reply")
        except Exception as e:
            last_err = e
    raise AIError(explain_error(last_err))


def ask_ai_or_stop(prompt, **kwargs):
    # For the free-text tools: show a friendly error and stop this run.
    try:
        return ask_ai(prompt, **kwargs)
    except AIError as e:
        st.error(f"❌ {e}")
        st.stop()


def parse_json(text):
    # Normal case: the reply is pure JSON. Fallback: cut out the outermost
    # {...} in case a model wrapped it in a sentence or code fence.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end])


# The exact shape the Résumé Auditor must return. Strict mode requires
# every field listed in "required" and no extra fields.
_STR_LIST = {"type": "array", "items": {"type": "string"}}
_RUBRIC_KEYS = ["technical_skills", "experience_relevance",
                "education_fit", "evidence_quality"]
AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "rubric": {
            "type": "object",
            "properties": {k: {"type": "integer"} for k in _RUBRIC_KEYS},
            "required": _RUBRIC_KEYS,
            "additionalProperties": False,
        },
        "verdict": {"type": "string"},
        "critical_issues": _STR_LIST,
        "warning_issues": _STR_LIST,
        "good_points": _STR_LIST,
        "ats_keywords_found": _STR_LIST,
        "ats_keywords_missing": _STR_LIST,
        "skill_coverage": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"skill": {"type": "string"},
                               "percent": {"type": "integer"}},
                "required": ["skill", "percent"],
                "additionalProperties": False,
            },
        },
        "strong_phrases": _STR_LIST,
        "weak_phrases": _STR_LIST,
        "cv_comment": {"type": "string"},
    },
    "required": ["rubric", "verdict", "critical_issues", "warning_issues",
                 "good_points", "ats_keywords_found", "ats_keywords_missing",
                 "skill_coverage", "strong_phrases", "weak_phrases", "cv_comment"],
    "additionalProperties": False,
}


# ════════════════════════════════════════════════════════════════════════
# SECTION 1: RESUME AUDITOR
# ════════════════════════════════════════════════════════════════════════

if app_mode == "📋 Resume Auditor":

    # Page header — premium hero band
    st.markdown("""
<div class="hero">
  <div class="hero-badge">AI RESUME AUDIT</div>
  <div class="hero-title">Résumé <span class="grad">Auditor</span></div>
  <div class="hero-sub">Upload your CV and a target role. Get an annotated review, a transparent match score, and ATS keyword analysis in seconds.</div>
</div>
""", unsafe_allow_html=True)

    # Two input columns side-by-side
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="panel"><p class="panel-title">📄 Step 1 — Upload Your CV</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload CV (PDF only)",
            type=["pdf"],
            label_visibility="collapsed"   # Hide label — panel title explains it
        )
        if uploaded_file:
            # Show a small green confirmation so user knows it uploaded
            st.success(f"✅ {uploaded_file.name} uploaded")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel"><p class="panel-title">🎯 Step 2 — Target Role</p>', unsafe_allow_html=True)
        job_title = st.text_input(
            "Job title",
            placeholder="e.g. Data Analyst Intern",
            label_visibility="collapsed"
        )
        job_desc = st.text_area(
            "Job description",
            placeholder="Paste the full job description here...",
            height=130,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Submit button — centered using 3 columns trick
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        run_audit = st.button("⚡ Run Resume Audit", type="primary", use_container_width=True)

    # ── PIPELINE EXECUTION ───────────────────────────────────────────────
    # Only runs when button is clicked AND all inputs are provided

    if run_audit:

        # Validate inputs before wasting an API call
        if not uploaded_file:
            st.error("❌ Please upload your CV (PDF format)")
            st.stop()
        if not job_title or not job_desc:
            st.error("❌ Please enter both the job title and description")
            st.stop()

        with st.spinner("Analysing your CV against the role..."):

            # ── STEP 1: Extract text from PDF ────────────────────────────
            # pdfplumber opens the PDF like a book.
            # We loop through each "page" and pull the text out.
            # Analogy: like photocopying each page, then reading all copies together.

            extracted_text = ""   # Start with an empty string to collect all pages

            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    # extract_text() returns the text on that page, or None if blank/scanned
                    page_text = page.extract_text()
                    if page_text:
                        # Add this page's text to our collection, with a newline separator
                        extracted_text += page_text + "\n"

            # FIX: system_prompt was INSIDE the for loop in old code — it ran per page!
            # Now it's OUTSIDE the loop (correct) — runs once after ALL pages are read.

            if not extracted_text.strip():
                # .strip() removes whitespace — if nothing is left, the PDF had no text
                st.error("❌ Could not extract text from this PDF. Try a text-based PDF (not a scanned image).")
                st.stop()

            # ── STEP 2: Build the prompt ──────────────────────────────────
            # A prompt is the instruction we send to the AI.
            # Think of it as a very detailed memo to a very smart analyst.
            # We embed the CV text and job description inside the prompt.

            system_prompt = f"""
You are an expert graduate career advisor and ATS (Applicant Tracking System) analyst.
Analyse the student CV against the job description below.

RULES:
- Return ONLY a valid JSON object. No markdown, no backticks, no explanation.
- If the job description lacks specific technical requirements, infer standard tools for '{job_title}'.
- Be honest — match_score should reflect genuine alignment, not flattery.
- Extract 3-5 real keywords from the job description for ats_keywords_found and ats_keywords_missing.

Return this exact JSON structure:
{{
  "rubric": {{
    "technical_skills":     <0-10: hard skills vs the JD's requirements>,
    "experience_relevance": <0-10: how directly past roles map to this one>,
    "education_fit":        <0-10: qualifications vs what the JD asks>,
    "evidence_quality":     <0-10: quantified, verifiable achievements>
  }},
  "verdict": "<one of: Strong Match | Good Fit | Needs Work | Poor Fit>",
  "critical_issues": ["<specific issue>", "<specific issue>"],
  "warning_issues": ["<specific issue>", "<specific issue>"],
  "good_points": ["<specific strength>", "<specific strength>"],
  "ats_keywords_found": ["<keyword in both CV and JD>"],
  "ats_keywords_missing": ["<keyword in JD but not in CV>"],
  "skill_coverage": [
    {{"skill": "<core skill from the JD>", "percent": <0-100 how well the CV evidences it>}},
    {{"skill": "<core skill>", "percent": <0-100>}},
    {{"skill": "<core skill>", "percent": <0-100>}},
    {{"skill": "<core skill>", "percent": <0-100>}}
  ],
  "strong_phrases": ["<EXACT phrase copied VERBATIM from the CV that is strong — quantified impact, relevant tools>", "<up to 6 phrases>"],
  "weak_phrases": ["<EXACT verbatim CV phrase that is weak — vague, passive, unquantified>", "<up to 6 phrases>"],
  "cv_comment": "<one-sentence overall verdict on the CV's writing quality>"
}}

PHRASE RULES (critical):
- strong_phrases / weak_phrases MUST be copied character-for-character from the CV text.
- Do NOT paraphrase, trim, or fix typos — an inexact copy cannot be highlighted.
- Each phrase 3-15 words, no overlaps between the two lists.

CV Text:
{extracted_text}

Job Title: {job_title}
Job Description:
{job_desc}
"""

            # ── STEP 3: Call Groq API ─────────────────────────────────────
            # We send our prompt to Groq and get back an AI response.
            # response_format=json_object forces Groq to only output valid JSON.
            # Analogy: like faxing a questionnaire and getting back a filled form.

            try:
                # ask_ai() handles the model choice, the token budget, strict
                # JSON and the fallback model. 8,000 tokens leaves room for a
                # long CV's worth of phrases plus the model's reasoning.
                raw_output = ask_ai(system_prompt, temperature=0.1,
                                    max_tokens=8000, json_schema=AUDIT_SCHEMA)

                # ── STEP 5: Parse JSON into a Python dictionary ───────────
                # Analogy: converting a written form into a filing cabinet.
                data = parse_json(raw_output)

                # Counts come from the lists themselves, so the badges can
                # never disagree with the tabs ("3 Critical" but 2 listed).
                data["critical_count"] = len(data.get("critical_issues", []))
                data["warning_count"]  = len(data.get("warning_issues", []))
                data["good_count"]     = len(data.get("good_points", []))

                # ── SCORE COMPUTED IN PYTHON, NOT BY THE AI ────────────
                # WHY: a single LLM-invented "78" is unexplainable and
                # varies run to run. Instead the AI only judges four
                # narrow sub-questions (0-10 each); the final score is
                # OUR transparent weighted sum — reproducible arithmetic
                # we can show the user line by line.
                # Analogy: the examiner marks four exam sections; the
                # registrar (this code) adds them up with fixed weights.
                WEIGHTS = {
                    "technical_skills":     0.40,  # matters most for grad roles
                    "experience_relevance": 0.30,
                    "education_fit":        0.15,
                    "evidence_quality":     0.15,
                }
                rubric_raw = data.get("rubric", {})
                # Clamp every sub-score into 0-10 even if the AI misbehaves
                subs = {k: max(0.0, min(10.0, float(rubric_raw.get(k, 0))))
                        for k in WEIGHTS}
                # Weighted sum of 0-10 scores → 0-100 scale
                data["match_score"] = round(
                    sum(subs[k] * WEIGHTS[k] for k in WEIGHTS) * 10)
                data["rubric_clamped"] = subs      # for the breakdown UI
                data["rubric_weights"] = WEIGHTS

                # Persist the FULL CV text so the annotated document can
                # re-render after any rerun (button clicks etc.)
                st.session_state.cv_full = extracted_text
                st.session_state.audit_data = data

            except AIError as e:
                # Already a plain-English message from explain_error()
                st.error(f"❌ {e}")
                st.stop()

            except (json.JSONDecodeError, ValueError, TypeError):
                st.error("❌ The AI's answer couldn't be read. Please run the audit again.")
                st.stop()

    # ── DISPLAY RESULTS ──────────────────────────────────────────────────
    # This runs separately from the pipeline above.
    # It checks the notepad (session_state) — if analysis data exists, show it.
    # This means results persist even after other button clicks.

    if st.session_state.audit_data:
        data = st.session_state.audit_data   # Shortcut variable

        st.divider()

        # ── Score card ──
        score   = data.get("match_score", 0)      # .get() safely retrieves value, default 0
        verdict = data.get("verdict", "")

        # Traffic-light colour for the ring fill
        if score >= 70:
            ring_color = T["green"]
        elif score >= 45:
            ring_color = T["accent"]
        else:
            ring_color = T["red"]

        # conic-gradient draws an arc from 0 to (score*3.6)deg — a real
        # progress ring. The inner disc masks the centre so only a ring shows.
        st.markdown(f"""
        <div class="score-card">
            <div class="score-ring" style="
                background:conic-gradient({ring_color} {score*3.6}deg, {T['border']} 0deg);
                color:{ring_color};">
                <div style="position:absolute;width:82px;height:82px;border-radius:50%;
                     background:{T['surface']};display:flex;align-items:center;
                     justify-content:center;">{score}</div>
            </div>
            <div>
                <div class="score-label">Overall Match Score</div>
                <div class="score-verdict">{verdict}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Score breakdown — shows the arithmetic behind the number ──
        # Turns the score from a mystery into a receipt. Each line:
        #   sub-score/10  ×  weight  =  points contributed
        with st.expander("🧮 How this score was computed", expanded=False):
            subs    = data.get("rubric_clamped", {})
            weights = data.get("rubric_weights", {})
            if subs and weights:
                nice = {"technical_skills": "Technical skills",
                        "experience_relevance": "Experience relevance",
                        "education_fit": "Education fit",
                        "evidence_quality": "Evidence quality"}
                for k, w in weights.items():
                    pts = subs[k] * w * 10          # this component's points
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"font-size:0.87rem;padding:3px 0'>"
                        f"<span>{nice.get(k, k)} — <b>{subs[k]:.0f}/10</b>"
                        f" × weight {w:.2f}</span>"
                        f"<span style='color:{ACCENT};font-weight:600'>"
                        f"+{pts:.0f} pts</span></div>",
                        unsafe_allow_html=True)
                st.markdown(
                    f"<hr style='margin:6px 0;border-color:{BORDER}'>"
                    f"<div style='display:flex;justify-content:space-between;"
                    f"font-weight:700'><span>Total</span>"
                    f"<span style='color:{ACCENT}'>{score}/100</span></div>",
                    unsafe_allow_html=True)
            st.caption("AI-estimated sub-scores, deterministic weighted sum. "
                       "Indicative, not definitive — see it as a structured "
                       "second opinion, not a verdict.")

        # ── Badge row (Critical / Warnings / Good counts) ──
        st.markdown(f"""
        <div class="badge-row">
            <div class="badge badge-red">🔴 {data.get("critical_count", 0)} Critical</div>
            <div class="badge badge-amber">🟡 {data.get("warning_count", 0)} Warnings</div>
            <div class="badge badge-green">🟢 {data.get("good_count", 0)} Strengths</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Two-column results layout ──
        res_left, res_right = st.columns(2, gap="large")

        with res_left:
            st.markdown(f"<h4 style='color:{TEXT}'>📝 Your CV — Annotated</h4>",
                        unsafe_allow_html=True)

            # ── Build the full highlighted document ────────────────────
            # 1. html.escape() the ENTIRE CV — turns <, >, & into safe
            #    text so nothing in the CV can inject markup.
            # 2. For each AI-returned phrase, escape it the SAME way,
            #    then wrap its occurrence in a coloured <span>.
            #    Both sides escaped identically → exact string match.
            # 3. white-space:pre-wrap in .cv-doc preserves line breaks.
            import html as html_lib

            cv_raw = st.session_state.get("cv_full", "")
            if cv_raw:
                doc = html_lib.escape(cv_raw)

                # Weak first, then strong — if the AI accidentally returns
                # overlapping phrases, strong (applied last) wins visually.
                for ph in data.get("weak_phrases", []):
                    ph_esc = html_lib.escape(ph)
                    if ph_esc and ph_esc in doc:
                        doc = doc.replace(
                            ph_esc,
                            f'<span class="hl-bad">{ph_esc}</span>')
                for ph in data.get("strong_phrases", []):
                    ph_esc = html_lib.escape(ph)
                    if ph_esc and ph_esc in doc:
                        doc = doc.replace(
                            ph_esc,
                            f'<span class="hl-good">{ph_esc}</span>')

                # Legend so the colours explain themselves
                st.markdown(
                    f'<span class="legend-chip" style="background:'
                    f'rgba(52,211,153,0.16);color:{GREEN};border:1px solid {GREEN}">'
                    f'■ strength</span>'
                    f'<span class="legend-chip" style="background:'
                    f'rgba(248,113,113,0.14);color:{RED};border:1px solid {RED}">'
                    f'■ needs work</span>',
                    unsafe_allow_html=True)

                # The whole CV, scrollable, with highlights baked in
                st.markdown(f'<div class="cv-doc">{doc}</div>',
                            unsafe_allow_html=True)
            else:
                st.info("Re-run the audit to load your CV text.")

            comment = data.get("cv_comment", "")
            if comment:
                st.caption(f"💡 {comment}")

            # ── ATS Keyword Scanner ──
            # Novel feature: shows which job keywords appear/are missing in the CV
            st.markdown(f"<h4 style='color:{TEXT};margin-top:1.5rem'>🔍 ATS Keyword Scanner</h4>",
                        unsafe_allow_html=True)
            st.caption("Keywords from the job description — green = found in your CV, red = missing")

            found_html   = "".join(f'<span class="kw-found">✓ {k}</span>'
                                    for k in data.get("ats_keywords_found", []))
            missing_html = "".join(f'<span class="kw-missing">✗ {k}</span>'
                                    for k in data.get("ats_keywords_missing", []))

            st.markdown(found_html + missing_html, unsafe_allow_html=True)

            # ── Skill Coverage bars ────────────────────────────────────
            # WHY IT WASN'T SHOWING: this section never existed in the
            # code — the mockup had it, the app didn't. The AI also
            # wasn't asked to return coverage data. Both fixed:
            # the schema above now requests "skill_coverage", and the
            # loop below draws one bar per skill.
            coverage = data.get("skill_coverage", [])
            if coverage:
                st.markdown(
                    f"<h4 style='color:{TEXT};margin-top:1.5rem'>📊 Skill Coverage</h4>",
                    unsafe_allow_html=True)
                st.caption("How strongly your CV evidences each core skill the role demands")

                for item in coverage:
                    skill = item.get("skill", "")
                    pct   = max(0, min(100, int(item.get("percent", 0))))  # clamp 0-100

                    # Traffic-light fill colour by strength
                    #   ≥70 green (solid) · 40-69 amber (developing) · <40 red (gap)
                    if pct >= 70:
                        fill = GREEN
                    elif pct >= 40:
                        fill = AMBER
                    else:
                        fill = RED

                    # Two-layer bar: full-width grey track + coloured fill
                    # whose width IS the percentage (width:{pct}%).
                    st.markdown(f"""
                    <div class="cov-row">
                        <div class="cov-head">
                            <span class="cov-name">{skill}</span>
                            <span class="cov-pct">{pct}%</span>
                        </div>
                        <div class="cov-track">
                            <div class="cov-fill" style="width:{pct}%;background:{fill}"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with res_right:
            st.markdown(f"<h4 style='color:{TEXT}'>🛠 Audit Findings</h4>", unsafe_allow_html=True)

            # Three tabs for different severity levels
            tab_crit, tab_warn, tab_good = st.tabs(["🔴 Critical", "🟡 Warnings", "🟢 Strengths"])

            with tab_crit:
                issues = data.get("critical_issues", [])
                if issues:
                    for issue in issues:
                        st.markdown(f"• {issue}")
                else:
                    st.success("No critical issues found!")

            with tab_warn:
                warnings = data.get("warning_issues", [])
                if warnings:
                    for w in warnings:
                        st.markdown(f"• {w}")
                else:
                    st.success("No warnings!")

            with tab_good:
                goods = data.get("good_points", [])
                if goods:
                    for g in goods:
                        st.markdown(f"• {g}")
                else:
                    st.info("Run an audit to see your strengths.")


# ════════════════════════════════════════════════════════════════════════
# SECTION 2: PROJECT ARCHITECT
# ════════════════════════════════════════════════════════════════════════

elif app_mode == "🛠 Project Architect":

    st.markdown("""
<div class="hero">
  <div class="hero-badge">CLOSE YOUR GAPS</div>
  <div class="hero-title">Project <span class="grad">Architect</span></div>
  <div class="hero-sub">Turn every skill gap into a build-this-weekend GitHub project blueprint — framed as a real business problem, not a tutorial.</div>
</div>
""", unsafe_allow_html=True)
    st.divider()

    # Guard: must run Resume Auditor first to have gaps to fix
    if not st.session_state.audit_data:
        st.markdown(
            f"<div class='callout'>⚠️ Run a <b>Resume Audit</b> first to identify your gaps.<br>"
            f"The Project Architect turns those gaps into buildable projects.</div>",
            unsafe_allow_html=True
        )

    else:
        # Show what gaps we're building projects for
        gaps = st.session_state.audit_data.get("critical_issues", [])

        st.markdown(f"<h4 style='color:{TEXT}'>📋 Gaps being addressed:</h4>", unsafe_allow_html=True)
        for g in gaps:
            st.markdown(f"• {g}")

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            # Let user customise what kind of project they want
            project_type = st.selectbox(
                "Project type",
                ["Web App", "Data Analysis", "Machine Learning", "API / Backend", "Automation Script"]
            )
        with col_b:
            timeline = st.selectbox("Build timeline", ["Weekend (2 days)", "1 Week", "2 Weeks"])

        if st.button("⚡ Generate Project Blueprint", type="primary", use_container_width=True):
            with st.spinner("Engineering your project blueprint..."):

                architect_prompt = f"""
You are a senior software engineer mentoring a student.
Their CV audit identified these skill gaps: {gaps}
They want to build a '{project_type}' project in '{timeline}'.

Generate a professional GitHub README.md blueprint in raw Markdown.
Include:
1. A professional project title (framed as a BUSINESS problem, not a learning exercise)
2. The business problem it solves (1 paragraph)
3. Tech stack (as a bullet list with reasons for each choice)
4. ASCII directory tree of the repo structure
5. Step-by-step development checklist (10 steps maximum)
6. How this project closes the identified skill gaps (link each gap to a section)

Do NOT include pleasantries. Output raw Markdown only.
"""

                blueprint_text = ask_ai_or_stop(architect_prompt, temperature=0.3,
                                                max_tokens=6000)

            st.subheader("Your GitHub README Blueprint")
            # text_area so the user can copy the Markdown easily
            st.text_area("Copy this into your GitHub repo README.md", value=blueprint_text, height=450)
            st.success("✅ Copy the blueprint above, create a GitHub repo, and start building!")


# ════════════════════════════════════════════════════════════════════════
# SECTION 3: INTERVIEW COACH
# ════════════════════════════════════════════════════════════════════════

elif app_mode == "💬 Interview Coach":

    st.markdown("""
<div class="hero">
  <div class="hero-badge">PRACTICE & PROVE</div>
  <div class="hero-title">Interview <span class="grad">Coach</span></div>
  <div class="hero-sub">Rehearse role-specific behavioural questions and get instant AI feedback on live Python code challenges.</div>
</div>
""", unsafe_allow_html=True)
    st.divider()

    # Two modes: question generation OR code practice
    coach_mode = st.radio(
        "Choose practice mode",
        ["🎤 Behavioural Questions", "💻 Code Challenge"],
        horizontal=True    # Show side-by-side, not stacked
    )
    st.divider()

    if coach_mode == "🎤 Behavioural Questions":

        if not st.session_state.audit_data:
            st.markdown(
                f"<div class='callout'>Run a Resume Audit first — I'll generate questions "
                f"targeting YOUR specific gaps.</div>",
                unsafe_allow_html=True
            )
        else:
            gaps    = st.session_state.audit_data.get("critical_issues", [])
            verdict = st.session_state.audit_data.get("verdict", "")

            # Generate targeted interview questions based on the audit gaps
            if st.button("⚡ Generate Interview Questions", type="primary"):
                with st.spinner("Preparing questions targeting your gaps..."):

                    interview_prompt = f"""
You are an experienced graduate recruiter at a top firm.
The candidate's profile verdict was: '{verdict}'
Their critical gaps are: {gaps}

Generate exactly 5 interview questions that specifically probe these gaps.
For each question, include:
- The question itself
- What it is testing (the gap it probes)
- A model answer structure (2-3 sentences, STAR format guidance)

Format as a numbered list. Be direct and realistic — these should feel like real interview questions.
"""

                    questions_text = ask_ai_or_stop(interview_prompt, temperature=0.4,
                                                    max_tokens=4096)

                st.markdown(questions_text)

    elif coach_mode == "💻 Code Challenge":

        st.markdown(
            f"<p style='color:{MUTED}'>Write Python code to solve the challenge below, "
            f"then submit for AI feedback.</p>",
            unsafe_allow_html=True
        )

        # Challenge selector
        challenge = st.selectbox("Select a challenge", [
            "Remove duplicates from a list while maintaining order",
            "Flatten a nested list",
            "Find the most common element in a list",
            "Check if a string is a palindrome",
            "Write a function to perform a binary search"
        ])

        # Code editor
        student_code = st.text_area(
            "Your Python solution",
            value=f"def solution():\n    # Solve: {challenge}\n    pass",
            height=180
        )

        if st.button("⚡ Evaluate My Code", type="primary"):
            with st.spinner("Evaluating your code..."):

                eval_prompt = f"""
You are a senior Python engineer reviewing a junior developer's code submission.
Challenge: '{challenge}'
Submitted code:
{student_code}

Provide:
1. Correctness verdict (does it solve the challenge? yes/no/partial)
2. Time complexity (Big O notation with a plain English explanation)
3. Space complexity (Big O)
4. Two specific improvements (code quality, edge cases, or efficiency)
5. An optimised solution with inline comments

Be concise and direct. Format with clear headings.
"""

                feedback = ask_ai_or_stop(eval_prompt, temperature=0.1,
                                          max_tokens=4096)

            st.subheader("🏁 Code Review Feedback")
            st.markdown(feedback)


# ════════════════════════════════════════════════════════════════════════
# SECTION 4: LEARNING PATH (Novel Feature)
# ════════════════════════════════════════════════════════════════════════

elif app_mode == "📚 Learning Path":

    st.markdown("""
<div class="hero">
  <div class="hero-badge">YOUR 4-WEEK PLAN</div>
  <div class="hero-title">Learning <span class="grad">Path</span></div>
  <div class="hero-sub">A week-by-week study plan built from your gaps and your real availability — using only free resources.</div>
</div>
""", unsafe_allow_html=True)
    st.divider()

    if not st.session_state.audit_data:
        st.markdown(
            f"<div class='callout'>Run a <b>Resume Audit</b> first — I'll build a "
            f"personalised learning plan from your gaps.</div>",
            unsafe_allow_html=True
        )
    else:
        gaps = st.session_state.audit_data.get("critical_issues", [])
        missing_keywords = st.session_state.audit_data.get("ats_keywords_missing", [])

        all_gaps = list(set(gaps + missing_keywords))   # Combine, remove duplicates

        col1, col2 = st.columns(2)
        with col1:
            weeks = st.slider("Study plan length (weeks)", 1, 8, 4)
        with col2:
            hours = st.slider("Hours available per week", 2, 20, 8)

        if st.button("⚡ Generate My Learning Plan", type="primary"):
            with st.spinner("Building your personalised study plan..."):

                plan_prompt = f"""
You are a career coach building a practical study plan for a graduate.
Their skill gaps are: {all_gaps}
Available time: {hours} hours per week for {weeks} weeks.

Build a week-by-week plan that:
1. Prioritises the most impactful gaps first
2. Recommends ONLY free resources (YouTube, freeCodeCamp, Kaggle, official docs, Coursera audit)
3. Includes one small hands-on project per gap to prove the skill
4. Is realistic for the time available

Format as a Markdown table with columns: Week | Focus Skill | Resource | Hours | Mini-Project
Then add a 'What success looks like' section at the end.
"""

                plan_text = ask_ai_or_stop(plan_prompt, temperature=0.3,
                                           max_tokens=6000)

            st.markdown(plan_text)
