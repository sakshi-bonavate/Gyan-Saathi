"""
pages/teacher.py – Teacher dashboard.
"""

import json
import streamlit as st

import database as db
from ui import inject_css, mascot_say

inject_css()

SKILL_NAMES = {
    "counting":            "Counting",
    "addition":            "Addition",
    "subtraction":         "Subtraction",
    "multiplication":      "Multiplication",
    "division":            "Division",
    "fractions_basic":     "Fractions – Basics",
    "fractions_compare":   "Comparing Fractions",
    "fractions_add":       "Adding Fractions",
    "fractions_subtract":  "Subtracting Fractions",
    "fractions_of_number": "Fractions of a Number",
}

SAMPLE_STUDENTS = [
    {"name": "Aisha",   "mastery": {"fractions_basic": 40, "fractions_add": 20,       "addition": 80,       "counting": 90}},
    {"name": "Raju",    "mastery": {"fractions_basic": 70, "fractions_compare": 30,    "subtraction": 60,    "counting": 100}},
    {"name": "Meena",   "mastery": {"fractions_basic": 90, "fractions_add": 80,        "multiplication": 50, "counting": 100}},
    {"name": "Suresh",  "mastery": {"fractions_basic": 30, "fractions_subtract": 20,   "division": 40,       "counting": 80}},
    {"name": "Priya",   "mastery": {"fractions_basic": 60, "fractions_of_number": 30,  "addition": 90,       "counting": 100}},
    {"name": "Govind",  "mastery": {"fractions_basic": 50, "fractions_add": 40,        "subtraction": 70,    "counting": 90}},
    {"name": "Kavitha", "mastery": {"fractions_basic": 80, "fractions_compare": 50,    "multiplication": 60, "counting": 100}},
    {"name": "Deepak",  "mastery": {"fractions_basic": 20, "fractions_add": 10,        "division": 30,       "counting": 70}},
    {"name": "Lalita",  "mastery": {"fractions_basic": 75, "fractions_subtract": 55,   "addition": 85,       "counting": 95}},
    {"name": "Mohan",   "mastery": {"fractions_basic": 45, "fractions_of_number": 25,  "subtraction": 55,    "counting": 80}},
    {"name": "Sunita",  "mastery": {"fractions_basic": 65, "fractions_compare": 45,    "multiplication": 70, "counting": 90}},
    {"name": "Vikram",  "mastery": {"fractions_basic": 35, "fractions_add": 30,        "division": 50,       "counting": 75}},
    {"name": "Padma",   "mastery": {"fractions_basic": 85, "fractions_subtract": 75,   "addition": 95,       "counting": 100}},
    {"name": "Rahul",   "mastery": {"fractions_basic": 55, "fractions_of_number": 40,  "subtraction": 65,    "counting": 85}},
    {"name": "Nandita", "mastery": {"fractions_basic": 25, "fractions_compare": 15,    "multiplication": 45, "counting": 65}},
]


def _get_weakness_data():
    skill_wrong = {s: 0 for s in SKILL_NAMES}
    skill_total = {s: 0 for s in SKILL_NAMES}
    for student in SAMPLE_STUDENTS:
        for skill, score in student["mastery"].items():
            if skill in skill_wrong:
                skill_wrong[skill] += (100 - score)
                skill_total[skill] += 1
    real_data = db.get_skill_weakness_summary()
    for skill, wrong in real_data.items():
        if skill in skill_wrong:
            skill_wrong[skill] += wrong * 15
            skill_total[skill] += 1
    return {s: round(skill_wrong[s] / skill_total[s]) for s in SKILL_NAMES if skill_total[s] > 0}


def _students_needing_attention():
    attention = []
    for s in SAMPLE_STUDENTS:
        weak = {sk: sc for sk, sc in s["mastery"].items() if sc < 50}
        if weak:
            weakest = min(weak, key=weak.get)
            attention.append({"name": s["name"], "skill": SKILL_NAMES.get(weakest, weakest),
                               "score": weak[weakest], "source": "sample"})
    for sess in db.get_all_sessions():
        mastery = json.loads(sess["mastery"]) if sess["mastery"] else {}
        weak = {sk: sc for sk, sc in mastery.items() if sc < 50}
        if weak:
            weakest = min(weak, key=weak.get)
            attention.append({"name": sess["student"], "skill": SKILL_NAMES.get(weakest, weakest),
                               "score": weak[weakest], "source": "real"})
    attention.sort(key=lambda x: x["score"])
    return attention


def show():
    st.html("<h2>📊 Teacher Dashboard</h2>")
    mascot_say("Here's how your class is doing! Focus on the orange bars. 🦉")

    st.html(
        '<div class="card card-yellow" style="font-size:16px">'
        '⚠️ <b>Note:</b> Includes <b>sample/demo data</b> for 15 fictional students '
        'plus any real quiz results stored on this device.'
        '</div>'
    )
    st.html("<br>")

    # ── Weak Topics Chart ─────────────────────────────────────────────────────
    st.html("<h3>📉 Weak Topics Across the Class</h3>")
    st.html("<div style='font-size:15px;color:#888;margin-bottom:12px'>Higher bar = more students struggling</div>")

    weakness = _get_weakness_data()
    if weakness:
        max_val = max(weakness.values()) or 1
        bars = ""
        for skill, val in weakness.items():
            label = SKILL_NAMES.get(skill, skill)
            pct   = int(val / max_val * 100)
            color = "#FF9F43" if val > 60 else "#FFC83D" if val > 30 else "#3DD598"
            bars += f"""
<div style="margin-bottom:12px">
  <div style="display:flex;justify-content:space-between;font-size:16px;font-weight:700;margin-bottom:4px">
    <span>{label}</span><span style="color:{color}">{val}</span>
  </div>
  <div style="background:#F0E6D0;border-radius:20px;height:22px">
    <div style="background:{color};width:{pct}%;height:100%;border-radius:20px;min-width:8px"></div>
  </div>
</div>"""
        st.html(f"<div style='margin-bottom:20px'>{bars}</div>")

        weakest_skill = max(weakness, key=weakness.get)
        st.html(f"""
<div class="card card-orange">
  🔴 <b>Most challenging topic:</b> {SKILL_NAMES.get(weakest_skill, weakest_skill)}<br>
  <span style="font-size:17px">Consider spending extra class time here.</span>
</div>""")

    st.html("<br>")

    # ── Students needing attention ────────────────────────────────────────────
    st.html("<h3>🚨 Students Needing Attention</h3>")
    st.html("<div style='font-size:15px;color:#888;margin-bottom:12px'>Scored below 50% in at least one skill</div>")

    at_risk = _students_needing_attention()
    if not at_risk:
        st.html('<div class="good">🎉 All students are doing well! No one below 50%.</div>')
    else:
        rows = ""
        for student in at_risk[:12]:
            badge_color = "#FF9F43" if student["score"] < 30 else "#FFC83D"
            src_bg  = "#ddd"  if student["source"] == "sample" else "#4DA8FF"
            src_col = "#333"  if student["source"] == "sample" else "#fff"
            rows += f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            background:#fff;border:2px solid {badge_color};border-radius:20px;
            padding:12px 18px;margin-bottom:8px">
  <span style="font-size:19px;font-weight:800">{student['name']}</span>
  <span style="font-size:12px;background:{src_bg};color:{src_col};border-radius:8px;padding:2px 7px">{student['source']}</span>
  <span style="font-size:17px;color:#555">Weak: <b>{student['skill']}</b></span>
  <span style="font-size:20px;font-weight:800;color:{badge_color}">{student['score']}%</span>
</div>"""
        st.html(f"<div>{rows}</div>")

    st.html("<br>")

    # ── Real quiz sessions ────────────────────────────────────────────────────
    real_sessions = [s for s in db.get_all_sessions() if s.get("student")]
    if real_sessions:
        st.html("<h3>📋 Recent Real Quiz Sessions</h3>")
        rows = ""
        for sess in real_sessions[:10]:
            mastery  = json.loads(sess["mastery"]) if sess["mastery"] else {}
            avg      = round(sum(mastery.values()) / len(mastery)) if mastery else 0
            date_str = sess["finished_at"][:10] if sess["finished_at"] else "?"
            rows += f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            background:#fff;border:2px solid #4DA8FF;border-radius:16px;
            padding:10px 16px;margin-bottom:6px;font-size:17px">
  <b>{sess.get('avatar') or '🐯'} {sess['student']}</b>
  <span>⭐ {sess.get('stars', 0)}</span>
  <span>📊 {avg}%</span>
  <span style="color:#aaa;font-size:14px">{date_str}</span>
</div>"""
        st.html(f"<div>{rows}</div>")
