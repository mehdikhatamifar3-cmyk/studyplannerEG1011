import json
from pathlib import Path

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# App setup and data
# -----------------------------------------------------------------------------
BASE = Path(__file__).parent
DATA = BASE / "data"

st.set_page_config(
    page_title="EG1011 Study Navigator",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


topics = load_json("topics.json")
activities = load_json("study_activities.json")
by_topic = {topic["id"]: topic for topic in topics}
activity_map = {activity["id"]: activity for activity in activities}

# -----------------------------------------------------------------------------
# Professional visual system
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #102F46;
    --navy-2: #174A68;
    --teal: #0E8C8C;
    --teal-soft: #E8F7F6;
    --blue-soft: #EAF3F8;
    --gold: #F2B84B;
    --gold-soft: #FFF7E7;
    --green: #238B68;
    --green-soft: #ECF8F3;
    --red: #C65353;
    --red-soft: #FFF1F1;
    --ink: #172B3A;
    --muted: #607482;
    --line: #DCE7EC;
    --surface: #FFFFFF;
    --page: #F5F8FA;
}

html, body, [class*="css"] {font-family: "Inter", sans-serif;}
.stApp {background: var(--page); color: var(--ink);}
.block-container {max-width: 1240px; padding-top: 1.35rem; padding-bottom: 4rem;}

/* Sidebar */
section[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid var(--line);}
section[data-testid="stSidebar"] .block-container {padding-top: 1.3rem;}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {color: var(--navy);}
section[data-testid="stSidebar"] label {font-weight: 600; color: #304B5C;}
section[data-testid="stSidebar"] hr {border-color: var(--line);}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(125deg, #0D2F47 0%, #145B76 58%, #0E8C8C 100%);
    color: white;
    border-radius: 24px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.15rem;
    box-shadow: 0 18px 44px rgba(16,47,70,.18);
}
.hero:after {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    border: 42px solid rgba(255,255,255,.08);
    border-radius: 50%;
    right: -80px;
    top: -105px;
}
.hero-kicker {font-size: .76rem; letter-spacing: .13em; font-weight: 800; opacity: .8; text-transform: uppercase;}
.hero h1 {font-size: 2.25rem; line-height: 1.12; margin: .35rem 0 .55rem; color: white;}
.hero p {max-width: 760px; font-size: 1rem; line-height: 1.65; margin: 0; opacity: .94;}

/* Cards and summaries */
.section-title {font-size: 1.28rem; font-weight: 800; color: var(--navy); margin: .25rem 0 .2rem;}
.section-intro {color: var(--muted); margin-bottom: 1rem;}
.metric-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 17px;
    padding: .95rem 1rem;
    min-height: 100px;
    box-shadow: 0 5px 16px rgba(16,47,70,.045);
}
.metric-label {font-size: .74rem; font-weight: 700; letter-spacing: .055em; text-transform: uppercase; color: var(--muted);}
.metric-value {margin-top: .28rem; font-size: 1.38rem; line-height: 1.25; font-weight: 800; color: var(--navy);}
.metric-sub {font-size: .76rem; color: var(--muted); margin-top: .25rem;}

.topic-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 1.25rem 1.35rem;
    margin: 1rem 0;
    box-shadow: 0 7px 22px rgba(16,47,70,.055);
}
.topic-card h2 {color: var(--navy); margin: .1rem 0 .35rem; font-size: 1.55rem;}
.topic-card p {color: #415B6B; line-height: 1.62; margin-bottom: .7rem;}
.chip {display: inline-block; margin: .18rem .3rem .05rem 0; padding: .33rem .68rem; border-radius: 999px; background: var(--teal-soft); color: #0B6767; font-size: .78rem; font-weight: 700;}

.notice {border-radius: 16px; padding: .95rem 1rem; margin: .75rem 0; border: 1px solid;}
.notice-title {font-weight: 800; margin-bottom: .18rem;}
.notice-text {font-size: .89rem; line-height: 1.5;}
.notice-warning {background: var(--red-soft); border-color: #F0CCCC; color: #743333;}
.notice-ready {background: var(--green-soft); border-color: #C8E9DC; color: #185F48;}
.notice-info {background: var(--blue-soft); border-color: #C9DEEA; color: #244F65;}

.next-card {
    display: grid;
    grid-template-columns: 64px 1fr auto;
    gap: 1rem;
    align-items: center;
    background: linear-gradient(100deg, #FFF8E8 0%, #FFFFFF 65%);
    border: 1px solid #F0D89D;
    border-left: 7px solid var(--gold);
    border-radius: 18px;
    padding: 1rem 1.15rem;
    margin: 1rem 0 1.15rem;
    box-shadow: 0 6px 18px rgba(122,90,25,.06);
}
.next-number {width: 54px; height: 54px; border-radius: 15px; display:flex; align-items:center; justify-content:center; background:#FFFFFF; color:#A56D00; font-size:1.35rem; font-weight:800; box-shadow:0 4px 12px rgba(122,90,25,.10);}
.next-label {font-size: .72rem; letter-spacing: .08em; font-weight: 800; text-transform: uppercase; color: #9B6B10;}
.next-title {font-size: 1.18rem; font-weight: 800; color: var(--navy); margin: .12rem 0 .2rem;}
.next-copy {font-size:.88rem; color:#536875; line-height:1.45;}
.time-badge {text-align:center; min-width:82px; background:#FFFFFF; border:1px solid #ECD9A7; border-radius:14px; padding:.65rem .75rem;}
.time-value {font-size:1.1rem; font-weight:800; color:var(--navy);}
.time-label {font-size:.7rem; color:var(--muted);}

/* Activity cards */
.activity-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin: .6rem 0;
    box-shadow: 0 5px 16px rgba(16,47,70,.04);
}
.activity-head {display:flex; align-items:flex-start; gap:.8rem;}
.activity-order {flex:0 0 38px; width:38px; height:38px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:var(--navy); color:white; font-weight:800;}
.activity-name {font-size:1.02rem; font-weight:800; color:var(--navy); margin:.02rem 0 .12rem;}
.activity-guidance {font-size:.88rem; line-height:1.52; color:#526A78; margin-top:.48rem;}
.tag-row {margin-top:.55rem;}
.tag {display:inline-block; margin:0 .3rem .18rem 0; padding:.24rem .55rem; border-radius:7px; font-size:.7rem; font-weight:700;}
.tag-core {background:#E8F2F8;color:#215A76}.tag-support {background:var(--teal-soft);color:#116B6B}.tag-difficulty {background:#F0F2F4;color:#53626C}.tag-time {background:var(--gold-soft);color:#845D0A}

.pathway {display:flex; align-items:center; flex-wrap:wrap; gap:.45rem; margin:.8rem 0 1rem;}
.path-step {background:#FFFFFF; border:1px solid var(--line); border-radius:12px; padding:.52rem .7rem; color:var(--navy); font-size:.78rem; font-weight:700;}
.path-arrow {color:#8DA0AA; font-weight:800;}

/* Streamlit controls */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {border-radius: 11px;}
.stButton > button, .stDownloadButton > button {border-radius: 12px; font-weight: 700; min-height: 2.65rem;}
.stDownloadButton > button {background: var(--navy); color: white; border: none;}
.stDownloadButton > button:hover {background: var(--navy-2); color: white; border: none;}
.stTabs [data-baseweb="tab-list"] {gap:.35rem; background:#EAF0F3; padding:.3rem; border-radius:14px;}
.stTabs [data-baseweb="tab"] {height:2.75rem; border-radius:10px; padding:0 1rem; font-weight:700;}
.stTabs [aria-selected="true"] {background:#FFFFFF; color:var(--navy); box-shadow:0 3px 10px rgba(16,47,70,.08);}
hr {border-color: var(--line);}

.mobile-note {color:var(--muted); font-size:.78rem; text-align:center; margin-top:1.5rem;}

@media (max-width: 800px) {
    .block-container {padding: .8rem .8rem 3rem;}
    .hero {padding:1.45rem 1.25rem; border-radius:18px;}
    .hero h1 {font-size:1.75rem;}
    .next-card {grid-template-columns:48px 1fr;}
    .time-badge {grid-column:2; justify-self:start;}
    .metric-card {min-height:88px;}
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Planning logic
# -----------------------------------------------------------------------------
STAR = {
    5: "★★★★★ Core practice",
    4: "★★★★☆ Important practice",
    3: "★★★☆☆ Supporting learning",
    2: "★★☆☆☆ Optional support",
    1: "★☆☆☆☆ Extension",
}


def topic_name(topic_id):
    return by_topic.get(topic_id, {}).get("title", topic_id)


def adjusted_importance(item, confidence, goal):
    importance = item["importance"]
    if confidence == "Low" and item["type"] in [
        "Step by Step with Mehdi",
        "Interactive app",
        "Solutions in Action with Mehdi",
    ]:
        importance = min(4, importance + 1)
    if goal == "Prepare for lecture" and item["type"] == "QuickGuide":
        importance = min(5, importance + 1)
    if goal == "Prepare for tutorial" and item["type"] == "T questions":
        importance = 5
    if goal == "Quiz or exam revision" and item["type"] in [
        "Lecture examples",
        "T questions",
        "H questions",
    ]:
        importance = 5
    return importance


def ordered_activity_ids(topic):
    preferred = ["LN", "T", "H", "SBS", "APP", "SIA", "QG", "EXIT"]
    listed = list(topic.get("activities", []))
    if "SIA" in activity_map and "SIA" not in listed:
        listed.append("SIA")
    return [item for item in preferred if item in listed and item in activity_map]


def build_plan(topic, confidence, goal, minutes, completed):
    missing = [item for item in topic["required"] if item not in completed]
    plan = []
    remaining = minutes

    if missing:
        review_time = min(15, max(6, round(minutes * 0.18)))
        plan.append(
            {
                "title": "Targeted prerequisite review",
                "type": "Review",
                "importance": 5,
                "difficulty": "Foundation",
                "minutes": review_time,
                "minimum_minutes": review_time,
                "guidance": "Review: " + ", ".join(topic_name(item) for item in missing),
            }
        )
        remaining -= review_time

    for activity_id in ordered_activity_ids(topic):
        item = activity_map[activity_id].copy()
        item["importance"] = adjusted_importance(item, confidence, goal)
        minimum = item.get("minimum_minutes", item["minutes"])
        if remaining >= minimum:
            item["minutes"] = min(item["minutes"], remaining)
            plan.append(item)
            remaining -= item["minutes"]

    return plan, missing, remaining


def importance_class(importance):
    return "tag-core" if importance >= 4 else "tag-support"


# -----------------------------------------------------------------------------
# Sidebar controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 Plan your study")
    st.caption("Choose the topic and the time available. The app will create an ordered, realistic plan.")

    area = st.segmented_control(
        "Subject area",
        ["Statics", "Dynamics"],
        default="Statics",
        selection_mode="single",
    )
    if not area:
        area = "Statics"

    choices = [topic for topic in topics if topic["area"] == area]
    chosen_title = st.selectbox("Current topic", [topic["title"] for topic in choices])
    selected_topic = next(topic for topic in choices if topic["title"] == chosen_title)

    goal = st.selectbox(
        "Study goal",
        [
            "Prepare for lecture",
            "Prepare for tutorial",
            "Independent study",
            "Quiz or exam revision",
            "Catch up after missing classes",
            "Review a difficult topic",
        ],
    )
    confidence = st.segmented_control(
        "Current confidence",
        ["Low", "Medium", "High"],
        default="Medium",
        selection_mode="single",
    )
    if not confidence:
        confidence = "Medium"

    minutes = st.select_slider(
        "Available study time",
        options=[15, 30, 45, 60, 90, 120],
        value=60,
        format_func=lambda value: f"{value} min",
    )

    st.divider()
    st.markdown("#### Previous knowledge")
    st.caption("Tick only topics you can solve with reasonable confidence.")

    completed = []
    eligible = [
        topic
        for topic in choices
        if topic["id"] != selected_topic["id"]
        and topic["session"] <= selected_topic["session"]
    ]
    if eligible:
        for topic in eligible:
            if st.checkbox(topic["title"], key="done_" + topic["id"]):
                completed.append(topic["id"])
    else:
        st.caption("No earlier topics in this study sequence.")

# -----------------------------------------------------------------------------
# Main header and overview
# -----------------------------------------------------------------------------
plan, missing, unused = build_plan(
    selected_topic, confidence, goal, minutes, completed
)
planned_minutes = sum(item["minutes"] for item in plan)

st.markdown(
    """
<div class="hero">
  <div class="hero-kicker">EG1011 • Statics and Dynamics</div>
  <h1>Study Navigator</h1>
  <p>A clear study pathway that prioritises solving important examples and questions, while using supporting resources only where they improve understanding.</p>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
metrics = [
    (m1, "Current focus", selected_topic["title"], f"{area} • Session {selected_topic['session']}"),
    (m2, "Study goal", goal, confidence + " confidence"),
    (m3, "Planned time", f"{planned_minutes} minutes", f"{len(plan)} focused activities"),
    (m4, "Prerequisite status", "Review needed" if missing else "Ready to begin", f"{len(missing)} topic(s) flagged" if missing else "No required gaps selected"),
]
for column, label, value, sub in metrics:
    with column:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    f"""
<div class="topic-card">
  <div class="metric-label">Your selected topic</div>
  <h2>{selected_topic['title']}</h2>
  <p>{selected_topic['description']}</p>
  {''.join(f'<span class="chip">{outcome}</span>' for outcome in selected_topic['outcomes'])}
</div>
""",
    unsafe_allow_html=True,
)

if missing:
    st.markdown(
        f"""
<div class="notice notice-warning">
  <div class="notice-title">Prerequisite review recommended</div>
  <div class="notice-text">Before starting the main topic, briefly review <b>{', '.join(topic_name(item) for item in missing)}</b>. This review has been added to the plan.</div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
<div class="notice notice-ready">
  <div class="notice-title">Ready to start</div>
  <div class="notice-text">No required prerequisite is missing from the topics selected in the sidebar.</div>
</div>
""",
        unsafe_allow_html=True,
    )

if plan:
    first = plan[0]
    st.markdown(
        f"""
<div class="next-card">
  <div class="next-number">1</div>
  <div>
    <div class="next-label">Recommended next action</div>
    <div class="next-title">{first['title']}</div>
    <div class="next-copy">{first['guidance']}</div>
  </div>
  <div class="time-badge"><div class="time-value">{first['minutes']} min</div><div class="time-label">focused time</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Main navigation
# -----------------------------------------------------------------------------
plan_tab, roadmap_tab, weekly_tab, catchup_tab, progress_tab = st.tabs(
    ["Study plan", "Topic roadmap", "Weekly routine", "Catch-up", "Progress"]
)

with plan_tab:
    st.markdown('<div class="section-title">Your ordered study plan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-intro">Core problem-solving stays first. Supporting resources are included only when the available time allows a meaningful study block.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="pathway">
  <span class="path-step">Lecture examples</span><span class="path-arrow">→</span>
  <span class="path-step">T-type questions</span><span class="path-arrow">→</span>
  <span class="path-step">H-type questions</span><span class="path-arrow">→</span>
  <span class="path-step">Supporting learning</span>
</div>
""",
        unsafe_allow_html=True,
    )

    rows = []
    for index, item in enumerate(plan, 1):
        left, right = st.columns([5.6, 1.2], vertical_alignment="center")
        with left:
            tag_class = importance_class(item["importance"])
            st.markdown(
                f"""
<div class="activity-card">
  <div class="activity-head">
    <div class="activity-order">{index}</div>
    <div>
      <div class="activity-name">{item['title']}</div>
      <div class="tag-row">
        <span class="tag {tag_class}">{STAR[item['importance']]}</span>
        <span class="tag tag-difficulty">{item['difficulty']}</span>
        <span class="tag tag-time">{item['minutes']} min</span>
      </div>
    </div>
  </div>
  <div class="activity-guidance">{item['guidance']}</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with right:
            st.checkbox(
                "Completed",
                key=f"complete_{selected_topic['id']}_{index}",
            )

        rows.append(
            {
                "Order": index,
                "Topic": selected_topic["title"],
                "Activity": item["title"],
                "Minutes": item["minutes"],
                "Importance": STAR[item["importance"]],
                "Guidance": item["guidance"],
            }
        )

    if unused >= 5:
        st.markdown(
            f"""
<div class="notice notice-info">
  <div class="notice-title">{unused} minutes remain</div>
  <div class="notice-text">Use this time to review errors, finish the current problem carefully, or explain the solution method aloud without looking at the notes.</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.download_button(
        "Download my study checklist",
        pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
        file_name=f"EG1011_{selected_topic['id']}_study_plan.csv",
        mime="text/csv",
        use_container_width=True,
    )

with roadmap_tab:
    st.markdown('<div class="section-title">Topic connections</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-intro">See what knowledge comes before this topic and which later topics depend on it.</div>',
        unsafe_allow_html=True,
    )

    before, after = st.columns(2)
    with before:
        st.markdown("#### Required before this topic")
        if selected_topic["required"]:
            for item in selected_topic["required"]:
                st.markdown(f"- **{topic_name(item)}**")
        else:
            st.success("This is a foundation topic.")

        st.markdown("#### Helpful background")
        if selected_topic["helpful"]:
            for item in selected_topic["helpful"]:
                st.markdown(f"- {topic_name(item)}")
        else:
            st.caption("No additional background is listed.")

    with after:
        downstream = [
            topic["title"]
            for topic in topics
            if selected_topic["id"] in topic["required"]
        ]
        st.markdown("#### Later topics that use this knowledge")
        if downstream:
            for item in downstream:
                st.markdown(f"- **{item}**")
        else:
            st.caption("No direct downstream topic is currently listed.")

    st.divider()
    st.markdown(f"#### {area} learning sequence")
    for topic in choices:
        status = "🔵" if topic["id"] == selected_topic["id"] else "⚪"
        st.markdown(f"{status} **Session {topic['session']}**  ·  {topic['title']}")

with weekly_tab:
    st.markdown('<div class="section-title">A simple weekly routine</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-intro">The routine keeps active problem-solving central and uses support materials at the right time.</div>',
        unsafe_allow_html=True,
    )

    routine = [
        ("01", "Before the lecture", "Preview the main ideas and terminology using the QuickGuide."),
        ("02", "After the lecture", "Cover the shown solution and re-solve the important lecture-note examples yourself."),
        ("03", "Before the tutorial", "Attempt the relevant T-type questions and mark the exact steps requiring clarification."),
        ("04", "During the tutorial", "Complete T-type questions, ask targeted questions, and record common errors."),
        ("05", "After the tutorial", "Attempt H-type questions independently before checking any support material."),
        ("06", "When you are stuck", "Use Step by Step, the interactive exercise, or Solutions in Action, then return to the original problem."),
        ("07", "End of the week", "Complete an exit check and explain one solution method without looking at the notes."),
    ]
    for number, title, text in routine:
        st.markdown(
            f"""
<div class="activity-card">
  <div class="activity-head">
    <div class="activity-order">{number}</div>
    <div><div class="activity-name">{title}</div><div class="activity-guidance">{text}</div></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

with catchup_tab:
    st.markdown('<div class="section-title">Build a catch-up pathway</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-intro">Select missed topics and the app will allocate a realistic minimum study period to each.</div>',
        unsafe_allow_html=True,
    )

    missed = st.multiselect(
        "Topics missed",
        [f"{topic['area']} S{topic['session']}: {topic['title']}" for topic in topics],
        placeholder="Select one or more missed topics",
    )
    total = st.select_slider(
        "Total catch-up time",
        options=[30, 60, 90, 120, 180, 240],
        value=120,
        format_func=lambda value: f"{value} min",
    )

    if missed:
        allocation = max(15, total // len(missed))
        st.warning("Focus on the minimum viable pathway rather than trying to complete every available activity.")
        for item in missed:
            st.markdown(
                f"""
<div class="activity-card">
  <div class="activity-name">{item}</div>
  <div class="tag-row"><span class="tag tag-time">About {allocation} min</span></div>
  <div class="activity-guidance"><b>Lecture example → T-type question → H-type question.</b> Use Step by Step, the interactive app, or Solutions in Action only where additional explanation is needed.</div>
</div>
""",
                unsafe_allow_html=True,
            )
    else:
        st.info("Select at least one missed topic to create a catch-up pathway.")

with progress_tab:
    st.markdown('<div class="section-title">Current plan progress</div>', unsafe_allow_html=True)
    completed_count = sum(
        st.session_state.get(
            f"complete_{selected_topic['id']}_{index}", False
        )
        for index in range(1, len(plan) + 1)
    )
    progress_fraction = completed_count / len(plan) if plan else 0
    st.progress(progress_fraction)

    p1, p2, p3 = st.columns(3)
    p1.metric("Completed", completed_count)
    p2.metric("Remaining", max(0, len(plan) - completed_count))
    p3.metric("Progress", f"{round(progress_fraction * 100)}%")

    st.markdown(
        """
<div class="notice notice-info">
  <div class="notice-title">When should I move on?</div>
  <div class="notice-text">Move on when you can re-solve an important lecture example, complete a T-type problem with limited support, and make a serious independent attempt at an H-type problem.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Progress is stored only during the current browser session.")

st.markdown(
    '<div class="mobile-note">EG1011 Study Navigator • Planning only • No course files, grades, student IDs, or login details are stored</div>',
    unsafe_allow_html=True,
)
