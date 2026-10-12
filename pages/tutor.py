"""
pages/tutor.py – "Ask Chhotu" AI tutor chat page.

Features:
  • Chat bubbles: student (right/blue), Chhotu (left/yellow)
  • Suggested question chips
  • Language chips: English | हिन्दी | मराठी
  • Hint-first: "Show me the answer" appears only after the hint
  • Typing indicator animation
  • 🔊 read-aloud on every Chhotu reply
  • Off-topic guard (handled in llm.py system prompt)
"""

import streamlit as st
from ui import inject_css, mascot_say, speak_button, star_counter

inject_css()

SUGGESTIONS = {
    "English": [
        ("🍕", "Explain fractions"),
        ("💡", "Give me a hint on adding fractions"),
        ("🌾", "Show me an example with rotis"),
        ("➗", "How does division work?"),
        ("🔢", "What is 3/4 + 1/4?"),
    ],
    "Hindi": [
        ("🍕", "भिन्न समझाओ"),
        ("💡", "भिन्न जोड़ने का संकेत दो"),
        ("🌾", "रोटी का उदाहरण दो"),
        ("➗", "भाग कैसे करते हैं?"),
        ("🔢", "3/4 + 1/4 क्या होगा?"),
    ],
}


def _get_lang():
    return st.session_state.get("lang", "English")


def _call_tutor(user_text: str) -> str:
    from llm import call_llm
    history = st.session_state.get("chat_history", [])
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": user_text})
    return call_llm(messages, language=_get_lang())


def show():
    user = st.session_state.get("user", {})
    avatar = user.get("avatar", "🐯")
    stars  = user.get("stars", 0)

    st.html("<h2>💬 Ask Chhotu</h2>")
    star_counter(stars)
    mascot_say("Namaste! Ask me anything about math — fractions, adding, dividing! 🦉")

    # ── Language selector ────────────────────────────────────────────────────
    cur_lang = _get_lang()
    lang_cols = st.columns(2)
    lang_map = [("English", "🇬🇧 English"), ("Hindi", "🇮🇳 हिन्दी")]
    for col, (lang_val, lang_label) in zip(lang_cols, lang_map):
        with col:
            is_active = cur_lang == lang_val
            # Use st.html for safe style injection (no stripping)
            if is_active:
                st.html(f"""<style>
                  div[data-testid="stBaseButton-secondary"][aria-label="{lang_label}"],
                  button[kind="secondary"] {{ border-radius:50px!important; }}
                </style>""")
            label_display = f"✅ {lang_label}" if is_active else lang_label
            if st.button(label_display, key=f"lang_{lang_val}", use_container_width=True):
                st.session_state["lang"] = lang_val
                st.rerun()

    st.html("<hr style='border-color:#FFE3A3;margin:8px 0 16px'>")

    # ── Suggested chips (language-aware) ─────────────────────────────────────
    current_suggestions = SUGGESTIONS.get(cur_lang, SUGGESTIONS["English"])
    chip_cols = st.columns(len(current_suggestions))
    for col, (icon, label) in zip(chip_cols, current_suggestions):
        with col:
            if st.button(f"{icon} {label}", key=f"chip_{label}", use_container_width=True):
                _send_message(label)
                st.rerun()

    # ── Chat history ─────────────────────────────────────────────────────────
    history = st.session_state.get("chat_history", [])
    if not history:
        st.session_state["chat_history"] = []
        history = st.session_state["chat_history"]

    for i, msg in enumerate(history):
        if msg["role"] == "user":
            st.html(f"""
<div class="bubble-row-student">
  <div class="bubble-student">{avatar} {msg['content']}</div>
</div>""")
        else:
            st.html(f"""
<div class="bubble-row-tutor">
  <div style="font-size:40px">🦉</div>
  <div class="bubble-tutor">{msg['content']}</div>
</div>""")
            speak_button(msg["content"], language=_get_lang(), key=f"spk_{i}")

            # Show "Show me the answer" button after a hint reply
            if msg.get("is_hint") and not msg.get("answer_revealed"):
                if st.button("🔍 Show me the answer", key=f"reveal_{i}"):
                    follow_up = "Can you now give me the complete worked example and final answer?"
                    _send_message(follow_up, mark_as_answer=True, hint_index=i)
                    st.rerun()

    # ── Typing indicator (shown while waiting) ───────────────────────────────
    if st.session_state.get("tutor_thinking"):
        st.html(
            '<div class="bubble-row-tutor">'
            '<div style="font-size:40px">🦉</div>'
            '<div class="typing-indicator">Chhotu is thinking... 🦉</div>'
            '</div>')

    # ── Input box ────────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        col_in, col_btn = st.columns([5, 1])
        with col_in:
            user_input = st.text_input(
                "Ask Chhotu a math question:",
                placeholder="Type your question here...",
                label_visibility="collapsed",
                key="chat_input",
            )
        with col_btn:
            submitted = st.form_submit_button("➤", use_container_width=True)

    if submitted and user_input.strip():
        _send_message(user_input.strip())
        st.rerun()

    # ── Clear chat ───────────────────────────────────────────────────────────
    if history:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()


def _send_message(text: str, mark_as_answer: bool = False, hint_index: int | None = None):
    """Append user message, call LLM, append assistant reply."""
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    history = st.session_state["chat_history"]

    # Mark previous hint as answered if we're revealing
    if hint_index is not None and hint_index < len(history):
        history[hint_index]["answer_revealed"] = True

    history.append({"role": "user", "content": text})
    st.session_state["tutor_thinking"] = True

    try:
        reply = _call_tutor(text)
    except Exception as e:
        reply = f"Oops, I couldn't connect right now. Try again! ({e})"

    st.session_state["tutor_thinking"] = False

    # Detect if this is a hint reply (heuristic: contains 💡 or "hint")
    is_hint = ("💡" in reply or "hint" in reply.lower()) and not mark_as_answer

    history.append({
        "role":      "assistant",
        "content":   reply,
        "is_hint":   is_hint,
        "answer_revealed": False,
    })
    st.session_state["chat_history"] = history
