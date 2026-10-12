"""
pages/student.py – Diagnostic quiz page for Gyan Saathi.

Adaptive logic:
  - Pulls questions from questions.json in order.
  - Wrong answer → next question is drawn from the prerequisite_skill (easier).
  - Tracks mastery per skill (correct/total).
  - Gamification: +10 stars per correct answer, st.balloons() on 3-streak.
  - Saves every response to SQLite via database.py.
"""

import json
import random
import os
import streamlit as st

import database as db
from ui import (
    inject_css, mascot_say, fraction_svg, show_fraction_svg,
    progress_road, star_counter, badge_grid, speak_button,
    OPTION_COLORS, BADGE_DEFS,
)

inject_css()

# ── Load questions ────────────────────────────────────────────────────────────

@st.cache_data
def load_questions():
    path = os.path.join(os.path.dirname(__file__), "..", "questions.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

ALL_QS = load_questions()
QUIZ_SIZE = 8  # questions per session

# Skill display names
SKILL_NAMES = {
    "counting":           "Counting",
    "addition":           "Addition",
    "subtraction":        "Subtraction",
    "multiplication":     "Multiplication",
    "division":           "Division",
    "fractions_basic":    "Fractions – Basics",
    "fractions_compare":  "Comparing Fractions",
    "fractions_add":      "Adding Fractions",
    "fractions_subtract": "Subtracting Fractions",
    "fractions_of_number":"Fractions of a Number",
}

# ── State helpers ─────────────────────────────────────────────────────────────

def _init_quiz():
    """Initialise quiz state for a fresh attempt."""
    user = st.session_state.get("user", {})

    # Start with one question from each skill group, difficulty 1 or 2
    starter = [q for q in ALL_QS if q["difficulty"] <= 2]
    random.shuffle(starter)
    queue = starter[:QUIZ_SIZE]

    st.session_state["quiz"] = {
        "queue":       queue,
        "index":       0,
        "answers":     [],        # list of {q, correct}
        "mastery":     {},        # {skill: [correct, total]}
        "stars_earned":0,
        "streak":      0,
        "done":        False,
        "last_correct": None,
        "hint_shown":  False,
        "session_id":  db.start_session(
            student=user.get("display_name", "Guest"),
            avatar=user.get("avatar", "🐯"),
            user_id=user.get("id"),
        ),
    }


def _q_state():
    return st.session_state["quiz"]


# ── Fraction detection ────────────────────────────────────────────────────────

def _parse_fraction(text: str):
    """Return (n, d) if text looks like 'n/d', else None."""
    import re
    m = re.match(r"^(\d+)/(\d+)$", text.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _question_has_fraction(q: dict) -> tuple | None:
    """If the question mentions an obvious fraction like '1/4', return (n,d)."""
    import re
    fracs = re.findall(r"\b(\d+)/(\d+)\b", q["question"])
    if fracs:
        return int(fracs[0][0]), int(fracs[0][1])
    return None


# ── Main render ───────────────────────────────────────────────────────────────

def show():
    if "quiz" not in st.session_state or st.session_state["quiz"].get("done") is False and st.session_state["quiz"].get("index", 0) == 0 and not st.session_state["quiz"].get("answers"):
        pass  # already initialised by nav

    if "quiz" not in st.session_state:
        _init_quiz()

    qs = _q_state()

    if qs["done"]:
        _show_results(qs)
        return

    queue = qs["queue"]
    idx   = qs["index"]

    if idx >= len(queue):
        qs["done"] = True
        _finalise(qs)
        st.rerun()
        return

    q = queue[idx]
    lang = st.session_state.get("lang", "English")

    # ── Header ────────────────────────────────────────────────────────────────
    st.html("<h2>🎯 Play Quiz</h2>")
    user = st.session_state.get("user", {})
    star_counter(
        user.get("stars", 0) + qs["stars_earned"],
        streak=qs["streak"],
    )

    progress_road(idx + 1, len(queue), user.get("avatar", "🐯"))

    # ── Feedback from last answer ─────────────────────────────────────────────
    if qs.get("last_correct") is True:
        st.html('<div class="good">🎉 Shabash! That\'s correct! +10 ⭐</div>')
        qs["last_correct"] = None
    elif qs.get("last_correct") is False:
        st.html(
            '<div class="tryagain">💪 Almost! Let\'s try an easier one — you\'ve got this!</div>')
        qs["last_correct"] = None

    st.html("<br>")

    # ── Question card ─────────────────────────────────────────────────────────
    frac = _question_has_fraction(q)
    with st.container():
        st.html(
            f'<div class="card"><span style="font-size:13px;color:#aaa;font-weight:700">'
            f'Skill: {SKILL_NAMES.get(q["skill"], q["skill"])}</span>'
            f'<h3 style="margin-top:8px">{q["question"]}</h3></div>')

    # Show fraction SVG if relevant
    if frac and q["skill"] in ("fractions_basic", "fractions_compare",
                                "fractions_add", "fractions_subtract",
                                "fractions_of_number"):
        col_sv, _ = st.columns([1, 2])
        with col_sv:
            show_fraction_svg(frac[0], frac[1], size=130)

    speak_button(q["question"], language=lang, key=f"spk_q_{idx}")

    # ── Answer options (2×2 grid) ─────────────────────────────────────────────
    # Inject per-option color CSS once per question render using st.html
    opt_css = ""
    options = q["options"]
    for i, opt in enumerate(options):
        bg, border, text_color = OPTION_COLORS[i % 4]
        opt_css += (
            f'div[data-testid="stButton"]:has(button[data-testid="baseButton-secondary"]:nth-child(1)) > button {{}}'
        )
    # Use a single consolidated CSS block via st.html (not st.markdown) to avoid stripping
    st.html(f"""<style>
      /* option A */ div[data-testid="column"]:nth-child(1) button {{
        background:{OPTION_COLORS[0][0]}!important;border:4px solid {OPTION_COLORS[0][1]}!important;color:{OPTION_COLORS[0][2]}!important;
      }}
      /* option B */ div[data-testid="column"]:nth-child(2) button {{
        background:{OPTION_COLORS[1][0]}!important;border:4px solid {OPTION_COLORS[1][1]}!important;color:{OPTION_COLORS[1][2]}!important;
      }}
    </style>""")

    col1, col2 = st.columns(2)
    cols = [col1, col2, col1, col2]

    for i, opt in enumerate(options):
        with cols[i]:
            if st.button(
                opt,
                key=f"opt_{idx}_{i}",
                use_container_width=True,
            ):
                _handle_answer(qs, q, opt, idx)
                st.rerun()

    # ── Language toggle ───────────────────────────────────────────────────────
    st.html("<br>")
    lang_col1, lang_col2 = st.columns(2)
    with lang_col1:
        if st.button("🇬🇧 English", key="lq_en", use_container_width=True):
            st.session_state["lang"] = "English"
            st.rerun()
    with lang_col2:
        if st.button("🇮🇳 हिन्दी", key="lq_hi", use_container_width=True):
            st.session_state["lang"] = "Hindi"
            st.rerun()


# ── Answer handling ───────────────────────────────────────────────────────────

def _handle_answer(qs: dict, q: dict, chosen: str, idx: int):
    correct = (chosen.strip() == q["answer"].strip())

    # Record in DB
    db.record_response(
        session_id=qs["session_id"],
        question_id=q["id"],
        skill=q["skill"],
        difficulty=q["difficulty"],
        correct=correct,
    )

    # Mastery tracking
    skill = q["skill"]
    if skill not in qs["mastery"]:
        qs["mastery"][skill] = [0, 0]
    qs["mastery"][skill][1] += 1
    if correct:
        qs["mastery"][skill][0] += 1

    qs["answers"].append({"q": q, "correct": correct})
    qs["last_correct"] = correct

    if correct:
        qs["stars_earned"] += 10
        qs["streak"] += 1
        if qs["streak"] % 3 == 0:
            st.balloons()
        qs["index"] += 1
    else:
        qs["streak"] = 0
        # Adaptive: insert a prerequisite-skill question next
        prereq_skill = q.get("prerequisite_skill", q["skill"])
        prereq_qs = [
            pq for pq in ALL_QS
            if pq["skill"] == prereq_skill
            and pq["id"] != q["id"]
            and pq not in qs["queue"]
        ]
        if prereq_qs:
            insert_q = random.choice(prereq_qs)
            new_queue = qs["queue"][:idx + 1] + [insert_q] + qs["queue"][idx + 1:]
            qs["queue"] = new_queue
        qs["index"] += 1

    # End quiz when we've consumed all queued questions
    if qs["index"] >= len(qs["queue"]):
        qs["done"] = True
        _finalise(qs)


def _finalise(qs: dict):
    """Compute mastery scores, award badges, persist to DB."""
    mastery_scores = {}
    for skill, (right, total) in qs["mastery"].items():
        mastery_scores[skill] = round(right / total * 100) if total else 0

    db.finish_session(qs["session_id"], qs["stars_earned"], mastery_scores)

    # Update user stars + badges in DB
    user = st.session_state.get("user", {})
    if user.get("id"):
        existing_stars = user.get("stars", 0)
        existing_badges = json.loads(user.get("badges", "[]")) if isinstance(user.get("badges"), str) else user.get("badges", [])

        new_stars = existing_stars + qs["stars_earned"]
        new_badges = list(existing_badges)

        # Award badges
        total_correct = sum(1 for a in qs["answers"] if a["correct"])
        if "Fraction Explorer" not in new_badges:
            new_badges.append("Fraction Explorer")
        if total_correct >= 5 and "5 in a Row" not in new_badges:
            new_badges.append("5 in a Row")
        if "fractions_basic" in mastery_scores and mastery_scores["fractions_basic"] == 100 and "Pizza Master" not in new_badges:
            new_badges.append("Pizza Master")
        if total_correct >= 4 and mastery_scores and max(mastery_scores.values()) >= 80 and "Math Wizard" not in new_badges:
            new_badges.append("Math Wizard")

        db.update_user_stars_badges(user["id"], new_stars, new_badges)
        user["stars"]  = new_stars
        user["badges"] = new_badges
        st.session_state["user"] = user

    qs["mastery_scores"] = mastery_scores


# ── Results screen ────────────────────────────────────────────────────────────

def _show_results(qs: dict):
    import json as _json

    st.balloons()
    st.html("<h2 style='text-align:center'>🎊 Quiz Complete!</h2>")

    mastery = qs.get("mastery_scores", {})
    if not mastery:
        mastery = {skill: round(right/total*100) if total else 0
                   for skill, (right, total) in qs.get("mastery", {}).items()}

    stars = qs["stars_earned"]
    total_q = len(qs["answers"])
    total_right = sum(1 for a in qs["answers"] if a["correct"])

    # Positive framing
    strong = [SKILL_NAMES.get(s, s) for s, sc in mastery.items() if sc >= 70]
    weak   = [SKILL_NAMES.get(s, s) for s, sc in mastery.items() if sc < 70]

    if strong:
        mascot_say(f"You are STRONG in: {', '.join(strong)}! 🔥 Keep it up!")
    else:
        mascot_say("Great effort! Every try makes you smarter! 💪")

    st.html(f"""
<div class="good" style="text-align:center;font-size:26px">
  ⭐ You earned <b>{stars} stars</b>!<br>
  ✅ {total_right} out of {total_q} correct
</div>""")

    st.html("<br>")

    if weak:
        st.html(f"""
<div class="card card-yellow">
  🗺️ <b>Your next adventure:</b> {', '.join(weak)}<br>
  <span style="font-size:17px">Visit <b>Ask Chhotu</b> to practice these!</span>
</div>""")

    # Per-skill breakdown
    st.html("<h3>📊 Your skill map</h3>")
    for skill, score in mastery.items():
        color = "#3DD598" if score >= 70 else "#FF9F43"
        label = SKILL_NAMES.get(skill, skill)
        st.html(f"""
<div style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;font-weight:800;font-size:18px">
    <span>{label}</span><span style="color:{color}">{score}%</span>
  </div>
  <div style="background:#F0E6D0;border-radius:20px;height:18px">
    <div style="background:{color};width:{score}%;height:100%;border-radius:20px;transition:width .5s ease"></div>
  </div>
</div>""")

    st.html("<br>")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 Play Again", key="quiz_again"):
            del st.session_state["quiz"]
            _init_quiz()
            st.rerun()
    with col_b:
        if st.button("💬 Ask Chhotu", key="goto_tutor"):
            st.session_state["page"] = "tutor"
            st.rerun()
