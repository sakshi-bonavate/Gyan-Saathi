"""
app.py – Gyan Saathi entry point.

Handles:
  • Login / Register screens (auth gate)
  • Home screen with 3 big nav cards for students
  • Routing to pages via st.session_state["page"]
"""

import json
import streamlit as st

import database as db
from ui import (
    inject_css, mascot_say, big_card, home_button,
    star_counter, OPTION_COLORS,
)

st.set_page_config(
    page_title="Gyan Saathi 🦉",
    page_icon="🦉",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_css()

# ── Helpers ───────────────────────────────────────────────────────────────────

AVATARS = ["🐯", "🐘", "🦚", "🐒", "🐼"]
TEACHER_PIN = "1234"   # change this to your preferred PIN

def _init_state():
    st.session_state.setdefault("page", "home")
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("auth_tab", "login")   # "login" | "register" | "teacher"
    st.session_state.setdefault("show_teacher_pin", False)

_init_state()

# ── Auth gate ─────────────────────────────────────────────────────────────────

def show_auth():
    st.html("<h1 style='text-align:center'>🦉 Gyan Saathi</h1>")

    tab = st.session_state["auth_tab"]

    if tab == "teacher":
        mascot_say("Welcome, Teacher! Enter your PIN to continue. 🦉")
    else:
        mascot_say("Namaste! Please log in or create a new account. 😊")

    col_l, col_m, col_r = st.columns(3)
    with col_l:
        if st.button("🔑 Login", key="tab_login"):
            st.session_state["auth_tab"] = "login"
            st.rerun()
    with col_m:
        if st.button("✏️ Register", key="tab_register"):
            st.session_state["auth_tab"] = "register"
            st.rerun()
    with col_r:
        if st.button("📊 Teacher", key="tab_teacher"):
            st.session_state["auth_tab"] = "teacher"
            st.rerun()

    st.html("<hr style='border-color:#FFE3A3;margin:10px 0 20px'>")

    if tab == "login":
        _login_form()
    elif tab == "register":
        _register_form()
    else:
        _teacher_pin_form()


def _login_form():
    st.html("<h3 style='text-align:center'>Welcome back! 👋</h3>")

    username = st.text_input("Username", placeholder="your username", key="li_user")
    password = st.text_input("Password", type="password", placeholder="your password", key="li_pass")

    if st.button("🚀 Let's Go!", key="do_login"):
        if not username or not password:
            st.warning("Please fill in both fields.")
        else:
            ok, result = db.login_user(username, password)
            if ok:
                st.session_state["logged_in"] = True
                st.session_state["user"] = result
                st.session_state["page"] = "home"
                st.rerun()
            else:
                st.html(
                    f'<div class="tryagain">❌ {result}</div>')

    st.html("<br>")
    st.html(
        "<div style='text-align:center;font-size:17px'>No account yet? "
        "Click <b>Register</b> above! 🌟</div>")


def _teacher_pin_form():
    """Quick PIN gate → goes straight to teacher dashboard without needing an account."""
    st.html("<h3 style='text-align:center'>📊 Teacher Access</h3>")
    st.html(
        "<div style='text-align:center;font-size:17px;margin-bottom:16px'>"
        "Enter the teacher PIN to open the dashboard.</div>"
    )

    pin = st.text_input("Teacher PIN", type="password", placeholder="Enter PIN", key="t_pin")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🚪 Enter Dashboard", key="do_pin", use_container_width=True):
            if pin == TEACHER_PIN:
                # Log in as a special teacher session (no DB account needed)
                st.session_state["logged_in"] = True
                st.session_state["user"] = {
                    "id": None,
                    "display_name": "Teacher",
                    "role": "teacher",
                    "avatar": "📊",
                    "stars": 0,
                    "streak": 0,
                    "badges": [],
                }
                st.session_state["page"] = "teacher"
                st.rerun()
            else:
                st.html('<div class="tryagain">❌ Wrong PIN. Try again!</div>')
    with col_b:
        if st.button("← Back to Login", key="pin_back", use_container_width=True):
            st.session_state["auth_tab"] = "login"
            st.rerun()

    st.html("<br>")
    st.html(
        "<div style='text-align:center;font-size:15px;color:#aaa'>"
        "Teachers can also register a full account using the Register tab.</div>"
    )


def _register_form():
    st.html("<h3 style='text-align:center'>Create your account! 🌟</h3>")

    display_name = st.text_input("Your first name", placeholder="e.g. Priya", key="rg_name")
    username     = st.text_input("Choose a username", placeholder="e.g. priya123", key="rg_user")
    password     = st.text_input("Choose a password (min 4 chars)", type="password", key="rg_pass")
    confirm      = st.text_input("Repeat password", type="password", key="rg_pass2")

    role = st.radio("I am a", ["Student", "Teacher"], horizontal=True, key="rg_role")

    st.markdown("**Pick your avatar:**")
    av_cols = st.columns(len(AVATARS))
    selected_avatar = st.session_state.get("reg_avatar", AVATARS[0])
    for i, av in enumerate(AVATARS):
        with av_cols[i]:
            border = "4px solid #FFC83D" if av == selected_avatar else "3px solid #ddd"
            st.html(
                f'<div style="font-size:42px;text-align:center;border:{border};'
                f'border-radius:16px;padding:4px">{av}</div>')
            if st.button(av, key=f"av_{i}"):
                st.session_state["reg_avatar"] = av
                st.rerun()

    if st.button("✅ Create Account", key="do_register"):
        selected_avatar = st.session_state.get("reg_avatar", AVATARS[0])
        if password != confirm:
            st.html('<div class="tryagain">🔑 Passwords do not match!</div>')
        else:
            ok, msg = db.register_user(
                username, display_name, password,
                role=role.lower(), avatar=selected_avatar,
            )
            if ok:
                st.html(
                    '<div class="good">🎉 Account created! Now log in.</div>')
                st.session_state["auth_tab"] = "login"
                import time; time.sleep(1.2)
                st.rerun()
            else:
                st.html(
                    f'<div class="tryagain">⚠️ {msg}</div>')


# ── Home screen ───────────────────────────────────────────────────────────────

def show_home():
    user = st.session_state["user"]
    name = user["display_name"]
    avatar = user["avatar"]
    stars  = user.get("stars", 0)

    st.html(
        f"<h1 style='text-align:center'>{avatar} Namaste, {name}!</h1>")
    mascot_say("Ready to learn and have fun? Pick what you want to do! 🎉")
    star_counter(stars, streak=user.get("streak", 0))
    st.html("<br>")

    # 3 big nav cards
    cards = [
        ("🎯", "Play Quiz",   "quiz",   "#4DA8FF", "#2F86E0"),
        ("💬", "Ask Chhotu",  "tutor",  "#FFC83D", "#D4A017"),
        ("⭐", "My Stars",    "stars",  "#3DD598", "#29A87A"),
    ]

    cols = st.columns(3)
    for col, (icon, label, page, bg, border) in zip(cols, cards):
        with col:
            st.html(f"""
<div class="nav-card" style="border-color:{border};background:linear-gradient(135deg,#fff,{bg}22)">
  <span class="nav-card-icon">{icon}</span>
  <span class="nav-card-label">{label}</span>
</div>""")
            if st.button(label, key=f"nav_{page}"):
                st.session_state["page"] = page
                st.rerun()

    # Teacher dashboard card (visible to teachers + PIN-access users)
    if user.get("role") == "teacher":
        st.html("<br>")
        st.html("""
<div class="card card-blue" style="text-align:center">
  <span style="font-size:36px">📊</span>
  <span style="font-size:22px;font-weight:800;margin-left:10px">Teacher Dashboard</span>
</div>""")
        if st.button("Open Dashboard 📊", key="nav_teacher"):
            st.session_state["page"] = "teacher"
            st.rerun()
    else:
        # Show a small teacher link in footer for any user
        st.html("<br>")
        st.html(
            "<div style='text-align:center;font-size:15px;color:#aaa'>"
            "Are you a teacher? "
            "<span style='cursor:pointer;color:#4DA8FF'>"
            "Log out and use the 📊 Teacher tab.</span></div>"
        )

    # Logout
    st.html("<br><br>")
    if st.button("🚪 Log Out", key="logout"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ── Page router ───────────────────────────────────────────────────────────────

def main():
    if not st.session_state.get("logged_in"):
        show_auth()
        return

    page = st.session_state.get("page", "home")

    if page == "home":
        show_home()

    elif page == "quiz":
        from pages.student import show as show_quiz
        home_button()
        show_quiz()

    elif page == "tutor":
        from pages.tutor import show as show_tutor
        home_button()
        show_tutor()

    elif page == "stars":
        from pages.stars import show as show_stars
        home_button()
        show_stars()

    elif page == "teacher":
        user = st.session_state.get("user", {})
        if user.get("role") != "teacher":
            st.warning("Teacher access only.")
            st.session_state["page"] = "home"
            st.rerun()
        else:
            from pages.teacher import show as show_teacher
            home_button()
            show_teacher()


main()
