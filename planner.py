"""Explainable EG1011 planning. Pure Python; no API keys or external services."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import csv
import io
import json
import math
from urllib.parse import urlsplit


LEVELS = ("Not checked", "Needs practice", "Can solve with help", "Can solve independently")
GOALS = ("Independent practice", "Prepare for a lecture", "Prepare for a tutorial",
         "Quiz or exam revision", "Catch up", "Understand a difficult topic")
CHALLENGES = ("Not sure yet", "Choosing a method", "Drawing the diagram",
              "Maths or signs", "Starting a question", "Checking my answer")
AREA_COLORS = {"Foundations": "#8B66AD", "Statics": "#087F8C", "Dynamics": "#C16A31"}
SCHEMA = 2
PROBLEM_ROUTES = {
    "Resolve a force or find its direction": (["S1_FORCE", "S2_VECTOR"], "Start with 2D components; use the 3D vector method when coordinates describe a line in space."),
    "Draw supports, contacts or a free-body diagram": (["S1_FBD"], "Identify the isolated body and external forces before choosing equations."),
    "Find beam support reactions": (["S2_REACT", "S2_DIST"], "Use rigid-body equilibrium; convert distributed loads to resultants when needed."),
    "Find forces in truss members": (["S1_TRUSS"], "Choose joints for a sequence of member forces or sections for a selected member."),
    "Find a moment about a 3D point or axis": (["S2_MOM3D"], "Use a vector moment; project onto a unit axis for an axis moment."),
    "Draw a shear-force or bending-moment diagram": (["S3_INTERNAL", "S3_DIAGRAM"], "Begin with reactions and section cuts, then connect the piecewise shear and moment."),
    "Find the centroid or an area property": (["S4_CENT", "S4_MOI"], "Find the centroid first when the required second moment is about a centroidal axis."),
    "Relate position, velocity, acceleration and time": (["D1_KIN", "D1_VARIABLE"], "Check whether acceleration is constant; otherwise select a derivative or integral relationship."),
    "Find a force, tension or reaction during motion": (["D2_FA", "D2_CURVE"], "Connect a free-body diagram to acceleration; choose normal-tangential axes on a curved path."),
    "Find particle speed after a distance or height change": (["D3_WE", "D3_CONSERVE"], "Consider work-energy; account for friction and other nonconservative work."),
    "Find velocities in a link, gear, belt or rolling body": (["D4_RBV", "D4_IC"], "Use rigid-body velocity and compatibility; no-slip or an instantaneous centre may simplify the motion."),
    "Find accelerations in a rigid-body mechanism": (["D5_RBA"], "Complete velocity analysis first, then include both normal and tangential terms."),
    "Find speed in a rotating or rolling energy problem": (["D6_MASS", "D6_RBE"], "Include the correct translational and rotational kinetic energy, work terms and motion constraints."),
}


def validate_catalog(topics, activities):
    """Fail early on broken links, cycles or malformed instructor edits."""
    by_id = {t["id"]: t for t in topics}
    resources = {a["id"]: a for a in activities}
    if len(by_id) != len(topics) or len(resources) != len(activities):
        raise ValueError("Topic and resource IDs must be unique.")
    for topic in topics:
        if topic["area"] not in AREA_COLORS:
            raise ValueError(f"Unknown subject area for {topic['id']}")
        for other in topic["required"] + topic.get("helpful", []):
            if other not in by_id or other == topic["id"]:
                raise ValueError(f"Invalid prerequisite: {topic['id']} -> {other}")
        if any(a not in resources for a in topic["activities"]):
            raise ValueError(f"Unknown resource for {topic['id']}")
        source = topic["source"]
        if not 1 <= source["pages"][0] <= source["pages"][1]:
            raise ValueError("Invalid source page range.")
        check = topic["check"]
        if not 0 <= check["answer"] < len(check["options"]) or check["repair_topic"] not in by_id:
            raise ValueError(f"Invalid concept check for {topic['id']}")
    for activity in activities:
        if not 1 <= activity["minimum_minutes"] <= activity["minutes"]:
            raise ValueError("Invalid resource duration.")
    prerequisite_order(list(by_id), by_id)
    return by_id, resources


def blank_progress():
    return {"schema_version": SCHEMA, "ratings": {}, "completed": {}, "checks": {}, "errors": []}


def prerequisite_order(topic_ids, by_id):
    """Topological closure across both subjects and their mathematics foundations."""
    ordered, visited, visiting = [], set(), set()

    def visit(topic_id):
        if topic_id in visiting:
            raise ValueError("The required-prerequisite graph contains a cycle.")
        if topic_id in visited:
            return
        if topic_id not in by_id:
            raise ValueError(f"Unknown topic: {topic_id}")
        visiting.add(topic_id)
        for parent in by_id[topic_id]["required"]:
            visit(parent)
        visiting.remove(topic_id)
        visited.add(topic_id)
        ordered.append(topic_id)

    for item in topic_ids:
        visit(item)
    return ordered


def level(progress, topic_id):
    return progress.get("ratings", {}).get(topic_id, {}).get("level", 0)


def needs_review(progress, topic_id):
    check = progress.get("checks", {}).get(topic_id)
    return level(progress, topic_id) < 2 or bool(check and not check["correct"])


def gaps(topic_id, by_id, progress):
    return [t for t in prerequisite_order([topic_id], by_id)
            if t != topic_id and needs_review(progress, t)]


def next_gap(topic_id, by_id, progress):
    """Address an explicit difficulty before an unchecked topic, if both are ready."""
    missing = gaps(topic_id, by_id, progress)
    ready = [t for t in missing if all(not needs_review(progress, p) for p in by_id[t]["required"])]
    return next((t for t in ready if level(progress, t) == 1), (ready or missing or [None])[0])


def rate_topic(progress, topic_id, value, today):
    if type(value) is not int or value not in range(4):
        raise ValueError("Invalid confidence level.")
    old = progress["ratings"].get(topic_id, {})
    # Repeated clicks on one date must not stretch the suggested review interval.
    count = old.get("reviews", 0)
    if value >= 2 and old.get("date") != today.isoformat():
        count += 1
    progress["ratings"][topic_id] = {"level": value, "date": today.isoformat(), "reviews": count}


def due_topics(progress, by_id, today):
    due = []
    for topic_id, rating in progress["ratings"].items():
        if topic_id not in by_id or rating["level"] < 2:
            continue
        interval = (1, 3, 7, 14)[min(max(rating.get("reviews", 1) - 1, 0), 3)]
        if rating["level"] == 2:
            interval = 1
        review_date = date.fromisoformat(rating["date"]) + timedelta(days=interval)
        if review_date <= today:
            due.append((topic_id, review_date))
    return sorted(due, key=lambda pair: (pair[1], pair[0]))


def activity_key(topic_id, resource_id, role="practice"):
    return f"{topic_id}|{resource_id}|{role}"


def resource_url(topic, activity):
    """Optional instructor-supplied URLs; never invent resource links."""
    url = topic.get("resource_urls", {}).get(activity["id"], "")
    parsed = urlsplit(url)
    return url if parsed.scheme == "https" and parsed.netloc and not parsed.username else ""


def build_session(topic_id, by_id, resources, progress, minutes=60,
                  goal=GOALS[0], confidence="Medium", challenge=CHALLENGES[0],
                  include_prerequisites=True):
    """Fit meaningful blocks in a hard time budget and always reserve retrieval time.

    Completion never changes the ordering or a topic rating: stable IDs prevent
    an unrelated checkbox from being re-used when time, goal or topic changes.
    """
    if type(minutes) is not int or minutes < 10 or minutes > 240:
        raise ValueError("A study session must be between 10 and 240 minutes.")
    topic = by_id[topic_id]
    available = set(topic["activities"])
    plan, remaining = [], minutes
    exit_time = 3 if minutes < 30 else 5
    remaining -= exit_time
    missing = gaps(topic_id, by_id, progress) if include_prerequisites else []
    last_check = progress.get("checks", {}).get(topic_id)
    repair = (topic["check"]["repair_topic"] if last_check and not last_check["correct"] else None)
    if include_prerequisites and repair and repair != topic_id and repair not in missing:
        missing.insert(0, repair)

    def append(resource_id, target_id, duration, role, reason, title=None):
        activity = resources[resource_id]
        target = by_id[target_id]
        block = dict(activity, topic_id=target_id, minutes=duration, role=role,
                     key=activity_key(target_id, resource_id, role), reason=reason,
                     title=title or activity["title"], topic_title=target["title"])
        if resource_id == "LN":
            block["guidance"] = f"{target['practice_prompt']} {activity['guidance']}"
        plan.append(block)

    if missing:
        target_id = repair if repair and repair != topic_id else next_gap(topic_id, by_id, progress)
        duration = min(12, max(4, math.floor(minutes * .17)))
        # Keep room for at least a short worked-example attempt and retrieval.
        duration = min(duration, max(0, remaining - resources["LN"]["minimum_minutes"]))
        if duration >= 4:
            append("LN", target_id, duration, "prerequisite",
                   ("Your latest concept check flagged this connection. Revisit the idea, then attempt a fresh problem."
                    if repair == target_id else "This required building block is unchecked or needs practice. Today targets one gap; other gaps may remain."),
                   f"Reconnect: {by_id[target_id]['short_title']}")
            remaining -= duration

    support = {"Choosing a method": "QG", "Drawing the diagram": "SBS",
               "Maths or signs": "APP", "Starting a question": "SBS",
               "Checking my answer": "SIA"}.get(challenge)
    if not support and repair:
        support = "QG"
    if not support and confidence == "Low":
        support = "SBS"
    if goal == "Prepare for a lecture":
        candidates = ["QG", "LN", "T"]
    elif goal in ("Independent practice", "Quiz or exam revision") and confidence == "High":
        candidates = ["H", "T", "LN"]
    elif goal == "Quiz or exam revision":
        candidates = ["T", "H", "LN"]
    else:
        candidates = ["LN", "T", "H"]
    if support in available and support not in candidates:
        # Support follows an initial attempt, and precedes the next practice block.
        candidates.insert(2 if candidates[0] == "QG" else 1, support)
    explanations = {
        "QG": "A short overview helps you choose a method; close it before the next problem.",
        "LN": "Re-solving a worked example exposes the first step you cannot yet explain.",
        "T": "Tutorial practice turns the example method into a solution you can write yourself.",
        "H": "An independent attempt tests transfer to a question without prompts.",
        "SBS": "Use a short explanation for the diagram or starting step, then return to practice.",
        "APP": "Make a prediction and check the specific sign, quantity or relationship that is unclear.",
        "SIA": "Compare video reasoning with your attempted solution; then re-solve without the video.",
    }
    for resource_id in dict.fromkeys(candidates):
        if resource_id not in available:
            continue
        item = resources[resource_id]
        if remaining < item["minimum_minutes"]:
            continue
        duration = min(item["minutes"], remaining)
        append(resource_id, topic_id, duration, "practice", explanations[resource_id])
        remaining -= duration
    # Extra minutes deepen active work instead of adding every optional resource.
    core = [b for b in plan if b["topic_id"] == topic_id and b["id"] in ("LN", "T", "H")]
    if core and remaining:
        core[-1]["minutes"] += remaining
        remaining = 0
    append("EXIT", topic_id, exit_time, "practice",
           "Finish with closed-book retrieval. Update your topic rating only from what you can actually do.")
    return {"blocks": plan, "gaps": missing, "unused": remaining,
            "minutes": sum(b["minutes"] for b in plan), "budget": minutes}


def build_week(topic_ids, by_id, resources, progress, start, weekdays, daily_minutes, goal=GOALS[0]):
    """Prerequisite-first route with hard daily capacity and a visible backlog.

    Scheduling an activity does not assert that the prerequisite is mastered.
    Each new study day includes a short retrieval revisit when capacity allows.
    """
    if not topic_ids or not weekdays:
        return {"days": [], "backlog": [], "route": [], "capacity": 0, "minutes": 0}
    if type(daily_minutes) is not int or not 15 <= daily_minutes <= 180:
        raise ValueError("Daily study time must be 15 to 180 minutes.")
    if any(type(day) is not int or day not in range(7) for day in weekdays):
        raise ValueError("Invalid weekday selection.")
    dates = [start + timedelta(days=i) for i in range(7)
             if (start + timedelta(days=i)).weekday() in weekdays]
    route = [t for t in prerequisite_order(topic_ids, by_id)
             if t in topic_ids or needs_review(progress, t)]
    queue = []
    for t in route:
        # A weekly route includes an independent attempt, even when its blocks
        # have to continue on the next chosen study day.
        budget = 25 if by_id[t]["area"] == "Foundations" else 70
        session = build_session(t, by_id, resources, progress, budget, goal=goal,
                                confidence="Low" if level(progress, t) == 1 else "High" if level(progress, t) == 3 else "Medium",
                                include_prerequisites=False)
        queue.extend(deepcopy(session["blocks"]))
    days, studied = [], []
    due = [t for t, _ in due_topics(progress, by_id, start)]
    for day_index, day in enumerate(dates):
        blocks, left = [], daily_minutes
        revisit = studied[-1] if studied else (due[0] if due else None)
        if revisit and left >= 15:
            blocks.append(dict(resources["EXIT"], topic_id=revisit,
                               topic_title=by_id[revisit]["title"], minutes=5,
                               title="Spaced recall", role="review",
                               key=f"{revisit}|EXIT|review", reason="Retrieve an earlier method before new practice.",
                               guidance="With notes closed, outline a problem method from the earlier topic. If it is unclear, adjust the next session before progressing."))
            left -= 5
            if not studied and due:
                due.pop(0)
        while queue and left >= queue[0]["minimum_minutes"]:
            item = queue.pop(0)
            item["minutes"] = min(item["minutes"], left)
            left -= item["minutes"]
            blocks.append(item)
            if item["id"] == "EXIT" and item["role"] == "practice":
                studied.append(item["topic_id"])
        # Once the first route is scheduled, give later days meaningful transfer
        # practice, rather than filling a day with passive support materials.
        if not queue and left >= 25:
            focus = topic_ids[day_index % len(topic_ids)]
            resource_id = "H" if "H" in by_id[focus]["activities"] else "LN"
            if not any(b["topic_id"] == focus and b["id"] == resource_id for b in blocks):
                duration = min(30, left - 5)
                blocks.append(dict(resources[resource_id], topic_id=focus,
                                   topic_title=by_id[focus]["title"], minutes=duration,
                                   title="Fresh independent attempt" if resource_id == "H" else "Re-solve with notes closed",
                                   role="review", key=activity_key(focus, resource_id, "review"),
                                   reason="Test transfer after the first learning route; revisit foundations if you need help."))
                blocks.append(dict(resources["EXIT"], topic_id=focus,
                                   topic_title=by_id[focus]["title"], minutes=5,
                                   role="review", key=activity_key(focus, "EXIT", "review"),
                                   reason="Explain what changed between the earlier attempt and this one."))
                left -= duration + 5
        if blocks:
            days.append({"date": day.isoformat(), "blocks": blocks,
                         "minutes": sum(b["minutes"] for b in blocks), "unused": left})
    return {"days": days, "backlog": queue, "route": route,
            "capacity": len(dates) * daily_minutes,
            "minutes": sum(d["minutes"] for d in days)}


def validate_progress(raw, by_id, resources):
    """Validate untrusted browser storage/backups; never execute imported content."""
    if not isinstance(raw, dict) or raw.get("schema_version") != SCHEMA:
        raise ValueError("Choose an EG1011 progress backup from this version of the app.")
    clean = blank_progress()

    def day(value):
        if not isinstance(value, str):
            raise ValueError("A saved date is invalid.")
        date.fromisoformat(value)
        return value

    for section in ("ratings", "completed", "checks"):
        if not isinstance(raw.get(section), dict) or len(raw[section]) > 2000:
            raise ValueError("The progress backup has an invalid section.")
    for t, rating in raw["ratings"].items():
        if t not in by_id or not isinstance(rating, dict):
            raise ValueError("The backup contains an unknown topic.")
        value, reviews = rating.get("level"), rating.get("reviews", 0)
        if type(value) is not int or value not in range(4) or type(reviews) is not int or not 0 <= reviews <= 10000:
            raise ValueError("The backup contains an invalid topic rating.")
        clean["ratings"][t] = {"level": value, "reviews": reviews, "date": day(rating.get("date"))}
    for key, record in raw["completed"].items():
        parts = key.split("|")
        if len(parts) != 3 or parts[0] not in by_id or parts[1] not in resources or parts[2] not in ("practice", "prerequisite", "review"):
            raise ValueError("The backup contains an unknown activity.")
        if not isinstance(record, dict) or type(record.get("minutes")) is not int or not 0 < record["minutes"] <= 240:
            raise ValueError("The backup contains an invalid activity duration.")
        clean["completed"][key] = {"date": day(record.get("date")), "minutes": record["minutes"]}
    for t, check in raw["checks"].items():
        if t not in by_id or not isinstance(check, dict) or type(check.get("correct")) is not bool:
            raise ValueError("The backup contains an invalid concept check.")
        answer = check.get("answer")
        if type(answer) is not int or answer not in range(len(by_id[t]["check"]["options"])):
            raise ValueError("The backup contains an invalid concept answer.")
        clean["checks"][t] = {"correct": answer == by_id[t]["check"]["answer"],
                               "answer": answer, "date": day(check.get("date"))}
    errors = raw.get("errors", [])
    if not isinstance(errors, list) or len(errors) > 100:
        raise ValueError("The backup contains too many error notes.")
    for note in errors:
        if not isinstance(note, dict) or note.get("topic_id") not in by_id:
            raise ValueError("An error note has an unknown topic.")
        text = note.get("text")
        if not isinstance(text, str) or len(text) > 800:
            raise ValueError("An error note is too long.")
        clean["errors"].append({"topic_id": note["topic_id"], "text": text, "date": day(note.get("date"))})
    return clean


def progress_json(progress):
    return json.dumps(progress, ensure_ascii=False, indent=2)


def csv_plan(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(("Date / order", "Topic", "Resource", "Minutes", "Purpose", "Instructions"))
    for label, block in rows:
        cells = [label, block["topic_title"], block["title"], block["minutes"], block["reason"], block["guidance"]]
        # Guard spreadsheet formula interpretation if an instructor edits text later.
        writer.writerow(["'" + str(c) if str(c).startswith(("=", "+", "-", "@")) else c for c in cells])
    return output.getvalue().encode("utf-8-sig")


def calendar_file(week, stamp):
    """All-day calendar entries: no guessed class dates, times or time zones."""
    def escape(text):
        return str(text).replace("\\", "\\\\").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//EG1011//Study Navigator//EN", "CALSCALE:GREGORIAN"]
    for day in week["days"]:
        when = date.fromisoformat(day["date"])
        description = "\n".join(f"{b['minutes']} min - {b['topic_title']}: {b['title']}. {b['guidance']}" for b in day["blocks"])
        lines.extend(["BEGIN:VEVENT", f"UID:eg1011-{when.isoformat()}-{stamp}@study-navigator",
                      f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{when:%Y%m%d}",
                      f"DTEND;VALUE=DATE:{when + timedelta(days=1):%Y%m%d}",
                      f"SUMMARY:{escape('EG1011 study - ' + str(day['minutes']) + ' min')}",
                      f"DESCRIPTION:{escape(description)}", "END:VEVENT"])
    lines.append("END:VCALENDAR")
    # RFC 5545 folds lines at 75 octets, without splitting UTF-8 code points.
    folded = []
    for line in lines:
        current = ""
        for char in line:
            if len((current + char).encode("utf-8")) > 75:
                folded.append(current)
                current = " "
            current += char
        folded.append(current)
    return ("\r\n".join(folded) + "\r\n").encode("utf-8")
