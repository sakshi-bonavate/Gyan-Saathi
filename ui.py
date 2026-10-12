"""
ui.py – Gyan Saathi visual theme, mascot, and reusable helper components.

Import and call inject_css() at the top of every page.
"""

import math
import streamlit as st
import streamlit.components.v1 as components

# ── Google Fonts + full CSS theme ─────────────────────────────────────────────

def inject_css():
    # st.html() is the correct API for raw HTML/CSS in Streamlit 1.31+
    # It never strips <style> or <link> tags unlike st.markdown
    st.html("""
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Nunito:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header {visibility: hidden;}
  [data-testid="stToolbar"] {display: none;}
  [data-testid="stSidebar"] {display: none;}
  [data-testid="collapsedControl"] {display: none;}

  /* ── Base ── */
  html, body, .stApp {
    background: #FFF8E7 !important;
    font-family: 'Nunito', sans-serif;
    font-size: 20px;
    color: #2B3A67;
  }
  h1, h2, h3, h4 {
    font-family: 'Baloo 2', cursive !important;
    color: #2B3A67;
  }
  h1 { font-size: 38px !important; }
  h2 { font-size: 30px !important; }
  h3 { font-size: 26px !important; }

  /* ── Layout ── */
  .block-container {
    max-width: 760px !important;
    padding: 1rem 1.2rem 4rem !important;
    margin: 0 auto;
  }

  /* ── Buttons (primary) ── */
  div[data-testid="stButton"] > button,
  .stButton > button {
    width: 100% !important;
    min-height: 72px !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    font-family: 'Baloo 2', cursive !important;
    color: #fff !important;
    background: #4DA8FF !important;
    border: 4px solid #2F86E0 !important;
    border-radius: 24px !important;
    box-shadow: 0 6px 0 #2F86E0 !important;
    transition: all .12s ease !important;
    cursor: pointer !important;
  }
  div[data-testid="stButton"] > button:hover,
  .stButton > button:hover {
    transform: translateY(-2px) !important;
    background: #66B6FF !important;
  }
  div[data-testid="stButton"] > button:active,
  .stButton > button:active {
    transform: translateY(4px) !important;
    box-shadow: 0 2px 0 #2F86E0 !important;
  }

  /* ── Answer choice buttons (option grid) ── */
  .option-btn {
    display: block; width: 100%; min-height: 80px;
    font-size: 22px; font-weight: 800;
    font-family: 'Baloo 2', cursive;
    border-radius: 24px; border: 4px solid;
    cursor: pointer; transition: all .12s ease;
    padding: 12px 18px; text-align: center; line-height: 1.3;
  }
  .opt-a { background:#E8F4FF; border-color:#4DA8FF; color:#1B5EA8; }
  .opt-b { background:#FFF3D0; border-color:#FFC83D; color:#7A5500; }
  .opt-c { background:#E8FFF3; border-color:#3DD598; color:#1A6641; }
  .opt-d { background:#FFF0E6; border-color:#FF9F43; color:#7A3B00; }
  .option-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 0 rgba(0,0,0,.15); }
  .option-btn:active { transform: translateY(3px); }

  /* ── Cards ── */
  .card {
    background: #fff; border-radius: 28px; padding: 24px 28px;
    box-shadow: 0 8px 24px rgba(0,0,0,.08);
    border: 3px solid #FFE3A3;
    animation: pop .35s ease;
    margin-bottom: 16px;
  }
  .card-blue  { border-color: #4DA8FF; background: #EFF8FF; }
  .card-yellow{ border-color: #FFC83D; background: #FFFBEE; }
  .card-green { border-color: #3DD598; background: #EDFFF6; }
  .card-orange{ border-color: #FF9F43; background: #FFF5EC; }

  /* ── Speech bubble (mascot) ── */
  .speech {
    background: #FFC83D; color: #3a2a00;
    border-radius: 24px 24px 24px 4px;
    padding: 14px 20px; font-weight: 800;
    font-size: 20px; display: inline-block;
    box-shadow: 0 4px 0 #D4A017;
    max-width: 85%;
    animation: pop .3s ease;
  }

  /* ── Feedback cards ── */
  .good {
    background: #E6FBF2; border: 3px solid #3DD598;
    border-radius: 24px; padding: 20px 24px;
    font-size: 22px; font-weight: 800; color: #1A6641;
    animation: pop .35s ease;
  }
  .tryagain {
    background: #FFF1E0; border: 3px solid #FF9F43;
    border-radius: 24px; padding: 20px 24px;
    font-size: 22px; font-weight: 800; color: #7A3B00;
    animation: pop .35s ease;
  }

  /* ── Progress bar ── */
  .stProgress > div > div > div > div {
    background: linear-gradient(90deg, #FFC83D, #FF9F43) !important;
    border-radius: 20px !important;
  }
  .stProgress > div > div {
    background: #F0E6D0 !important;
    border-radius: 20px !important;
    height: 20px !important;
  }

  /* ── Chat bubbles ── */
  .bubble-student {
    background: #4DA8FF; color: #fff;
    border-radius: 24px 24px 4px 24px;
    padding: 14px 18px; margin: 8px 0;
    font-size: 19px; font-weight: 700;
    max-width: 80%; margin-left: auto;
    box-shadow: 0 4px 0 #2F86E0;
    animation: pop .25s ease;
  }
  .bubble-tutor {
    background: #FFC83D; color: #3a2a00;
    border-radius: 24px 24px 24px 4px;
    padding: 14px 18px; margin: 8px 0;
    font-size: 19px; font-weight: 700;
    max-width: 80%;
    box-shadow: 0 4px 0 #D4A017;
    animation: pop .25s ease;
  }
  .bubble-row-student { display:flex; justify-content:flex-end; margin:6px 0; }
  .bubble-row-tutor   { display:flex; align-items:flex-start; gap:10px; margin:6px 0; }

  /* ── Language pill buttons ── */
  .lang-pills { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
  .lang-pill {
    padding: 10px 22px; border-radius: 50px;
    font-size: 18px; font-weight: 800;
    font-family: 'Baloo 2', cursive;
    border: 3px solid #4DA8FF; background: #EFF8FF; color: #1B5EA8;
    cursor: pointer; transition: all .12s ease;
  }
  .lang-pill.active { background:#4DA8FF; color:#fff; }

  /* ── Star / badge display ── */
  .star-count {
    font-size: 32px; font-weight: 800; font-family: 'Baloo 2', cursive;
    color: #FFA500; display: inline-flex; align-items: center; gap: 6px;
  }
  .badge {
    display: inline-flex; flex-direction: column; align-items: center;
    background: #FFF3D0; border: 3px solid #FFC83D;
    border-radius: 20px; padding: 14px 18px; margin: 6px;
    font-size: 16px; font-weight: 800; min-width: 110px;
    transition: transform .15s ease;
  }
  .badge:hover { transform: scale(1.05); }
  .badge.locked { filter: grayscale(1); opacity: .55; border-color:#ccc; background:#f0f0f0; }
  .badge-icon { font-size: 42px; margin-bottom: 4px; }

  /* ── Big home nav cards ── */
  .nav-card {
    background: #fff; border-radius: 28px; padding: 32px 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,.10);
    border: 4px solid #4DA8FF; text-align: center;
    cursor: pointer; transition: all .15s ease;
    animation: pop .35s ease;
  }
  .nav-card:hover { transform: translateY(-4px); box-shadow: 0 14px 32px rgba(0,0,0,.14); }
  .nav-card-icon { font-size: 56px; margin-bottom: 10px; display: block; }
  .nav-card-label {
    font-family: 'Baloo 2', cursive;
    font-size: 26px; font-weight: 800; color: #2B3A67;
  }

  /* ── Typing indicator ── */
  .typing-indicator {
    font-size: 18px; color: #7A5500; font-weight: 700;
    animation: pulse 1.2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  /* ── Animations ── */
  @keyframes pop {
    0%  { transform: scale(.92); opacity: 0; }
    100%{ transform: scale(1);   opacity: 1; }
  }
  @keyframes bounce {
    0%,100%{ transform: translateY(0); }
    50%    { transform: translateY(-8px); }
  }

  /* ── Suggestion chips ── */
  .chip {
    display: inline-block; padding: 10px 18px;
    background: #EFF8FF; border: 2px solid #4DA8FF;
    border-radius: 50px; font-size: 17px; font-weight: 700;
    color: #1B5EA8; cursor: pointer; margin: 4px;
    transition: all .12s ease;
  }
  .chip:hover { background: #4DA8FF; color: #fff; }

  /* ── Responsive single-column ── */
  @media (max-width: 500px) {
    .block-container { padding: 0.6rem 0.7rem 3rem !important; }
    h1 { font-size: 28px !important; }
    .nav-card-label { font-size: 20px; }
    .option-btn { font-size: 19px; }
  }
</style>
""")


# ── Mascot ────────────────────────────────────────────────────────────────────

def mascot_say(text: str):
    """Render Chhotu the Owl with a speech bubble."""
    st.html(f"""
<div style="display:flex;align-items:center;gap:14px;margin-bottom:16px">
  <div style="font-size:64px;animation:bounce 2s infinite">🦉</div>
  <div class="speech">{text}</div>
</div>""")


# ── Fraction SVG ──────────────────────────────────────────────────────────────

def fraction_svg(n: int, d: int, size: int = 140) -> str:
    """
    Return an SVG string of a pie/circle divided into d equal sectors,
    with the first n sectors filled in yellow (representing n/d).
    """
    cx = cy = size / 2
    r = size / 2 - 8
    parts = []

    if d == 1:
        fill = "#FFC83D" if n >= 1 else "#FFFFFF"
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="#B9770E" stroke-width="3"/>')
    else:
        for i in range(d):
            a1 = 2 * math.pi * i / d - math.pi / 2
            a2 = 2 * math.pi * (i + 1) / d - math.pi / 2
            x1 = cx + r * math.cos(a1)
            y1 = cy + r * math.sin(a1)
            x2 = cx + r * math.cos(a2)
            y2 = cy + r * math.sin(a2)
            large = 1 if (a2 - a1) > math.pi else 0
            fill = "#FFC83D" if i < n else "#FFFFFF"
            parts.append(
                f'<path d="M{cx:.1f},{cy:.1f} L{x1:.1f},{y1:.1f} '
                f'A{r:.1f},{r:.1f} 0 {large} 1 {x2:.1f},{y2:.1f} Z" '
                f'fill="{fill}" stroke="#B9770E" stroke-width="3"/>'
            )

    label = f'<text x="{cx}" y="{size-4}" text-anchor="middle" font-size="18" font-weight="bold" fill="#7A5500" font-family="Nunito,sans-serif">{n}/{d}</text>'
    svg = (f'<svg width="{size}" height="{size+18}" viewBox="0 0 {size} {size+18}" '
           f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}{label}</svg>')
    return svg


def show_fraction_svg(n: int, d: int, size: int = 140):
    """Render a fraction SVG inline."""
    st.html(fraction_svg(n, d, size))


# ── Read-aloud button (Web Speech API) ───────────────────────────────────────

_LANG_CODES = {
    "English": "en-IN",
    "Hindi":   "hi-IN",
}

def speak_button(text: str, language: str = "English", key: str = "speak"):
    """
    Render a 🔊 button that speaks `text` using the browser's
    SpeechSynthesis API. Strips emojis and symbols before speaking
    so the browser never reads out "check mark" or "fire".
    Tries mr-IN for Marathi with a best-match voice-selection loop.
    """
    lang_code = _LANG_CODES.get(language, "en-IN")

    # Escape the text safely for embedding in a JS single-quoted string
    safe = (text
            .replace("\\", "\\\\")
            .replace("'",  "\\'")
            .replace("\n", " ")
            .replace("\r", ""))

    html = f"""
<button onclick="(function(){{
  var raw = '{safe}';
  var cleaned = raw
    .replace(/[\\u{{1F000}}-\\u{{1FFFF}}]/gu, '')
    .replace(/[\\u{{2000}}-\\u{{27FF}}]/gu,   '')
    .replace(/[\\u{{2B00}}-\\u{{2BFF}}]/gu,   '')
    .replace(/[*_`#~>]/g, '')
    .replace(/\\s+/g, ' ')
    .trim();
  var lang = '{lang_code}';
  function doSpeak(voice) {{
    var u = new SpeechSynthesisUtterance(cleaned);
    u.lang = lang;
    u.rate = 0.92;
    if (voice) u.voice = voice;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }}
  var voices = window.speechSynthesis.getVoices();
  if (voices.length === 0) {{
    window.speechSynthesis.onvoiceschanged = function() {{
      var v = window.speechSynthesis.getVoices();
      var match = v.find(function(x){{ return x.lang.startsWith(lang.substring(0,2)); }});
      doSpeak(match || null);
    }};
  }} else {{
    var match = voices.find(function(x){{ return x.lang.startsWith(lang.substring(0,2)); }});
    doSpeak(match || null);
  }}
}})();" style="
  font-size:28px; background:#EFF8FF; border:3px solid #4DA8FF;
  border-radius:50px; padding:8px 18px; cursor:pointer;
  font-family:sans-serif; transition:all .12s ease;
" title="Read aloud">🔊</button>
"""
    components.html(html, height=60)


# ── Star counter ──────────────────────────────────────────────────────────────

def star_counter(stars: int, streak: int = 0):
    """Display stars and streak in a friendly inline banner."""
    streak_html = f'&nbsp;&nbsp;🔥 {streak} day streak' if streak > 0 else ""
    st.html(f'<div class="star-count">⭐ {stars} Stars{streak_html}</div>')


# ── Badge grid ────────────────────────────────────────────────────────────────

BADGE_DEFS = [
    ("🍕", "Pizza Master",     "Answer 3 fraction questions right"),
    ("🔢", "Fraction Explorer","Complete your first quiz"),
    ("🌾", "Farm Helper",      "Use all farm examples"),
    ("5️⃣", "5 in a Row",       "Get 5 correct in a row"),
    ("🧮", "Math Wizard",      "Score 80%+ in a quiz"),
]

def badge_grid(earned_badges: list[str]):
    """Render a sticker-style badge collection."""
    cols = st.columns(min(len(BADGE_DEFS), 3))
    for idx, (icon, name, desc) in enumerate(BADGE_DEFS):
        locked = name not in earned_badges
        cls = "badge locked" if locked else "badge"
        lock_icon = "🔒 " if locked else ""
        with cols[idx % 3]:
            st.html(f"""
<div class="{cls}" title="{desc}">
  <span class="badge-icon">{icon}</span>
  <span>{lock_icon}{name}</span>
</div>""")


# ── Big card helper ───────────────────────────────────────────────────────────

def big_card(content_html: str, variant: str = ""):
    """Wrap arbitrary HTML in a styled card div."""
    cls = f"card card-{variant}" if variant else "card"
    st.html(f'<div class="{cls}">{content_html}</div>')


# ── Home button ───────────────────────────────────────────────────────────────

def home_button():
    """Render a persistent 🏠 Home button that resets navigation."""
    if st.button("🏠 Home", key="home_top"):
        for key in ["page", "quiz_state", "chat_history", "session_id"]:
            st.session_state.pop(key, None)
        st.rerun()


# ── Progress road ─────────────────────────────────────────────────────────────

def progress_road(current: int, total: int, avatar_emoji: str = "🐯"):
    """Render a fun progress bar with emoji animal on the road."""
    pct = current / total if total > 0 else 0
    pct_int = int(pct * 100)
    st.html(f"""
<div style="margin-bottom:16px">
  <div style="display:flex;justify-content:space-between;font-size:18px;font-weight:800;color:#7A5500;margin-bottom:4px">
    <span>Question {current} of {total}</span>
    <span>{avatar_emoji}</span>
  </div>
  <div style="background:#F0E6D0;border-radius:20px;height:22px;position:relative;overflow:visible">
    <div style="background:linear-gradient(90deg,#FFC83D,#FF9F43);width:{pct_int}%;height:100%;border-radius:20px;transition:width .4s ease;position:relative">
      <span style="position:absolute;right:-14px;top:-10px;font-size:28px">{avatar_emoji}</span>
    </div>
  </div>
</div>""")


# ── Option color palette for answer choices ───────────────────────────────────

OPTION_CLASSES = ["opt-a", "opt-b", "opt-c", "opt-d"]
OPTION_COLORS = [
    ("#E8F4FF", "#4DA8FF", "#1B5EA8"),
    ("#FFF3D0", "#FFC83D", "#7A5500"),
    ("#E8FFF3", "#3DD598", "#1A6641"),
    ("#FFF0E6", "#FF9F43", "#7A3B00"),
]
