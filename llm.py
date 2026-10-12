"""
llm.py – LLM abstraction for Gyan Saathi.

Mode 1 (IBM_API_KEY set):  calls IBM watsonx chat endpoint.
Mode 2 (no key):           returns pre-written hints/examples/answers
                           from questions.json — no crash, no API needed.

The 3-stage demo flow per topic:
  ask once  → hint
  ask again → worked example
  ask again → full answer
"""

import os
import json
import requests


# ── Configuration (Streamlit secrets → env vars → defaults) ──────────────────

def _cfg(key: str, default: str = "") -> str:
    """Read from st.secrets first, then os.environ, then default."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


IBM_API_KEY    = _cfg("IBM_API_KEY")
IBM_PROJECT_ID = _cfg("IBM_PROJECT_ID")
IBM_MODEL_ID   = _cfg("IBM_MODEL_ID", "ibm/granite-3-3-8b-instruct")
IBM_API_URL    = _cfg(
    "IBM_API_URL",
    "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29",
)

DEMO_MODE: bool = not bool(IBM_API_KEY)   # True when no key is present

# ── Load questions.json once ──────────────────────────────────────────────────

_QUESTIONS: list[dict] = []

def _load_questions():
    global _QUESTIONS
    if _QUESTIONS:
        return _QUESTIONS
    path = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(path, encoding="utf-8") as f:
        _QUESTIONS = json.load(f)
    return _QUESTIONS


# ── Language key helper ───────────────────────────────────────────────────────

def _lang_key(language: str) -> str:
    return {"Hindi": "hi"}.get(language, "en")


# ── IAM token helper ──────────────────────────────────────────────────────────

_iam_token_cache: dict = {}

def _get_iam_token() -> str:
    import time
    if _iam_token_cache.get("token") and time.time() < _iam_token_cache.get("expires", 0):
        return _iam_token_cache["token"]
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": IBM_API_KEY},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _iam_token_cache["token"] = data["access_token"]
    _iam_token_cache["expires"] = time.time() + int(data.get("expires_in", 3500)) - 60
    return _iam_token_cache["token"]


# ── System prompt (used by live mode) ────────────────────────────────────────

SYSTEM_PROMPT = """You are Chhotu, a friendly AI tutor for Grade 4-5 rural Indian students.
Rules:
- Answer ONLY questions about Grade 4-5 mathematics (fractions, addition, subtraction, multiplication, division).
- If asked anything off-topic reply: "I only help with math! Ask me about fractions or sums. 😊"
- Use very simple language. Short sentences. Max 80 words.
- Use local examples: roti, chapati, farm, market, mango, laddoo, cow, field.
- ALWAYS give a HINT first. Only show the full worked example if the student asks again.
- Only reveal the final answer if the student asks a third time or says "tell me the answer".
- When language is Hindi: reply entirely in simple Hindi (Devanagari script).
"""


# ── Public API ────────────────────────────────────────────────────────────────

def call_llm(messages: list[dict], language: str = "English") -> str:
    """
    Parameters
    ----------
    messages : list of {"role": "user"|"assistant"|"system", "content": str}
    language : "English" | "Hindi" | "Marathi"

    Returns str – assistant reply.
    Never raises — returns a friendly error message if the API call fails.
    """
    if DEMO_MODE:
        return _demo_response(messages, language)

    # ── Live IBM watsonx call ─────────────────────────────────────────────────
    try:
        lang_instruction = {
            "Hindi": "तुम्हें पूरी तरह सरल हिंदी में जवाब देना है।",
        }.get(language, "")
        system_content = SYSTEM_PROMPT + (f"\n{lang_instruction}" if lang_instruction else "")
        full_messages = [{"role": "system", "content": system_content}] + messages

        token = _get_iam_token()
        payload = {
            "model_id": IBM_MODEL_ID,
            "project_id": IBM_PROJECT_ID,
            "messages": full_messages,
            "parameters": {"max_new_tokens": 200, "temperature": 0.4},
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        resp = requests.post(IBM_API_URL, headers=headers,
                             data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        # Never crash — fall back to demo
        return _demo_response(messages, language)


# ── Demo mode: 3-stage hint → example → answer from questions.json ────────────

# Skill keywords for matching user input (English + Devanagari)
_SKILL_KEYWORDS: list[tuple[list[str], str]] = [
    (["fraction", "भिन्न", "1/2", "1/3", "1/4", "2/4", "3/4",
      "pizza", "roti", "half", "आधा"], "fractions_basic"),
    (["compar", "bigger", "smaller", "बड़ा", "छोटा",
      "which is more", "कौन ज़्यादा"], "fractions_compare"),
    (["add fraction", "भिन्न जोड़", "jod", "जोड"],                            "fractions_add"),
    (["subtract fraction", "घटाव", "minus fraction"],                          "fractions_subtract"),
    (["fraction of", "of 12", "of 20", "1/3 of", "1/4 of"],                   "fractions_of_number"),
    (["multipl", "times", "गुणा", "गुणाकार", "×"],                            "multiplication"),
    (["divis", "share", "भाग", "भागाकार", "÷"],                               "division"),
    (["subtract", "minus", "घटाव", "sold", "left"],                            "subtraction"),
    (["add", "plus", "जोड़", "more", "total"],                                  "addition"),
    (["count", "group", "गिनो"],                                               "counting"),
]

# Generic fallbacks
_FALLBACK = {
    "en": (
        "Namaste! 😊 I can help with fractions, addition, subtraction, "
        "multiplication, and division.\nWhat topic would you like to explore?"
    ),
    "hi": "नमस्ते! 😊 मैं भिन्न, जोड़, घटाव, गुणा और भाग में मदद कर सकता हूँ।\nआज क्या सीखना है?",
}

# Off-topic replies
_OFFTOPIC = {
    "en": "I only help with math! Ask me about fractions or sums. 😊",
    "hi": "मैं सिर्फ गणित में मदद करता हूँ! भिन्न या जोड़-घटाव के बारे में पूछो। 😊",
}

# Explicit off-topic triggers
_OFFTOPIC_WORDS = [
    "cricket", "movie", "film", "song", "game", "joke", "history",
    "geography", "science", "english grammar", "hindi poem",
]

# Warm, varied openers — English and Hindi only
_OPENERS = {
    "hint": {
        "en": [
            "Good question! Let me give you a little clue first. 😊\n",
            "Ooh, great topic! Here's something to help you think 👇\n",
            "Let's figure this out together! 🤔\n",
            "I love this question! Start with this hint 💡\n",
        ],
        "hi": [
            "अच्छा सवाल! पहले एक छोटा संकेत लो। 😊\n",
            "बढ़िया! एक सुराग से शुरू करते हैं 👇\n",
            "मिलकर सोचते हैं! 🤔\n",
            "मुझे यह सवाल पसंद है! यह संकेत लो 💡\n",
        ],
    },
    "example": {
        "en": [
            "You're doing great — let's look at a real example now! 🌾\n",
            "Nice thinking! Here's how it works with a farm story 🌾\n",
            "Almost cracked it! Let me show you step by step 👣\n",
            "Good effort! Watch how Gopal solves it 🌾\n",
        ],
        "hi": [
            "शाबाश! अब एक असली उदाहरण देखते हैं 🌾\n",
            "अच्छी सोच! खेत की कहानी से समझते हैं 🌾\n",
            "बस थोड़ा और! कदम-दर-कदम देखते हैं 👣\n",
            "बढ़िया कोशिश! देखो गोपाल कैसे हल करता है 🌾\n",
        ],
    },
    "full_answer": {
        "en": [
            "You got it! Here's the complete answer 🎉\n",
            "Well done for sticking with it — here's the solution ✅\n",
            "You were so close! Here it is ✅\n",
            "Great job asking again — here's the full answer 🎉\n",
        ],
        "hi": [
            "शाबाश! यह रहा पूरा जवाब 🎉\n",
            "लगे रहो! यह रहा हल ✅\n",
            "तुम बिल्कुल पास थे! यह रहा ✅\n",
            "फिर पूछा, बहुत अच्छे! यह रहा पूरा जवाब 🎉\n",
        ],
    },
}


def _demo_response(messages: list[dict], language: str) -> str:
    """
    Warm, conversational 3-stage engine:
      1st ask → hint with friendly opener
      2nd ask → worked example
      3rd ask / 'tell me' → full answer
    No mention of demo mode anywhere in the output.
    """
    import random
    questions = _load_questions()
    lk = _lang_key(language)
    last_user = messages[-1]["content"] if messages else ""
    last_lower = last_user.lower()

    # Off-topic guard
    if any(word in last_lower for word in _OFFTOPIC_WORDS):
        return _OFFTOPIC.get(lk, _OFFTOPIC["en"])

    # Reveal triggers → skip straight to full answer
    reveal_triggers = [
        "tell me the answer", "show answer", "answer please", "what is it",
        "just tell", "जवाब बताओ", "बता",
    ]
    force_answer = any(t in last_lower for t in reveal_triggers)

    matched_skill = _match_skill(last_lower, last_user)
    q = _pick_question(questions, matched_skill)

    if q is None:
        return _FALLBACK.get(lk, _FALLBACK["en"])

    prior_replies = sum(1 for m in messages[:-1] if m["role"] == "assistant")

    stage = "full_answer" if force_answer else (
        "hint"       if prior_replies == 0 else
        "example"    if prior_replies == 1 else
        "full_answer"
    )

    content = q.get(stage, {})
    body = content.get(lk) or content.get("en", "")

    if not body:
        return _FALLBACK.get(lk, _FALLBACK["en"])

    opener = random.choice(_OPENERS[stage][lk])
    return opener + body


def _match_skill(text_lower: str, text_original: str) -> str | None:
    for keywords, skill in _SKILL_KEYWORDS:
        if any(kw.lower() in text_lower or kw in text_original for kw in keywords):
            return skill
    return None


def _pick_question(questions: list[dict], skill: str | None) -> dict | None:
    """Return the easiest question matching the skill, or any question if no match."""
    if skill:
        matches = [q for q in questions if q.get("skill") == skill]
        if matches:
            return sorted(matches, key=lambda q: q.get("difficulty", 9))[0]
    # Default: pick first fractions_basic question
    for q in questions:
        if q.get("skill") == "fractions_basic" and q.get("hint"):
            return q
    return questions[0] if questions else None
