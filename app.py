"""EG1011 Study Navigator — run with: streamlit run app.py."""
from datetime import date, datetime
from html import escape
import json
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit.components.v1 import declare_component

from planner import (AREA_COLORS, CHALLENGES, GOALS, LEVELS, PROBLEM_ROUTES, activity_key,
                     blank_progress, build_session, build_week, calendar_file,
                     csv_plan, due_topics, gaps, level, next_gap, prerequisite_order,
                     progress_json, rate_topic, resource_url, validate_catalog,
                     validate_progress)

BASE = Path(__file__).resolve().parent
st.set_page_config(page_title="EG1011 · Study Navigator", page_icon="◉", layout="wide")


@st.cache_data
def load_catalog(file_versions):
    # File timestamps participate in the cache key so instructor JSON edits
    # become visible without waiting for an unrelated Python-code change.
    topics = json.loads((BASE / "data/topics.json").read_text(encoding="utf-8"))
    activities = json.loads((BASE / "data/study_activities.json").read_text(encoding="utf-8"))
    validate_catalog(topics, activities)
    return topics, activities


try:
    versions = tuple((BASE / "data" / name).stat().st_mtime_ns
                     for name in ("topics.json", "study_activities.json"))
    topics, activities = load_catalog(versions)
    by_topic, resources = validate_catalog(topics, activities)
except (OSError, ValueError, KeyError, TypeError) as exc:
    st.error(f"The course map needs an instructor update: {exc}")
    st.stop()

learning_map = declare_component("eg1011_learning_map", path=str(BASE / "components/learning_map"))
today = datetime.now(ZoneInfo("Australia/Brisbane")).date()
h = lambda text: escape(str(text), quote=True)

st.markdown("""
<style>
:root{--navy:#172f49;--ink:#243b51;--muted:#556b7e;--line:#dce5ee;--teal:#087f8c;--page:#f5f7fb}
.stApp{background:var(--page);color:var(--ink)}.block-container{max-width:1420px;padding-top:4.5rem;padding-bottom:3rem}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}
h1,h2,h3,h4{color:var(--navy);letter-spacing:-.025em}p{line-height:1.6}
section[data-testid="stSidebar"]{background:white;border-right:1px solid var(--line)}section[data-testid="stSidebar"] .block-container{padding-top:1.6rem}
[data-testid="stSidebar"] label{font-size:.86rem}[data-testid="stSidebar"] h3{font-size:1.15rem}
.brand{display:flex;gap:11px;align-items:center;margin-bottom:22px}.brand-mark{border:2px solid #087f8c;border-radius:50%;width:32px;height:32px;position:relative}.brand-mark:after{content:'';position:absolute;border:2px solid #c16a31;border-radius:50%;width:22px;height:22px;left:12px;top:8px}.brand strong{display:block;color:#172f49;font-size:16px}.brand small{display:block;color:#62778a;font-size:10px;letter-spacing:.13em;text-transform:uppercase}
.hero{background:#172f49;border-radius:22px;padding:28px 32px 24px;color:#fff;margin-bottom:18px;position:relative;overflow:hidden}.hero:before,.hero:after{content:'';position:absolute;border-radius:50%;pointer-events:none}.hero:before{width:240px;height:240px;right:-25px;top:-75px;border:35px solid #ffffff08}.hero:after{width:190px;height:190px;right:95px;top:-50px;border:2px solid #ffffff15}.eyebrow{font-size:10px;font-weight:750;text-transform:uppercase;letter-spacing:.14em;color:#96cbd0}.hero h1{font-size:clamp(1.65rem,3vw,2.25rem);font-weight:750;color:white;margin:5px 0 8px;padding:0;max-width:850px}.hero p{color:#d4e2ee;font-size:.9rem;margin:0;max-width:770px}.hero-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.hero-tag{background:#ffffff0e;border:1px solid #ffffff20;border-radius:30px;padding:5px 11px;font-size:11px;color:#e5eff7}
.kicker{font-size:10px;font-weight:750;letter-spacing:.12em;text-transform:uppercase;color:#58748a;margin:4px 0 5px}.focus-title{font-size:1.5rem;font-weight:750;line-height:1.3;color:#172f49;margin:0 0 7px}.focus-copy{font-size:.9rem;color:#556b7e;margin:0 0 8px;max-width:950px}.pill{display:inline-block;font-size:10px;font-weight:650;border-radius:20px;padding:5px 10px;background:#e8eef4;margin:2px 6px 2px 0;color:#36556f}.source{color:#62778b;font-size:11px;margin:9px 0 20px}
.next{background:#edf5f3;border:1px solid #cde3db;border-radius:17px;padding:18px 20px;margin-bottom:13px}.next .kicker{color:#34745f}.next h3{font-size:1.1rem;margin:3px 0 8px;padding:0}.next p{font-size:.84rem;line-height:1.55;margin:0;color:#375b50}.time{display:inline-block;margin:0 0 8px;font-size:11px;font-weight:750;color:#24694e}.hint-card{border:1px solid #e7d6ba;background:#fff9ee;border-radius:15px;padding:14px 17px;margin:10px 0 14px;font-size:.82rem;line-height:1.55;color:#71552e}.hint-card strong{color:#694a1c}
.material{border-left:4px solid var(--resource-color);padding:2px 0 2px 14px;margin:10px 0 14px}.material h4{font-size:1.03rem;margin:0 0 6px;padding:0}.material p{font-size:.84rem;color:#496277;margin:0;line-height:1.6}.material .kicker{color:var(--resource-color)}
.step{display:flex;gap:12px;align-items:flex-start;padding:13px 0 11px;border-bottom:1px solid #e4ebf1}.step-number{background:var(--c);color:white;flex:0 0 28px;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:750}.step-title{font-size:.88rem;font-weight:700;color:#1f3a51}.step-meta{color:#5b7082;font-size:11px;margin:2px 0 4px}.step-reason{font-size:.8rem;color:#546b7f;line-height:1.45}.step-done{opacity:.6}.mini-stat{border:1px solid #dce5ee;background:white;border-radius:14px;padding:14px 17px;margin:3px 0 15px}.mini-stat b{font-size:1.5rem;color:#172f49;display:block}.mini-stat span{font-size:11px;color:#607487}.bridge{color:#3d5d77;font-size:.82rem;line-height:1.6}.footer{border-top:1px solid #dce5ee;padding-top:16px;margin-top:28px;color:#60768a;font-size:11px;line-height:1.6}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:17px!important}.stButton button,.stDownloadButton button,.stLinkButton a{border-radius:10px;font-weight:600}.stButton button[kind="primary"]{background:#087f8c;border-color:#087f8c;color:white}.stButton button[kind="primary"]:hover{background:#066c77;border-color:#066c77}
div[data-baseweb="select"]>div{border-radius:10px}[data-testid="stMetricValue"]{font-size:1.5rem}button:focus-visible{outline:3px solid #357cb6!important;outline-offset:2px}
@media(max-width:800px){.block-container{padding-top:4.25rem;padding-left:1rem;padding-right:1rem}.hero{padding:22px 20px;border-radius:16px}.hero h1{max-width:95%;font-size:1.65rem}.hero-tags{gap:5px}.hero-tag{font-size:10px}.focus-title{font-size:1.3rem}}
</style>
""", unsafe_allow_html=True)

# Callbacks queue topic changes so map clicks and native widgets stay in sync.
ss = st.session_state
for key, value in {"progress": blank_progress(), "focus": "S1_FORCE", "area_picker": "Statics",
                   "topic_picker": "S1_FORCE", "resource_picker": "LN", "storage_ready": False,
                   "storage_failed": False, "boot": str(uuid4()), "handled_events": [], "epoch": 0}.items():
    if key not in ss:
        ss[key] = value


def queue_topic(topic_id, view=None):
    ss.pending_topic = topic_id
    if view:
        ss.pending_view = view


def queue_resource(resource_id):
    ss.pending_resource = resource_id


def change_area():
    queue_topic(next(t["id"] for t in topics if t["area"] == ss.area_picker))


def change_topic():
    queue_topic(ss.topic_picker)


def use_topic(topic_id, view=None):
    queue_topic(topic_id, view)
    st.rerun()


if "pending_topic" in ss:
    tid = ss.pop("pending_topic")
    if tid in by_topic:
        ss.focus = tid
        ss.area_picker = by_topic[tid]["area"]
        ss.topic_picker = tid
        ss.resource_picker = "LN"
if "pending_resource" in ss:
    rid = ss.pop("pending_resource")
    if rid in resources:
        ss.resource_picker = rid
if "pending_view" in ss:
    ss.view = ss.pop("pending_view")


def handle_event(event):
    if not isinstance(event, dict) or not event.get("event_id") or event["event_id"] in ss.handled_events:
        return
    ss.handled_events = (ss.handled_events + [event["event_id"]])[-100:]
    kind = event.get("kind")
    if kind == "topic" and event.get("id") in by_topic:
        use_topic(event["id"], "My pathway" if event.get("view") == "My pathway" else None)
    elif kind == "resource" and event.get("id") in resources:
        queue_resource(event["id"])
        st.rerun()
    elif kind == "restore" and not ss.storage_ready:
        try:
            if event.get("data") is not None:
                ss.progress = validate_progress(event["data"], by_topic, resources)
                ss.epoch += 1
        except (ValueError, TypeError, KeyError, OverflowError):
            ss.storage_notice = "The saved progress could not be read. You can restore a downloaded backup in My progress."
        ss.storage_ready = True
        st.rerun()
    elif kind == "storage_error":
        ss.storage_ready = True
        ss.storage_failed = True
        st.rerun()


def toggle_activity(key, widget_key, duration):
    if ss[widget_key]:
        ss.progress["completed"][key] = {"date": today.isoformat(), "minutes": duration}
    else:
        ss.progress["completed"].pop(key, None)


def completion_checkbox(block, label="Done"):
    widget_key = f"task_{ss.epoch}_{block['key']}"
    if widget_key not in ss:
        ss[widget_key] = block["key"] in ss.progress["completed"]
    st.checkbox(label, key=widget_key, on_change=toggle_activity,
                args=(block["key"], widget_key, block["minutes"]))


def repeat_pathway(keys):
    for key in keys:
        ss.progress["completed"].pop(key, None)
    ss.epoch += 1


def source_text(topic):
    source = topic["source"]
    a, b = source["pages"]
    return f"{source['file']} · " + (f"p. {a}" if a == b else f"pp. {a}–{b}")


def mini_stat(column, number, text):
    with column:
        st.markdown(f'<div class="mini-stat"><b>{h(number)}</b><span>{h(text)}</span></div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark"></div><div><strong>Study Navigator</strong><small>EG1011 · Learning studio</small></div></div>', unsafe_allow_html=True)
    st.radio("Subject area", ["Statics", "Dynamics", "Foundations"], key="area_picker", on_change=change_area, horizontal=True)
    choices = [t["id"] for t in topics if t["area"] == ss.area_picker]
    st.selectbox("What are you working on?", choices, key="topic_picker", format_func=lambda t: by_topic[t]["title"], on_change=change_topic)
    st.selectbox("My goal", GOALS, key="goal")
    st.radio("Confidence for this session", ["Low", "Medium", "High"], index=1, horizontal=True, key="confidence")
    st.select_slider("Time for this session", options=[15, 30, 45, 60, 90, 120], value=60, format_func=lambda v: f"{v} min", key="minutes")
    st.selectbox("Where do you get stuck?", CHALLENGES, key="challenge")
    st.caption("The plan changes with your goal, time, topic ratings and the step you find difficult.")
    st.divider()
    st.caption("FIRST VISIT? Mark familiar topics in My progress to personalise the prerequisite review.")
    storage_event = learning_map(mode="storage", payload=ss.progress, restore=not ss.storage_ready,
                                 boot=ss.boot, key="browser_progress", default=None)
    handle_event(storage_event)
    if ss.storage_failed:
        st.caption("Browser saving is unavailable. Download a progress backup before leaving.")

p = ss.progress
topic = by_topic[ss.focus]
result = build_session(topic["id"], by_topic, resources, p, ss.minutes, ss.goal, ss.confidence, ss.challenge)
plan = result["blocks"]
missing = result["gaps"]
ready_count = sum(level(p, t["id"]) >= 2 for t in topics)
independent_count = sum(level(p, t["id"]) == 3 for t in topics)

st.markdown(f"""
<div class="hero"><div class="eyebrow">First-year engineering · Statics & Dynamics</div>
<h1>See the connections.<br>Find your next step.</h1>
<p>Build from what you know, practise what you need, and make a study plan you can actually follow.</p>
<div class="hero-tags"><span class="hero-tag">{h(topic['area'])}{' · Session '+str(topic['session']) if topic['session'] else ' · Previous knowledge'}</span>
<span class="hero-tag">{result['minutes']} / {ss.minutes} min planned</span>
<span class="hero-tag">{len(missing)} building block{'s' if len(missing)!=1 else ''} to check</span>
<span class="hero-tag">{independent_count} / {len(topics)} topics independent</span></div></div>
""", unsafe_allow_html=True)
if ss.get("storage_notice"):
    st.info(ss.storage_notice)

view = st.radio("Explore your learning", ["My pathway", "Topic connections", "Weekly studio", "My progress"], horizontal=True, label_visibility="collapsed", key="view")
with st.expander("Not sure which topic you need? Start from your problem"):
    clue = st.selectbox("What does the question ask you to do?", list(PROBLEM_ROUTES), index=None,
                        placeholder="Choose a problem clue…")
    if clue:
        route_ids, explanation = PROBLEM_ROUTES[clue]
        st.caption(explanation)
        route_cols = st.columns(len(route_ids))
        for col, tid in zip(route_cols, route_ids):
            with col:
                st.button("Explore " + by_topic[tid]["short_title"], key="find_"+tid,
                          on_click=queue_topic, args=(tid, "My pathway"), use_container_width=True)
st.markdown(f'<div class="kicker">{h(topic["area"])} · {"Session "+str(topic["session"]) if topic["session"] else "Foundations"}</div><div class="focus-title">{h(topic["title"])}</div><p class="focus-copy">{h(topic["description"])}</p>', unsafe_allow_html=True)
st.markdown(''.join(f'<span class="pill">{h(x)}</span>' for x in topic['outcomes']), unsafe_allow_html=True)
st.markdown(f'<div class="source">Lecture-note locator: {h(source_text(topic))} · Open your materials on the EG1011 course site.</div>', unsafe_allow_html=True)


def rate_current_topic():
    with st.form(f"rate_{topic['id']}_{ss.epoch}"):
        value = st.selectbox("What can you do on this topic?", range(4), index=level(p, topic["id"]), format_func=lambda n: LEVELS[n])
        st.caption("Choose independent only if you can solve a fresh problem and explain your method with notes closed.")
        if st.form_submit_button("Save my topic rating", use_container_width=True):
            rate_topic(p, topic["id"], value, today)
            st.rerun()


def concept_check():
    check = topic["check"]
    with st.expander("Try a short concept check", expanded=False):
        st.caption("This checks one idea; a correct answer alone does not establish independent problem-solving.")
        with st.form(f"check_{topic['id']}"):
            answer = st.radio(check["question"], range(len(check["options"])), index=None,
                              format_func=lambda i: check["options"][i], key=f"answer_{topic['id']}_{ss.epoch}")
            if st.form_submit_button("Check my reasoning"):
                if answer is None:
                    st.warning("Choose an answer before checking.")
                else:
                    p["checks"][topic["id"]] = {"answer": answer, "correct": answer == check["answer"], "date": today.isoformat()}
                    st.rerun()
        saved = p["checks"].get(topic["id"])
        if saved:
            if saved["correct"]:
                st.success("Correct. " + check["explanation"])
            else:
                st.info("Revisit this idea. " + check["explanation"])
                repair = check["repair_topic"]
                if repair != topic["id"]:
                    st.button("Reconnect with " + by_topic[repair]["short_title"], key="repair_"+topic["id"], on_click=queue_topic, args=(repair,))


if view == "My pathway":
    left, right = st.columns([1.7, 1], gap="large")
    with left:
        st.markdown("#### Your learning orbit")
        main_blocks = [dict(b, step=i) for i, b in enumerate(plan, 1)
                       if b["topic_id"] == topic["id"] and b["role"] == "practice"]
        active_resource = ss.resource_picker if ss.resource_picker in topic["activities"] else "LN"
        event = learning_map(mode="resources", payload={"topic": topic, "resources": [resources[i] for i in topic["activities"]],
                             "plan": main_blocks, "selected_resource": active_resource,
                             "completed": [a for a in topic["activities"] if activity_key(topic["id"], a) in p["completed"]]},
                             key="resource_orbit", default=None)
        handle_event(event)
        # Native equivalent remains usable on small screens and with assistive technology.
        if ss.resource_picker not in topic["activities"]:
            ss.resource_picker = "LN"
        material_id = st.selectbox("Explore a material", topic["activities"], format_func=lambda r: resources[r]["title"], key="resource_picker")
        item = resources[material_id]
        st.markdown(f'<div class="material" style="--resource-color:{item["color"]}"><div class="kicker">{h(item["phase"])} · {h(item["type"])}</div><h4>{h(item["title"])}</h4><p>{h(item["guidance"])}</p></div>', unsafe_allow_html=True)
        if material_id == "LN":
            st.info(topic["practice_prompt"])
        link = resource_url(topic, item)
        if link:
            st.link_button("Open this material", link, use_container_width=True)
        else:
            st.caption("Find the matching topic material on the EG1011 course site. The circles show how to use it.")
        st.markdown(f'<div class="hint-card"><strong>A mistake to watch for</strong><br>{h(topic["common_mistake"])}</div>', unsafe_allow_html=True)
        concept_check()
    with right:
        first = next((b for b in plan if b["key"] not in p["completed"]), None)
        if first:
            st.markdown(f'<div class="next"><div class="kicker">Your next useful action</div><h3>{h(first["title"])}</h3><div class="time">{first["minutes"]} focused minutes</div><p>{h(first["reason"])}</p></div>', unsafe_allow_html=True)
            if first["topic_id"] != topic["id"]:
                st.button("Explore this building block", on_click=queue_topic, args=(first["topic_id"],), use_container_width=True)
        else:
            st.success("This pathway is complete. Try a fresh problem, reflect, and update your topic rating below.")
        if missing:
            unknown = sum(level(p, t) == 0 for t in missing)
            st.markdown(f'<div class="hint-card"><strong>{len(missing)} building blocks to check</strong><br>{unknown} are not yet checked. Today reviews one gap; a short review does not clear the others. Mark familiar topics in My progress.</div>', unsafe_allow_html=True)
        else:
            st.caption("Your prerequisite ratings suggest you can begin. Revisit a building block whenever a problem exposes a gap.")
        done = sum(b["key"] in p["completed"] for b in plan)
        st.progress(done / len(plan), text=f"{done} of {len(plan)} activities completed")
        for order, block in enumerate(plan, 1):
            status = " step-done" if block["key"] in p["completed"] else ""
            st.markdown(f'<div class="step{status}"><span class="step-number" style="--c:{block["color"]}">{order}</span><div><div class="step-title">{h(block["title"])}</div><div class="step-meta">{block["minutes"]} min · {h(block["topic_title"])}</div><div class="step-reason">{h(block["reason"])}</div></div></div>', unsafe_allow_html=True)
            completion_checkbox(block, f"Complete step {order}")
        if result["unused"]:
            st.caption(f"{result['unused']} min spare: explain a method aloud or record an error to revisit.")
        st.download_button("Download this pathway · CSV", csv_plan([(i, b) for i, b in enumerate(plan, 1)]), file_name=f"EG1011_{topic['id']}_pathway.csv", mime="text/csv", use_container_width=True)
        if done:
            st.button("Start a fresh attempt", key="repeat_pathway", on_click=repeat_pathway,
                      args=([b["key"] for b in plan],), use_container_width=True)
        with st.expander("Reflect and update my topic rating"):
            rate_current_topic()

elif view == "Topic connections":
    controls, details = st.columns([2.2, 1])
    with controls:
        scope = st.radio("Map view", ["Focus chain", "Whole course"], horizontal=True)
        earlier = st.checkbox("Show the full prerequisite chain", value=False, disabled=scope == "Whole course")
    if scope == "Whole course":
        visible = set(by_topic)
    else:
        visible = set(prerequisite_order([topic["id"]], by_topic) if earlier else [topic["id"]]+topic["required"])
        visible.update(topic.get("helpful", []))
        visible.update(t["id"] for t in topics if topic["id"] in t["required"])
    direct = set(topic["required"])
    later = {t["id"] for t in topics if topic["id"] in t["required"]}
    nodes = []
    for t in topics:
        if t["id"] not in visible:
            continue
        role = "focus" if t["id"] == topic["id"] else "next" if t["id"] in later else "before"
        column = 0 if role == "focus" else 1 if role == "next" else -1 if t["id"] in direct or t["id"] in topic.get("helpful", []) else -2
        nodes.append(dict(t, level=level(p, t["id"]), role=role, column=column))
    edges = []
    for t in topics:
        if t["id"] not in visible:
            continue
        for parent in t["required"]:
            if parent in visible:
                edges.append({"from": parent, "to": t["id"], "helpful": False})
        # Helpful links are only shown for the focus, to keep the graph readable.
        if t["id"] == topic["id"]:
            edges.extend({"from": parent, "to": t["id"], "helpful": True} for parent in t.get("helpful", []) if parent in visible)
    event = learning_map(mode="topics", payload={"nodes": nodes, "edges": edges, "scope": "all" if scope == "Whole course" else "focus"}, key="topic_graph", default=None)
    handle_event(event)
    a, b = st.columns([1.5, 1])
    with a:
        st.markdown("#### Why these connections matter")
        st.markdown(f'<p class="bridge">{h(topic["practice_prompt"])}</p>', unsafe_allow_html=True)
        if missing:
            target = next_gap(topic["id"], by_topic, p)
            st.button("Practise this building block: " + by_topic[target]["short_title"], on_click=queue_topic, args=(target, "My pathway"), use_container_width=True)
        target_options = [t["id"] for t in topics if t["id"] in visible and t["id"] != topic["id"]]
        if target_options:
            jump = st.selectbox("Explore a connected topic", target_options, format_func=lambda t: f"{by_topic[t]['area']} · {by_topic[t]['title']}")
            st.button("Make this my focus", on_click=queue_topic, args=(jump,), use_container_width=True)
    with b:
        rate_current_topic()

elif view == "Weekly studio":
    st.markdown("#### Give your practice a place in the week")
    st.caption("Choose focus topics and study days. The planner adds unchecked prerequisites in learning order, then fits activities inside your time budget.")
    if "week_targets" not in ss:
        ss.week_targets = [topic["id"]]
    targets = st.multiselect("This week’s focus topics", list(by_topic), key="week_targets", format_func=lambda t: f"{by_topic[t]['area']} · {by_topic[t]['title']}", max_selections=4)
    c1, c2, c3 = st.columns([1, 1.7, 1])
    with c1:
        start = st.date_input("Seven days starting", value=today)
    with c2:
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days = st.multiselect("Days I can study", names, default=["Mon", "Wed", "Fri", "Sun"])
    with c3:
        daily = st.select_slider("Minutes per study day", options=[15,30,45,60,90,120,180], value=60, format_func=lambda v: f"{v} min")
    week = build_week(targets, by_topic, resources, p, start, [names.index(d) for d in days], daily, ss.goal)
    if not targets or not days:
        st.info("Choose at least one focus topic and one study day to build your week.")
    else:
        s1, s2, s3 = st.columns(3)
        mini_stat(s1, f"{week['minutes']} / {week['capacity']}", "minutes planned / available")
        mini_stat(s2, len(week["route"]), "topics in your learning route, including prerequisites")
        mini_stat(s3, len({b["topic_id"] for b in week["backlog"]}), "topics with activities still to schedule")
        handle_event(learning_map(mode="week", payload=week, key="weekly_timeline", default=None))
        if week["backlog"]:
            st.info(f"Your available time leaves {len(week['backlog'])} activities for a later week. Add time, narrow the focus, or mark topics you can already solve in My progress.")
            with st.expander("See what carries into the next week"):
                for tid in dict.fromkeys(b["topic_id"] for b in week["backlog"]):
                    minutes_left = sum(b["minutes"] for b in week["backlog"] if b["topic_id"] == tid)
                    st.write(f"{by_topic[tid]['title']} · {minutes_left} min still to schedule")
        x, y = st.columns(2)
        with x:
            st.download_button("Download weekly plan · CSV", csv_plan([(day["date"], block) for day in week["days"] for block in day["blocks"]]), file_name="EG1011_weekly_plan.csv", mime="text/csv", use_container_width=True)
        with y:
            stamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
            st.download_button("Add study days to calendar · ICS", calendar_file(week, stamp), file_name="EG1011_study_days.ics", mime="text/calendar", use_container_width=True)
        st.caption("Calendar entries are all-day personal study reminders. Use the official timetable and assessment dates for class commitments.")

elif view == "My progress":
    a, b, c = st.columns(3)
    mini_stat(a, independent_count, "topics rated independent")
    mini_stat(b, len(p["completed"]), "distinct activities completed")
    mini_stat(c, len(due_topics(p, by_topic, today)), "topics suggested for a spaced review")
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.markdown("#### Tell the planner what you already know")
        st.caption("Ratings are your self-assessment. An activity tick or a correct concept answer does not automatically change them.")
        rate_current_topic()
        with st.expander("Quick setup: add familiar topics", expanded=not bool(p["ratings"])):
            with st.form("bulk_ratings"):
                known = st.multiselect("Select topics you have already practised", list(by_topic), format_func=lambda t: f"{by_topic[t]['area']} · {by_topic[t]['title']}")
                rating = st.radio("I can solve these…", [2, 3], format_func=lambda n: LEVELS[n], horizontal=True)
                if st.form_submit_button("Save these topic ratings", use_container_width=True):
                    for tid in known:
                        rate_topic(p, tid, rating, today)
                    st.rerun()
        st.markdown("#### Turn an error into your next practice target")
        with st.form("error_note", clear_on_submit=True):
            note = st.text_area("What went wrong, and what will you do differently?", placeholder="Example: I used the wrong moment arm. Next time I will draw the perpendicular distance before calculating.", max_chars=800, height=105)
            if st.form_submit_button("Save my error note") and note.strip():
                p["errors"] = (p["errors"] + [{"topic_id": topic["id"], "text": note.strip(), "date": today.isoformat()}])[-100:]
                st.rerun()
        for i, note in enumerate(reversed(p["errors"][-8:])):
            with st.expander(f"{by_topic[note['topic_id']]['short_title']} · {note['date']}"):
                st.text(note["text"])
                st.button("Practise this topic", key=f"note_jump_{i}", on_click=queue_topic, args=(note["topic_id"], "My pathway"))
    with right:
        st.markdown("#### Revisit before you forget")
        due = due_topics(p, by_topic, today)
        if due:
            for tid, when in due[:5]:
                st.button("↻ " + by_topic[tid]["short_title"], key="due_"+tid, on_click=queue_topic, args=(tid, "My pathway"), use_container_width=True)
            st.caption("Suggested intervals expand from 1 to 3, 7 and 14 days after ratings on different dates. Change the plan if recall is difficult.")
        else:
            st.caption("No reviews are due yet. After practising, save a topic rating to start suggested spaced reviews.")
        st.markdown("#### Keep your progress")
        st.caption("Progress is saved automatically in this browser when browser storage is available. Download a backup to use another device or browser.")
        st.download_button("Download progress backup · JSON", progress_json(p), file_name=f"EG1011_progress_{today.isoformat()}.json", mime="application/json", use_container_width=True)
        upload = st.file_uploader("Restore a progress backup", type=["json"], help="An EG1011 progress backup up to 200 KB.")
        if upload is not None and st.button("Restore this backup", use_container_width=True):
            try:
                if upload.size > 200000:
                    raise ValueError("This backup is too large. Choose a file up to 200 KB.")
                restored = validate_progress(json.loads(upload.getvalue().decode("utf-8")), by_topic, resources)
                ss.progress = restored
                ss.storage_ready = True
                ss.epoch += 1
                st.rerun()
            except (ValueError, TypeError, KeyError, UnicodeDecodeError, OverflowError) as exc:
                st.error(f"The backup could not be restored. {exc}")
        with st.expander("Clear progress on this browser"):
            confirm = st.checkbox("Clear my saved topic ratings, activities and error notes")
            if st.button("Clear my progress", disabled=not confirm, use_container_width=True):
                ss.progress = blank_progress()
                ss.storage_ready = True
                ss.epoch += 1
                st.rerun()
        with st.expander("My topic ratings"):
            rated = [t for t in topics if level(p, t["id"]) > 0]
            if not rated:
                st.caption("No ratings saved yet.")
            for t in rated:
                st.caption(t["title"] + " · " + LEVELS[level(p, t["id"])])

st.markdown('<div class="footer">EG1011 · Study Navigator · Learn → attempt → check → revisit.<br>Study suggestions support your course materials. Your official timetable, assessment instructions and lecturer advice take priority.</div>', unsafe_allow_html=True)
