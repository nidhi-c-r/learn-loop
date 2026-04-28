import streamlit as st
import httpx
import uuid
import os
from datetime import datetime

API = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="LearnLoop",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f8f8f6; }
.main-title { font-size: 28px; font-weight: 600; color: #26215C; margin-bottom: 4px; }
.sub-title  { font-size: 14px; color: #888; margin-bottom: 1.5rem; }
.score-big  { font-size: 48px; font-weight: 700; text-align: center; }
.gap-card   { background: #fff; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
              border-left: 4px solid #ccc; }
.gap-red    { border-left-color: #E24B4A; }
.gap-amber  { border-left-color: #EF9F27; }
.gap-green  { border-left-color: #1D9E75; }
.stat-box   { background: #fff; border-radius: 10px; padding: 14px; text-align: center;
              border: 0.5px solid #e0e0dc; }
.stat-num   { font-size: 28px; font-weight: 600; }
.stat-label { font-size: 12px; color: #888; margin-top: 2px; }
.profile-tag{ display: inline-block; background: #EEEDFE; color: #534AB7;
              border-radius: 999px; padding: 3px 10px; font-size: 12px; margin: 2px; }
.chat-user  { background: #534AB7; color: #fff; border-radius: 12px 12px 4px 12px;
              padding: 8px 14px; margin: 6px 0; max-width: 80%; float: right; clear: both; font-size: 14px; }
.chat-bot   { background: #fff; color: #222; border-radius: 12px 12px 12px 4px;
              padding: 8px 14px; margin: 6px 0; max-width: 80%; float: left; clear: both; font-size: 14px;
              border: 0.5px solid #e0e0dc; }
.clearfix   { clear: both; }
</style>
""", unsafe_allow_html=True)

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
if "user_pattern" not in st.session_state:
    st.session_state.user_pattern = None
if "rag_loaded" not in st.session_state:
    st.session_state.rag_loaded = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""


with st.sidebar:
    st.markdown("### 🧠 LearnLoop")
    st.caption(f"Session: `{st.session_state.session_id}`")
    st.divider()

    st.markdown("**📚 Your Notes (RAG)**")
    rag_tab = st.radio("Upload method", ["Paste text", "Upload file"], label_visibility="collapsed")

    if rag_tab == "Paste text":
        rag_text = st.text_area("Paste notes / textbook content", height=140, placeholder="Paste any notes, chapter content, or study material here...")
        if st.button("Load Notes", use_container_width=True):
            if rag_text.strip():
                with st.spinner("Indexing notes..."):
                    r = httpx.post(f"{API}/rag/upload-text", json={
                        "session_id": st.session_state.session_id,
                        "text": rag_text,
                    }, timeout=30)
                    if r.status_code == 200:
                        st.session_state.rag_loaded = True
                        st.success(f"✓ {r.json()['chunks']} chunks indexed")
    else:
        uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
        if uploaded and st.button("Load File", use_container_width=True):
            with st.spinner("Processing file..."):
                r = httpx.post(
                    f"{API}/rag/upload-file",
                    data={"session_id": st.session_state.session_id},
                    files={"file": (uploaded.name, uploaded.read(), uploaded.type)},
                    timeout=60,
                )
                if r.status_code == 200:
                    st.session_state.rag_loaded = True
                    st.success(f"✓ {r.json()['chunks']} chunks from {uploaded.name}")

    if st.session_state.rag_loaded:
        st.markdown("🟢 Notes active — tutor will use your material")

    st.divider()

    if st.session_state.user_pattern and st.session_state.user_pattern.get("total_sessions", 0) > 0:
        p = st.session_state.user_pattern
        st.markdown("**👤 Your Learning Profile**")
        st.markdown(f"Sessions: `{p['total_sessions']}`  Avg score: `{p['avg_score']:.0%}`")
        if p.get("weak_topics"):
            st.markdown("**Needs work:**")
            for t in p["weak_topics"][:3]:
                st.markdown(f'<span class="profile-tag">⚠ {t}</span>', unsafe_allow_html=True)
        if p.get("strong_topics"):
            st.markdown("**Strengths:**")
            for t in p["strong_topics"][:3]:
                st.markdown(f'<span class="profile-tag" style="background:#E1F5EE;color:#0F6E56">✓ {t}</span>', unsafe_allow_html=True)
        if p.get("common_misconceptions"):
            st.markdown("**Watch out for:**")
            for m in p["common_misconceptions"][:3]:
                st.caption(f"• {m}")


st.markdown('<div class="main-title">LearnLoop</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Explain it. See the gaps. Learn what you actually don\'t know.</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔍 Analyse", "🗺 Knowledge Map", "💬 Tutor Chat"])

with tab1:
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("#### What topic are you studying?")
        topic = st.text_input("Topic", placeholder="e.g. Photosynthesis, Newton's Laws, Binary Search Trees...", label_visibility="collapsed")
        st.markdown("#### Explain it in your own words")
        explanation = st.text_area(
            "Explanation",
            placeholder="Explain the topic as if you're teaching someone who has never heard of it. Don't look anything up — just write what you know.",
            height=220,
            label_visibility="collapsed",
        )
        analyse_btn = st.button("🔍 Analyse My Understanding", use_container_width=True, type="primary")

    if analyse_btn:
        if not topic.strip() or not explanation.strip():
            st.error("Please enter both a topic and your explanation.")
        elif len(explanation.split()) < 10:
            st.warning("Write at least a few sentences for a meaningful analysis.")
        else:
            with st.spinner("Analysing your explanation..."):
                try:
                    r = httpx.post(f"{API}/analyse", json={
                        "session_id": st.session_state.session_id,
                        "topic": topic,
                        "explanation": explanation,
                    }, timeout=60)
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.gap_report = data["gap_report"]
                        st.session_state.graph_html = data["graph_html"]
                        st.session_state.stats = data["stats"]
                        st.session_state.user_pattern = data["user_pattern"]
                        st.session_state.current_topic = topic
                        st.session_state.chat_messages = []
                        st.success("Analysis complete! Check the Knowledge Map and Tutor Chat tabs.")
                    else:
                        st.error(f"API error: {r.text}")
                except Exception as e:
                    st.error(f"Could not connect to API: {e}\n\nMake sure the FastAPI server is running.")

    with col_result:
        if st.session_state.gap_report:
            report = st.session_state.gap_report
            stats = st.session_state.stats
            score = report["overall_score"]

            score_color = "#1D9E75" if score >= 0.7 else "#EF9F27" if score >= 0.4 else "#E24B4A"
            st.markdown(f'<div class="score-big" style="color:{score_color}">{score:.0%}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center;color:#888;font-size:13px;margin-bottom:1rem">Mastery score for {report["topic"]}</div>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="stat-box"><div class="stat-num" style="color:#1D9E75">{stats["understood"]}</div><div class="stat-label">Understood</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-box"><div class="stat-num" style="color:#E24B4A">{stats["gaps"]}</div><div class="stat-label">Gaps</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-box"><div class="stat-num">{stats["total_nodes"]}</div><div class="stat-label">Concepts</div></div>', unsafe_allow_html=True)

            st.markdown(f"**Summary:** {report['summary']}")

            if report.get("strengths"):
                st.markdown("**✓ Strengths**")
                for s in report["strengths"]:
                    st.markdown(f"- {s}")

            st.markdown("**Concept breakdown**")
            for gap in sorted(report["gaps"], key=lambda x: x["score"]):
                s = gap["score"]
                css = "gap-green" if gap["understood"] else "gap-amber" if s >= 0.4 else "gap-red"
                icon = "✓" if gap["understood"] else "⚠" if s >= 0.4 else "✗"
                st.markdown(f"""
                <div class="gap-card {css}">
                  <strong>{icon} {gap['concept'].title()}</strong>
                  <span style="float:right;color:#888;font-size:12px">{s:.0%}</span><br>
                  <span style="font-size:13px;color:#555">{gap['feedback']}</span>
                </div>
                """, unsafe_allow_html=True)


with tab2:
    if st.session_state.graph_html:
        stats = st.session_state.stats
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total concepts", stats["total_nodes"])
        m2.metric("Understood", stats["understood"])
        m3.metric("Gaps", stats["gaps"])
        m4.metric("Mastery", f"{stats['mastery_pct']}%")

        st.markdown("**Legend:** 🟢 Understood &nbsp;&nbsp; 🟡 Partial &nbsp;&nbsp; 🔴 Gap")
        st.components.v1.html(st.session_state.graph_html, height=520, scrolling=False)
    else:
        st.info("Run an analysis first to see your knowledge map.")


with tab3:
    if not st.session_state.gap_report:
        st.info("Analyse a topic first — the tutor will target your specific gaps.")
    else:
        topic = st.session_state.current_topic
        gaps = [g["concept"] for g in st.session_state.gap_report["gaps"] if not g["understood"]]
        st.markdown(f"**Topic:** {topic}")
        if gaps:
            st.markdown("**Targeting gaps:** " + " · ".join(f"`{g}`" for g in gaps[:5]))

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user">{msg["content"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bot">{msg["content"]}</div><div class="clearfix"></div>', unsafe_allow_html=True)

        if not st.session_state.chat_messages:
            if st.button("▶ Start tutor session", use_container_width=True):
                first_msg = f"I've reviewed my explanation of {topic}. Can we start?"
                with st.spinner("Tutor thinking..."):
                    r = httpx.post(f"{API}/tutor", json={
                        "session_id": st.session_state.session_id,
                        "topic": topic,
                        "message": first_msg,
                    }, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        reply = data["reply"]
                        if data.get("follow_up_question"):
                            reply += f"\n\n*{data['follow_up_question']}*"
                        st.session_state.chat_messages.append({"role": "user", "content": first_msg})
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                        st.rerun()

        user_input = st.text_input("Your answer", placeholder="Type your answer or ask a question...", key="chat_input")
        send_btn = st.button("Send", use_container_width=True, type="primary")

        if send_btn and user_input.strip():
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.spinner("Tutor thinking..."):
                r = httpx.post(f"{API}/tutor", json={
                    "session_id": st.session_state.session_id,
                    "topic": topic,
                    "message": user_input,
                }, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    reply = data["reply"]
                    if data.get("follow_up_question"):
                        reply += f"\n\n*{data['follow_up_question']}*"
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    st.rerun()
                else:
                    st.error(f"Tutor error: {r.text}")
