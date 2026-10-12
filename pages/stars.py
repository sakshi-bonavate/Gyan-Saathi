"""
pages/stars.py – "My Stars" gamification page.

Shows:
  • Stars counter + streak
  • Badge sticker collection (earned vs locked)
  • Quiz history summary
"""

import json
import streamlit as st

import database as db
from ui import inject_css, mascot_say, star_counter, badge_grid, BADGE_DEFS

inject_css()

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


def show():
    user = st.session_state.get("user", {})
    stars  = user.get("stars", 0)
    streak = user.get("streak", 0)
    badges_raw = user.get("badges", "[]")
    earned = json.loads(badges_raw) if isinstance(badges_raw, str) else badges_raw

    st.html("<h2>⭐ My Stars</h2>")

    if stars >= 50:
        mascot_say("You're on fire! Keep collecting those stars! 🔥")
    elif stars >= 20:
        mascot_say("Great work! You've earned lots of stars! ⭐")
    else:
        mascot_say("Play the quiz to earn stars and unlock badges! 🌟")

    # ── Stars + streak ────────────────────────────────────────────────────────
    st.html(f"""
<div class="card card-yellow" style="text-align:center">
  <div style="font-size:60px">⭐</div>
  <div style="font-size:42px;font-weight:800;font-family:'Baloo 2',cursive;color:#FFA500">
    {stars} Stars
  </div>
  {'<div style="font-size:24px;margin-top:8px">🔥 ' + str(streak) + ' day streak!</div>' if streak > 0 else ''}
</div>""")

    st.html("<br>")

    # ── Badges ────────────────────────────────────────────────────────────────
    st.html("<h3>🏅 My Badges</h3>")
    st.html(
        "<div style='font-size:17px;color:#7A5500;margin-bottom:12px'>"
        "Collect badges by completing quizzes and getting answers right!</div>")

    badge_grid(earned)

    # Show locked hint
    locked_count = len(BADGE_DEFS) - len(earned)
    if locked_count > 0:
        st.html(
            f'<div style="font-size:16px;color:#aaa;margin-top:8px">'
            f'🔒 {locked_count} badge{"s" if locked_count>1 else ""} still to unlock!</div>')

    st.html("<br>")

    # ── Past quiz history ─────────────────────────────────────────────────────
    st.html("<h3>📜 My Quiz History</h3>")

    all_sessions = db.get_all_sessions()
    # Filter to this user's sessions
    user_id = user.get("id")
    my_sessions = [
        s for s in all_sessions
        if s.get("user_id") == user_id or s.get("student") == user.get("display_name")
    ]

    if not my_sessions:
        st.html(
            '<div class="card card-blue" style="text-align:center;font-size:20px">'
            '🎯 You haven\'t finished a quiz yet!<br>'
            '<b>Play the Quiz</b> to see your history here.</div>')
    else:
        for i, sess in enumerate(my_sessions[:5]):  # last 5
            mastery = json.loads(sess["mastery"]) if sess["mastery"] else {}
            avg_score = round(sum(mastery.values()) / len(mastery)) if mastery else 0
            date_str = sess["finished_at"][:10] if sess["finished_at"] else "?"
            s_stars = sess.get("stars", 0)

            color = "card-green" if avg_score >= 70 else "card-orange"
            st.html(f"""
<div class="card {color}" style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-weight:800;font-size:18px">Quiz #{len(my_sessions)-i}</span>
    <span style="font-size:16px;color:#888">{date_str}</span>
  </div>
  <div style="font-size:20px;margin-top:6px">⭐ {s_stars} stars &nbsp;|&nbsp; 📊 Avg score: {avg_score}%</div>
  <div style="font-size:16px;color:#555;margin-top:4px">
    Skills: {', '.join(SKILL_NAMES.get(sk, sk) for sk in mastery.keys())}
  </div>
</div>""")

    st.html("<br>")
    if st.button("🎯 Play Another Quiz", key="stars_to_quiz"):
        st.session_state["page"] = "quiz"
        if "quiz" in st.session_state:
            del st.session_state["quiz"]
        st.rerun()
