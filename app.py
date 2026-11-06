import json
from pathlib import Path
import pandas as pd
import streamlit as st

BASE = Path(__file__).parent
DATA = BASE / "data"

st.set_page_config(page_title="EG1011 Study Navigator", page_icon="🧭", layout="wide")

@st.cache_data
def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

topics = load("topics.json")
activities = load("study_activities.json")
by_topic = {t["id"]: t for t in topics}
activity_map = {a["id"]: a for a in activities}

st.markdown("""
<style>
.block-container{max-width:1150px;padding-top:1.5rem}.hero{padding:1.6rem 1.8rem;border-radius:22px;color:white;background:linear-gradient(135deg,#11354d,#14718a,#18a3a0);box-shadow:0 12px 28px #1233;margin-bottom:1rem}.hero h1{margin:0}.box{padding:1rem 1.1rem;border:1px solid #dbe6ea;border-radius:16px;margin:.6rem 0;background:#fff}.warning{border-left:6px solid #d65b5b;background:#fff8f8}.ready{border-left:6px solid #2e9b70;background:#f5fffa}.next{border-left:6px solid #efb447;background:#fffaf0}.pill{display:inline-block;padding:.25rem .6rem;margin:.15rem;border-radius:999px;background:#e8f5f6;color:#125c67;font-weight:650;font-size:.86rem}
</style>
<div class="hero"><h1>EG1011 Study Navigator</h1><p>Plan what to study, in what order, and which earlier topics to review. All learning materials remain on the EG1011 subject website.</p></div>
""", unsafe_allow_html=True)

STAR = {5:"★★★★★ Essential",4:"★★★★☆ Strongly recommended",3:"★★★☆☆ Consolidation",2:"★★☆☆☆ Additional practice",1:"★☆☆☆☆ Extension"}

def name(tid):
    return by_topic.get(tid, {}).get("title", tid)

def priority(item, confidence, goal):
    p = item["importance"]
    if confidence == "Low" and item["type"] in ["QuickGuide","Step by Step with Mehdi","Interactive app"]: p += 1
    if confidence == "High" and item["type"] in ["H questions","Mixed practice"]: p += 1
    if goal == "Prepare for tutorial" and item["type"] in ["QuickGuide","T questions"]: p += 1
    if goal == "Quiz or exam revision" and item["type"] in ["H questions","Exit check"]: p += 1
    if goal == "Catch up after missing classes" and item["type"] in ["QuickGuide","Lecture notes","Step by Step with Mehdi"]: p += 1
    return min(5,p)

def build_plan(topic, confidence, goal, minutes, completed):
    missing=[x for x in topic["required"] if x not in completed]
    plan=[]
    remaining=minutes
    if missing:
        n=min(15,max(6,round(minutes*.18)))
        plan.append({"title":"Targeted prerequisite review","type":"Review","importance":5,"difficulty":"Foundation","minutes":n,"guidance":", ".join(name(x) for x in missing)})
        remaining-=n
    items=[activity_map[x].copy() for x in topic["activities"]]
    for x in items: x["importance"]=priority(x,confidence,goal)
    items.sort(key=lambda x:(-x["importance"],x["sequence"]))
    for x in items:
        if remaining < 5: break
        x["minutes"]=min(x["minutes"],remaining)
        plan.append(x); remaining-=x["minutes"]
    return plan,missing

with st.sidebar:
    st.header("Create my plan")
    area=st.radio("Subject area",["Statics","Dynamics"],horizontal=True)
    choices=[t for t in topics if t["area"]==area]
    chosen=st.selectbox("Current topic",[t["title"] for t in choices])
    topic=next(t for t in choices if t["title"]==chosen)
    goal=st.selectbox("Study goal",["Prepare for lecture","Prepare for tutorial","Independent study","Quiz or exam revision","Catch up after missing classes","Review a difficult topic"])
    confidence=st.radio("Current confidence",["Low","Medium","High"],horizontal=True)
    minutes=st.select_slider("Available time",[15,30,45,60,90,120],value=60)
    st.divider(); st.subheader("Previously completed")
    completed=[]
    for t in choices:
        if t["id"]!=topic["id"] and t["session"]<=topic["session"]:
            if st.checkbox(t["title"],key="done_"+t["id"]): completed.append(t["id"])

plan,missing=build_plan(topic,confidence,goal,minutes,completed)
a,b,c,d=st.columns(4)
a.metric("Session",topic["session"]); b.metric("Time",f"{minutes} min"); c.metric("Activities",len(plan)); d.metric("Reviews needed",len(missing))
st.subheader(topic["title"]); st.write(topic["description"])
st.markdown(" ".join(f'<span class="pill">{x}</span>' for x in topic["outcomes"]),unsafe_allow_html=True)
if missing:
    st.markdown(f'<div class="box warning"><b>Review recommended first</b><br>{", ".join(name(x) for x in missing)}</div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="box ready"><b>You appear ready to begin.</b><br>No required prerequisite is missing from your checklist.</div>',unsafe_allow_html=True)
if plan:
    st.markdown(f'<div class="box next"><b>Your next step</b><h3>{plan[0]["title"]}</h3>{plan[0]["guidance"]}<br><small>{plan[0]["minutes"]} minutes</small></div>',unsafe_allow_html=True)

p1,p2,p3,p4,p5=st.tabs(["My study plan","Topic roadmap","Weekly pathway","Catch-up planner","Progress"])
with p1:
    st.caption("This app gives planning instructions only. Open the named material from its normal location on the EG1011 website.")
    rows=[]
    for i,x in enumerate(plan,1):
        left,right=st.columns([5,1])
        with left:
            st.markdown(f"### {i}. {x['title']}")
            st.write(x["guidance"])
            st.caption(f"{x['type']} • Difficulty: {x['difficulty']} • {STAR[x['importance']]}")
        with right:
            st.metric("Time",f"{x['minutes']} min")
            st.checkbox("Complete",key=f"complete_{topic['id']}_{i}")
        rows.append({"Order":i,"Topic":topic["title"],"Activity":x["title"],"Minutes":x["minutes"],"Importance":x["importance"],"Guidance":x["guidance"]})
        st.divider()
    st.download_button("Download planning checklist",pd.DataFrame(rows).to_csv(index=False).encode(),f"EG1011_{topic['id']}_plan.csv","text/csv",use_container_width=True)
with p2:
    st.subheader("Topic connections")
    st.markdown("**Required earlier topics**")
    if topic["required"]:
        for x in topic["required"]: st.write("→ "+name(x))
    else: st.success("Foundation topic")
    st.markdown("**Helpful background**")
    if topic["helpful"]:
        for x in topic["helpful"]: st.write("• "+name(x))
    else: st.write("No additional background listed.")
    downstream=[t["title"] for t in topics if topic["id"] in t["required"]]
    if downstream:
        st.markdown("**Later topics that depend on this topic**")
        for x in downstream: st.write("→ "+x)
    st.divider(); st.subheader(area+" sequence")
    for t in choices: st.write(("🔵 " if t["id"]==topic["id"] else "⚪ ")+f"Session {t['session']}: **{t['title']}**")
with p3:
    for title,text in [("Before lecture","Use Start Here and the QuickGuide to preview key ideas."),("After lecture","Review selected lecture-note sections and one Step by Step example."),("Before tutorial","Use the interactive exercise and attempt the first T question."),("During tutorial","Complete T questions and record common errors."),("After tutorial","Attempt H questions independently before checking solutions."),("End of week","Complete an exit check and one mixed retrieval problem.")]:
        st.markdown("**"+title+"**"); st.write(text)
with p4:
    missed=st.multiselect("Missed topics",[f"{t['area']} S{t['session']}: {t['title']}" for t in topics])
    total=st.select_slider("Total catch-up time",[30,60,90,120,180,240],value=120)
    if missed:
        share=max(15,total//len(missed)); st.warning("Use a minimum viable pathway rather than attempting every activity.")
        for x in missed: st.write(f"**{x}:** approximately {share} min. QuickGuide → Step by Step → one T question → one H or exit question.")
with p5:
    done=sum(st.session_state.get(f"complete_{topic['id']}_{i}",False) for i in range(1,len(plan)+1))
    st.progress(done/len(plan) if plan else 0); st.write(f"{done} of {len(plan)} activities completed in this browser session.")
    st.info("Move on when you can choose the correct method, complete a standard problem without prompts, and score at least 4/5 on an exit check.")

st.divider(); st.caption("Planning only • No course files, links, grades, student IDs, or login details are stored")
