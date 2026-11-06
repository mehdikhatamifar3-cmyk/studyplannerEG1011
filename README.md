# EG1011 Study Navigator

A planning-only Streamlit app. It does not host or link to course resources. Students continue to access all lecture notes, QuickGuides, tutorial questions, videos, Step by Step with Mehdi PDFs, and interactive apps through the existing EG1011 website.

## Features

- personalised planning by topic, goal, confidence, and available time
- prerequisite review warnings
- separate importance and difficulty indicators
- Statics and Dynamics roadmaps
- weekly and catch-up pathways
- session-based progress checkboxes
- downloadable planning checklist

## Run

```bash
python -m venv .venv
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Upload the folder contents to a GitHub repository. In Streamlit Community Cloud, select the repository, branch, and `app.py` as the entry point.

## Edit the plan

- `data/topics.json` controls topic descriptions, outcomes, sessions, prerequisites, and activity order.
- `data/study_activities.json` controls activity names, importance, time, difficulty, and student instructions.

The app contains no course files, resource URLs, student names, IDs, grades, passwords, or permanent progress database.
