import streamlit as st
import httpx
import uuid
import os

API = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="LearnLoop",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# CLEAN MODERN UI CSS
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: #F7F8FC;
}

[data-testid="stSidebar"] {
    background: #1F2454 !important;
}

/* Force ALL sidebar text to white */
[data-testid="stSidebar"] * {
    color: white !important;
}

/* Radio button labels */
[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 500;
}

/* Sidebar text area */
[data-testid="stSidebar"] textarea {
    background: white !important;
    color: #111827 !important;
    border-radius: 12px !important;
    border: none !important;
}

/* Placeholder inside textarea */
[data-testid="stSidebar"] textarea::placeholder {
    color: #6B7280 !important;
    opacity: 1 !important;
}

/* Sidebar button */
[data-testid="stSidebar"] .stButton > button {
    background: white !important;
    color: #111827 !important;
    border-radius: 12px;
    font-weight: 600;
    border: none;
}

body, p, div, span, label {
    color: #111827 !important;
}

/* Better dark/light theme compatibility */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stText"] {
    color: #111827 !important;
}

.chat-user {
    background: #5B4BDB;
    color: white !important;
}

.chat-user * {
    color: white !important;
}

/* keep readable in dark mode */
textarea, input {
    color: #111827 !important;
}

body, p, div, span, label {
    color: #111827 !important;
}

h3 {
    color: #1F2454 !important;
    font-weight: 700;
}

.main-title {
    font-size: 34px;
    font-weight: 700;
    color: #1F2454;
    margin-bottom: 6px;
}

.sub-title {
    font-size: 15px;
    color: #667085;
    margin-bottom: 20px;
}

.score-big {
    font-size: 54px;
    font-weight: 700;
    text-align: center;
}

.stat-box {
    background: white;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    border: 1px solid #E5E7EB;
}

.stat-num {
    font-size: 28px;
    font-weight: 700;
}

.stat-label {
    font-size: 12px;
    color: #6B7280;
}

.gap-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 5px solid #ddd;
    border: 1px solid #E5E7EB;
    color: #111827 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.gap-red {
    border-left-color: #EF4444;
}

.gap-green {
    border-left-color: #10B981;
}

.chat-user {
    background: #5B4BDB;
    color: white !important;
    border-radius: 14px 14px 4px 14px;
    padding: 10px 14px;
    margin: 8px 0;
}

.chat-bot {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 14px 14px 14px 4px;
    padding: 10px 14px;
    margin: 8px 0;
}

.stButton > button {
    border-radius: 12px;
    height: 48px;
    font-weight: 600;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "gap_report" not in st.session_state:
    st.session_state.gap_report = None

if "graph_html" not in st.session_state:
    st.session_state.graph_html = None

if "stats" not in st.session_state:
    st.session_state.stats = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "rag_loaded" not in st.session_state:
    st.session_state.rag_loaded = False

if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown("## 🧠 LearnLoop")
    st.caption(f"Session ID: {st.session_state.session_id}")
    st.divider()

    st.markdown("### 📚 Your Notes")

    mode = st.radio(
        "Upload Method",
        ["Paste Text", "Upload File"],
        label_visibility="collapsed"
    )

    if mode == "Paste Text":
        rag_text = st.text_area(
            "Notes Input",
            placeholder="Paste textbook notes, lecture notes, or study material here...",
            height=150,
            label_visibility="collapsed"
        )

        if st.button("Load Notes"):
            if rag_text.strip():
                r = httpx.post(
                    f"{API}/rag/upload-text",
                    json={
                        "session_id": st.session_state.session_id,
                        "text": rag_text
                    },
                    timeout=30
                )

                if r.status_code == 200:
                    st.session_state.rag_loaded = True
                    st.success("Notes loaded successfully")
                else:
                    st.error("Failed to load notes")

    if st.session_state.rag_loaded:
        st.success("Tutor will use your uploaded notes")

# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="main-title">LearnLoop</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Explain a topic in your own words and discover what you actually understand.</div>',
    unsafe_allow_html=True
)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs([
    "🔍 Analyse",
    "🗺 Knowledge Map",
    "💬 Tutor Chat"
])

# =====================================================
# TAB 1 — ANALYSE
# =====================================================
with tab1:
    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown("### What topic are you studying?")

        topic = st.text_input(
            "Topic Input",
            placeholder="Example: Earth, Photosynthesis, OSI Model",
            label_visibility="collapsed"
        )

        st.markdown("### Explain it in your own words")

        explanation = st.text_area(
            "Explanation Input",
            placeholder="Explain like you're teaching a friend...",
            height=220,
            label_visibility="collapsed"
        )

        if st.button("✨ Analyse My Understanding"):
            if not topic.strip() or not explanation.strip():
                st.error("Please enter both topic and explanation")
            else:
                with st.spinner("Analysing your understanding..."):
                    r = httpx.post(
                        f"{API}/analyse",
                        json={
                            "session_id": st.session_state.session_id,
                            "topic": topic,
                            "explanation": explanation
                        },
                        timeout=60
                    )

                    if r.status_code == 200:
                        data = r.json()

                        st.session_state.gap_report = data["gap_report"]
                        st.session_state.graph_html = data["graph_html"]
                        st.session_state.stats = data["stats"]
                        st.session_state.current_topic = topic
                        st.session_state.chat_messages = []

                        st.info("Analysis complete! Open Knowledge Map and Tutor Chat.")
                    else:
                        st.error(f"API Error: {r.text}")

    with right:
        if st.session_state.gap_report:
            report = st.session_state.gap_report
            stats = st.session_state.stats
            score = report["overall_score"]

            if score >= 0.7:
                color = "#10B981"
            elif score >= 0.4:
                color = "#F59E0B"
            else:
                color = "#EF4444"

            st.markdown(
                f'<div class="score-big" style="color:{color}">{score:.0%}</div>',
                unsafe_allow_html=True
            )
            st.caption("Overall Mastery Score")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(
                    f'<div class="stat-box"><div class="stat-num">{stats["understood"]}</div><div class="stat-label">Understood</div></div>',
                    unsafe_allow_html=True
                )

            with c2:
                st.markdown(
                    f'<div class="stat-box"><div class="stat-num">{stats["gaps"]}</div><div class="stat-label">Gaps</div></div>',
                    unsafe_allow_html=True
                )

            with c3:
                st.markdown(
                    f'<div class="stat-box"><div class="stat-num">{stats["total_nodes"]}</div><div class="stat-label">Concepts</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown("### Summary")
            st.write(report["summary"])

            st.markdown("### Concept Breakdown")

            for gap in sorted(report["gaps"], key=lambda x: x["score"]):
                css = "gap-green" if gap["understood"] else "gap-red"

                st.markdown(
                    f'''<div class="gap-card {css}">
                    <b>{gap["concept"].title()}</b><br><br>
                    {gap["feedback"]}
                    </div>''',
                    unsafe_allow_html=True
                )
        else:
            st.info("Run analysis to see your mastery score and concept feedback.")

# =====================================================
# TAB 2 — KNOWLEDGE MAP
# =====================================================
with tab2:
    if st.session_state.graph_html:
        st.components.v1.html(
            st.session_state.graph_html,
            height=550,
            scrolling=False
        )
    else:
        st.info("Run analysis first to generate your knowledge map.")

# =====================================================
# TAB 3 — TUTOR CHAT
# =====================================================
with tab3:
    if not st.session_state.gap_report:
        st.info("Analyse a topic first to start tutoring.")
    else:
        topic = st.session_state.current_topic
        st.markdown(f"### Topic: {topic}")

        # Previous messages
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user">{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-bot">{msg["content"]}</div>',
                    unsafe_allow_html=True
                )

        # Chat input
        user_input = st.text_input(
            "Chat Input",
            placeholder="Type your answer here...",
            key="chat_input",
            label_visibility="collapsed"
        )

        if st.button("Send"):
            if user_input.strip():
                # Save user message
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": user_input
                })

                # Call backend tutor API
                r = httpx.post(
                    f"{API}/tutor",
                    json={
                        "session_id": st.session_state.session_id,
                        "topic": topic,
                        "message": user_input
                    },
                    timeout=30
                )

                if r.status_code == 200:
                    reply = r.json()["reply"]

                    # Save assistant reply
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": reply
                    })

                    # Only rerun (do NOT set session_state.chat_input = "")
                    st.rerun()

                else:
                    st.error(f"Tutor Error: {r.text}")