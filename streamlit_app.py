import datetime
import html
import os
import re

import requests
import streamlit as st

# Backend endpoint: env var (local / Render) > Streamlit secrets (Streamlit Cloud) > localhost
def _backend_url() -> str:
    url = os.getenv("BACKEND_URL")
    if not url:
        try:
            url = st.secrets.get("BACKEND_URL")
        except Exception:
            url = None
    return (url or "http://localhost:8001").rstrip("/")


BASE_URL = _backend_url()
REQUEST_TIMEOUT = 300  # agent runs make many tool calls; give them room

STYLES = ["Relaxed", "Packed days", "Food-first", "Budget", "Luxury", "Outdoors", "Culture", "Nightlife"]
EXAMPLES = [
    {"label": "Goa, 5 days, ₹40,000", "dest": "Goa", "origin": "Mumbai", "days": 5, "budget": 40000, "styles": ["Relaxed", "Food-first"]},
    {"label": "Jaipur, 3 days, ₹25,000", "dest": "Jaipur", "origin": "Delhi", "days": 3, "budget": 25000, "styles": ["Culture"]},
    {"label": "Kyoto, 7 days, ₹2,50,000", "dest": "Kyoto", "origin": "Bengaluru", "days": 7, "budget": 250000, "styles": ["Culture", "Food-first"]},
]

st.set_page_config(
    page_title="Trip Planner",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="auto",
)

# ---------------------------------------------------------------- styles
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Public+Sans:wght@400;500;600;700&display=swap');

:root {
  --paper: #F3F6F8;
  --ink: #17233F;
  --marigold: #F2A413;
  --marigold-deep: #D68C00;
  --teal: #116A6B;
  --fog: #5D6B82;
  --line: #D3DCE5;
  --card: #FFFFFF;
  --display: 'Bricolage Grotesque', 'Public Sans', sans-serif;
}

.stApp { background: var(--paper); color: var(--ink); }
.block-container { max-width: 900px; padding-top: 2.5rem; padding-bottom: 5rem; }
html, body, .stApp, .stMarkdown, input, textarea, button { font-family: 'Public Sans', sans-serif; }

/* ---------- masthead ---------- */
.tp-mark { font-family: var(--display); font-weight: 600; font-size: 1rem; color: var(--fog); margin: 0 0 2.25rem; }
.tp-mark b { color: var(--ink); font-weight: 800; }
.tp-title {
  font-family: var(--display); font-weight: 800; color: var(--ink);
  font-size: clamp(2.6rem, 7vw, 4.4rem); line-height: .95; letter-spacing: -0.035em;
  margin: 0 0 1rem; font-variation-settings: "opsz" 96;
}
.tp-lede { font-size: 1.075rem; line-height: 1.55; color: var(--fog); max-width: 54ch; margin: 0 0 2rem; }

/* ---------- the ticket ---------- */
.st-key-ticket {
  background: var(--card); border: 1px solid var(--line); border-radius: 20px;
  padding: 1.5rem 1.5rem 1.25rem; box-shadow: 0 1px 0 var(--line), 0 18px 40px -28px rgba(23,35,63,.35);
}
.st-key-ticket label p { font-weight: 600; font-size: .9rem; color: var(--ink); }
/* let the stub column stretch to the height of the form column */
.st-key-stub, .st-key-stub [data-testid="stElementContainer"],
.st-key-stub [data-testid="stMarkdown"], .st-key-stub [data-testid="stMarkdownContainer"] { height: 100%; }
.st-key-stub [data-testid="stMarkdown"] > div { height: 100%; }
.st-key-stub [data-testid="stMarkdownContainer"] { width: 100%; }

.tp-stub {
  position: relative; background: var(--marigold); color: var(--ink); border-radius: 14px;
  padding: 1.25rem 1.1rem 1.1rem; min-height: 100%; height: 100%;
  border-left: 2px dashed rgba(23,35,63,.35);
}
.tp-stub::before, .tp-stub::after {
  content: ""; position: absolute; left: -12px; width: 22px; height: 22px; border-radius: 50%;
  background: var(--card);
}
.tp-stub::before { top: -11px; } .tp-stub::after { bottom: -11px; }
.tp-route {
  font-family: var(--display); font-weight: 800; letter-spacing: -0.02em;
  font-size: 2.5rem; line-height: 1; display: flex; align-items: center; gap: .35rem; flex-wrap: wrap;
}
.tp-route .tp-from { opacity: .45; font-size: 1.4rem; }
.tp-route .tp-plane { font-size: 1.1rem; opacity: .6; }
.tp-dest { font-weight: 600; margin: .4rem 0 1.1rem; font-size: .95rem; overflow-wrap: anywhere; }
.tp-stub dl { display: grid; grid-template-columns: auto 1fr; gap: .35rem .8rem; margin: 0; font-size: .9rem; }
.tp-stub dt { opacity: .7; }
.tp-stub dd { margin: 0; font-weight: 700; font-variant-numeric: tabular-nums; }
.tp-stub .tp-empty { opacity: .7; font-weight: 500; }

/* ---------- buttons ---------- */
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background: var(--marigold); color: var(--ink); border: 0; font-weight: 700;
  font-size: 1rem; padding: .7rem 1.4rem; border-radius: 12px;
}
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
  background: var(--marigold-deep); color: var(--ink);
}
.stButton button[kind="primary"]:disabled { background: #EDE3CF; color: #8C8574; }
button:focus-visible, input:focus-visible, textarea:focus-visible {
  outline: 3px solid var(--teal) !important; outline-offset: 2px;
}

/* example chips under the ticket */
.st-key-examples .stButton button {
  background: transparent; border: 1px solid var(--line); color: var(--ink);
  border-radius: 999px; font-size: .9rem; padding: .3rem .9rem;
}
.st-key-examples .stButton button:hover { border-color: var(--teal); color: var(--teal); }
.tp-hint { color: var(--fog); font-size: .95rem; margin: 2.25rem 0 .6rem; }

/* ---------- the plan ---------- */
.st-key-plan {
  background: var(--card); border: 1px solid var(--line); border-radius: 20px;
  padding: 2rem clamp(1.1rem, 4vw, 2.75rem) 2.25rem; margin-top: 2.5rem;
}
.st-key-plan .stMarkdown { max-width: 68ch; }
.st-key-plan p, .st-key-plan li { font-size: 1.02rem; line-height: 1.65; }
.st-key-plan h1 {
  font-family: var(--display); font-weight: 800; letter-spacing: -0.03em;
  font-size: clamp(2rem, 5vw, 2.8rem); line-height: 1.02; padding: 0 0 .5rem;
}
.st-key-plan h2 {
  font-family: var(--display); font-weight: 700; font-size: 1.45rem; letter-spacing: -0.01em;
  border-top: 1px solid var(--line); padding-top: 1.6rem; margin-top: 1.6rem;
}
.st-key-plan h3 {
  font-family: var(--display); font-weight: 700; font-size: 1.2rem;
  display: inline-block; background: #FCEBC6; padding: .15rem .6rem; border-radius: 8px; margin-top: 1.4rem;
}
.st-key-plan h4 { font-size: 1.02rem; font-weight: 700; margin-top: 1rem; padding-bottom: .1rem; }
.st-key-plan a { color: var(--teal); text-decoration-thickness: 1px; text-underline-offset: 3px; }
.st-key-plan a:hover { text-decoration-thickness: 2px; }
.st-key-plan strong { font-weight: 700; }
.st-key-plan hr { border-color: var(--line); }
.tp-meta { color: var(--fog); font-size: .9rem; margin: 0 0 .25rem; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: #E9EFF3; }
[data-testid="stSidebar"] h3 { font-family: var(--display); font-weight: 700; letter-spacing: -0.01em; }
.tp-status { font-size: .88rem; color: var(--fog); display: flex; align-items: center; gap: .45rem; }
.tp-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.st-key-history .stButton button {
  justify-content: flex-start; text-align: left; background: transparent; border: 1px solid transparent; width: 100%;
}
.st-key-history .stButton button:hover { border-color: var(--line); background: #fff; }

@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("plans", [])        # list of dicts, newest last
ss.setdefault("active", None)     # index into plans
ss.setdefault("error", None)
for key, default in {"dest": "", "origin": "", "days": 4, "budget": 0, "styles": [], "notes": ""}.items():
    ss.setdefault(key, default)


def use_example(ex: dict):
    ss.dest, ss.origin, ss.days, ss.budget, ss.styles, ss.notes = (
        ex["dest"], ex["origin"], ex["days"], ex["budget"], ex["styles"], "")


def city_code(name: str) -> str:
    letters = re.sub(r"[^A-Za-z]", "", name)
    return letters[:3].upper() if letters else "???"


def inr(n: int) -> str:
    """Indian digit grouping: 250000 -> 2,50,000."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d{2})+$)", r"\1,", head)
    return f"{head},{tail}"


def build_question(dest, origin, days, budget, styles, notes) -> str:
    q = f"Plan a {days}-day trip to {dest}"
    if origin:
        q += f", starting from {origin}"
    if budget:
        q += f", with a total budget of about ₹{inr(budget)} for the whole trip"
    q += "."
    if styles:
        q += f" Travel style: {', '.join(styles).lower()}."
    if notes.strip():
        q += f" Also: {notes.strip()}"
    return q


@st.cache_data(ttl=20, show_spinner=False)
def backend_online(url: str) -> bool:
    try:
        return requests.get(f"{url}/health", timeout=2).ok
    except requests.RequestException:
        return False


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    online = backend_online(BASE_URL)
    colour = "#1E9E6A" if online else "#C0392B"
    status = "Planner is online" if online else "Planner is offline"
    st.markdown(
        f'<div class="tp-status"><span class="tp-dot" style="background:{colour}"></span>{status}</div>',
        unsafe_allow_html=True,
    )
    if not online:
        st.caption(f"Start the backend with `python main.py`. Looking for it at {BASE_URL}.")

    st.markdown("### Your plans")
    if not ss.plans:
        st.caption("Plans you make in this session show up here.")
    else:
        with st.container(key="history"):
            for i in reversed(range(len(ss.plans))):
                p = ss.plans[i]
                marker = "● " if i == ss.active else ""
                if st.button(f"{marker}{p['dest']}, {p['days']} days", key=f"hist_{i}", help=p["made"]):
                    ss.active = i
                    st.rerun()

# ---------------------------------------------------------------- hero
st.markdown('<p class="tp-mark"><b>Trip Planner</b></p>', unsafe_allow_html=True)
st.markdown('<h1 class="tp-title">Where are you headed?</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="tp-lede">Give a place, a number of days and a budget. The planner checks live '
    "weather, exchange rates and local spots, then writes a day-by-day plan with costs in rupees.</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- ticket
with st.container(key="ticket"):
    left, right = st.columns([2.1, 1], gap="medium")
    with left:
        c1, c2 = st.columns(2)
        c1.text_input("Going to", key="dest", placeholder="Goa")
        c2.text_input("Leaving from", key="origin", placeholder="Optional, e.g. Mumbai")
        c3, c4 = st.columns(2)
        c3.number_input("Days", key="days", min_value=1, max_value=21, step=1)
        c4.number_input("Total budget (₹)", key="budget", min_value=0, step=5000,
                        help="Leave at 0 if you're flexible.")
        st.pills("Travel style", STYLES, key="styles", selection_mode="multi")
        st.text_area("Anything else?", key="notes", height=80,
                     placeholder="Travelling with kids, vegetarian, want one beach day…")

    dest, origin = ss.dest.strip(), ss.origin.strip()
    with right.container(key="stub", height="stretch"):
        frm = f'<span class="tp-from">{city_code(origin)}</span><span class="tp-plane">✈</span>' if origin else ""
        budget_txt = f"₹{inr(ss.budget)}" if ss.budget else '<span class="tp-empty">Flexible</span>'
        style_txt = html.escape(", ".join(ss.styles)) if ss.styles else '<span class="tp-empty">Any</span>'
        st.markdown(
            f"""<div class="tp-stub" aria-label="Trip summary">
  <div class="tp-route">{frm}<span>{city_code(dest) if dest else "———"}</span></div>
  <div class="tp-dest">{html.escape(dest) if dest else "Pick a destination"}</div>
  <dl>
    <dt>Days</dt><dd>{ss.days}</dd>
    <dt>Budget</dt><dd>{budget_txt}</dd>
    <dt>Style</dt><dd>{style_txt}</dd>
  </dl>
</div>""",
            unsafe_allow_html=True,
        )

    go = st.button("Plan my trip", type="primary", disabled=not dest, use_container_width=False)

# ---------------------------------------------------------------- run
if go and dest:
    ss.error = None
    question = build_question(dest, origin, ss.days, ss.budget, ss.styles, ss.notes)
    try:
        with st.spinner(f"Checking weather, rates and places for {dest}. This usually takes under a minute."):
            resp = requests.post(f"{BASE_URL}/query", json={"question": question}, timeout=REQUEST_TIMEOUT)
        if resp.ok:
            answer = resp.json().get("answer") or ""
            if not answer.strip():
                ss.error = "The planner returned an empty plan. Try again, or add more detail to your request."
            else:
                ss.plans.append({
                    "dest": dest, "days": ss.days, "question": question, "answer": answer,
                    "made": datetime.datetime.now().strftime("%d %b, %H:%M"),
                })
                ss.active = len(ss.plans) - 1
                st.rerun()  # redraw so the sidebar history includes the new plan
        else:
            try:
                detail = resp.json().get("error", resp.text)
            except ValueError:
                detail = resp.text
            ss.error = f"The planner returned an error (HTTP {resp.status_code}): {detail}"
    except requests.Timeout:
        ss.error = f"The planner took longer than {REQUEST_TIMEOUT // 60} minutes. Try a shorter trip or try again."
    except requests.ConnectionError:
        ss.error = f"Can't reach the planner at {BASE_URL}. Start the backend with `python main.py`, then try again."
    except requests.RequestException as e:
        ss.error = f"The request failed: {e}"

if ss.error:
    st.error(ss.error)

# ---------------------------------------------------------------- output
if ss.active is not None and ss.active < len(ss.plans):
    plan = ss.plans[ss.active]
    with st.container(key="plan"):
        st.markdown(f'<p class="tp-meta">Planned {html.escape(plan["made"])}</p>', unsafe_allow_html=True)
        st.markdown(plan["answer"])
        st.divider()
        slug = re.sub(r"[^a-z0-9]+", "-", plan["dest"].lower()).strip("-") or "trip"
        st.download_button(
            "Download plan (.md)",
            data=plan["answer"],
            file_name=f"{slug}-{plan['days']}-days.md",
            mime="text/markdown",
        )
        st.caption("AI-generated. Check prices, opening hours and visa rules before you book.")
else:
    st.markdown('<p class="tp-hint">Not sure yet? Start from one of these.</p>', unsafe_allow_html=True)
    with st.container(key="examples", horizontal=True):
        for i, ex in enumerate(EXAMPLES):
            st.button(ex["label"], key=f"ex_{i}", on_click=use_example, args=(ex,))
