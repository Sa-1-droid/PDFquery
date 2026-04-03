# app.py
import streamlit as st
import uuid
import os
import tempfile

from pdf_utils import load_and_split_pdfs
from vector_store import create_vector_store
from qa_engine import ask_question, generate_suggestions, summarize_pdf

from gtts import gTTS
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4

# ------------------------------------------------------------------
# ⚙️ Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="AI PDF Assistant",
    page_icon="📄",
    layout="wide",
)

# ------------------------------------------------------------------
# 💅 Custom CSS
# ------------------------------------------------------------------
st.markdown("""
<style>
/* Remove default top padding */
.block-container { padding-top: 1.5rem; }

/* Chat bubbles */
.user-bubble {
    background: #e8f0fe;
    color: #1a1a2e;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 16px;
    margin: 4px 0;
    display: inline-block;
    max-width: 85%;
    font-size: 0.95rem;
}
.assistant-bubble {
    background: #f0f4f8;
    color: #1a1a2e;
    border-radius: 18px 18px 18px 4px;
    padding: 10px 16px;
    margin: 4px 0;
    display: inline-block;
    max-width: 85%;
    font-size: 0.95rem;
}
.source-pill {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.78rem;
    margin: 2px 3px;
}
.suggestion-label {
    font-size: 0.82rem;
    color: #6b7280;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 🗃️ Session state initialization
# ------------------------------------------------------------------
for key, default in {
    "chat_history": [],       # list of (role, message, sources)
    "vector_db": None,
    "pdf_file_name": None,
    "suggestions": [],
    "summary": None,
    "audio_files": [],        # track temp audio files
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------------------------------------------------------
# 🔊 Text-to-speech helper
# ------------------------------------------------------------------
def speak(text: str) -> str:
    """Generate an mp3, save to a temp file, return the path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts = gTTS(text[:500])          # limit length for speed
    tts.save(tmp.name)
    st.session_state.audio_files.append(tmp.name)
    return tmp.name

# ------------------------------------------------------------------
# 📥 Export chat as PDF
# ------------------------------------------------------------------
def export_chat_pdf() -> bytes:
    buf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(buf.name, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=16)
    user_style  = ParagraphStyle("user",  parent=styles["Normal"],  fontSize=11, spaceAfter=4, textColor="#1a56db")
    ai_style    = ParagraphStyle("ai",    parent=styles["Normal"],  fontSize=11, spaceAfter=8)
    src_style   = ParagraphStyle("src",   parent=styles["Normal"],  fontSize=9,  textColor="#6b7280")

    content = [Paragraph(f"📄 Chat Export — {st.session_state.pdf_file_name or 'PDF'}", title_style), Spacer(1, 12)]
    for role, msg, sources in st.session_state.chat_history:
        label = "You" if role == "user" else "Assistant"
        style = user_style if role == "user" else ai_style
        safe_msg = msg.replace("<", "&lt;").replace(">", "&gt;")
        content.append(Paragraph(f"<b>{label}:</b> {safe_msg}", style))
        if sources:
            srcs = ", ".join(f"{s['source']} p.{s['page']}" for s in sources)
            content.append(Paragraph(f"Sources: {srcs}", src_style))
        content.append(Spacer(1, 6))

    doc.build(content)
    with open(buf.name, "rb") as f:
        return f.read()

# ------------------------------------------------------------------
# 🖼️ Sidebar — PDF upload & controls
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📄 AI PDF Assistant")
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        # Process only if a new file is uploaded
        if st.session_state.pdf_file_name != uploaded_file.name:
            with st.spinner("🔍 Processing PDF…"):
                raw_docs = load_and_split_pdfs([uploaded_file])
                st.session_state.vector_db      = create_vector_store(raw_docs)
                st.session_state.chat_history   = []
                st.session_state.suggestions    = ["What is this PDF about?", "What are the key points?", "Summarize the main sections."]
                st.session_state.summary        = None
                st.session_state.pdf_file_name  = uploaded_file.name
            st.success(f"✅ '{uploaded_file.name}' ready!")

    if st.session_state.pdf_file_name:
        st.markdown(f"**Active PDF:** `{st.session_state.pdf_file_name}`")

    st.markdown("---")

    # 📝 Summarize
    if st.button("📝 Summarize PDF", use_container_width=True, disabled=not st.session_state.vector_db):
        with st.spinner("Summarizing…"):
            st.session_state.summary = summarize_pdf(st.session_state.vector_db)

    if st.session_state.summary:
        with st.expander("📋 PDF Summary", expanded=True):
            st.markdown(st.session_state.summary)

    st.markdown("---")

    # 📥 Export
    if st.button("📥 Export Chat as PDF", use_container_width=True, disabled=not st.session_state.chat_history):
        pdf_bytes = export_chat_pdf()
        st.download_button(
            label="⬇️ Download Chat PDF",
            data=pdf_bytes,
            file_name="chat_export.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("---")

    # 🆕 New Chat
    if st.button("🆕 New Chat", use_container_width=True):
        for key in ["chat_history", "vector_db", "pdf_file_name", "suggestions", "summary"]:
            st.session_state[key] = [] if key in ["chat_history", "suggestions"] else None
        st.rerun()

# ------------------------------------------------------------------
# 💬 Main chat area
# ------------------------------------------------------------------
st.markdown("### 💬 Chat with your PDF")

if not st.session_state.vector_db:
    st.info("👈 Upload a PDF from the sidebar to get started.")
else:
    # ── Display existing chat history ──────────────────────────────
    for role, msg, sources in st.session_state.chat_history:
        with st.chat_message(role):
            if role == "user":
                st.markdown(f'<div class="user-bubble">{msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-bubble">{msg}</div>', unsafe_allow_html=True)
                if sources:
                    pills = "".join(
                        f'<span class="source-pill">📄 {s["source"]} · p.{s["page"]}</span>'
                        for s in sources
                    )
                    st.markdown(f'<div style="margin-top:6px">{pills}</div>', unsafe_allow_html=True)

    # ── Suggested questions ────────────────────────────────────────
    if st.session_state.suggestions:
        st.markdown('<p class="suggestion-label">💡 Suggested questions:</p>', unsafe_allow_html=True)
        cols = st.columns(len(st.session_state.suggestions))
        for i, sugg in enumerate(st.session_state.suggestions):
            if cols[i].button(sugg, key=f"sugg_{i}"):
                st.session_state.chat_history.append(("user", sugg, None))
                st.session_state.suggestions = []
                with st.spinner("Thinking…"):
                    answer, sources = ask_question(
                        st.session_state.vector_db,
                        sugg,
                        st.session_state.chat_history,
                    )
                st.session_state.chat_history.append(("assistant", answer, sources))
                st.session_state.suggestions = generate_suggestions(
                    st.session_state.vector_db, st.session_state.chat_history
                )
                st.rerun()

    # ── Chat input ─────────────────────────────────────────────────
    query = st.chat_input("Ask something about your PDF…")

    if query:
        # Add user message
        st.session_state.chat_history.append(("user", query, None))
        st.session_state.suggestions = []

        with st.chat_message("user"):
            st.markdown(f'<div class="user-bubble">{query}</div>', unsafe_allow_html=True)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            with st.spinner("Thinking…"):
                answer, sources = ask_question(
                    st.session_state.vector_db,
                    query,
                    st.session_state.chat_history,
                )

            # ⚡ Streaming word-by-word effect
            words = answer.split()
            for i, word in enumerate(words):
                full_response += word + " "
                placeholder.markdown(
                    f'<div class="assistant-bubble">{full_response}▌</div>',
                    unsafe_allow_html=True,
                )

            placeholder.markdown(
                f'<div class="assistant-bubble">{answer}</div>',
                unsafe_allow_html=True,
            )

            # 📌 Source pills
            if sources:
                pills = "".join(
                    f'<span class="source-pill">📄 {s["source"]} · p.{s["page"]}</span>'
                    for s in sources
                )
                st.markdown(f'<div style="margin-top:6px">{pills}</div>', unsafe_allow_html=True)

            # 🔊 Voice output
            try:
                audio_path = speak(answer)
                st.audio(audio_path, format="audio/mp3")
            except Exception:
                pass  # Voice is optional — don't crash if gTTS fails

        # Save to history & generate new suggestions
        st.session_state.chat_history.append(("assistant", answer, sources))
        with st.spinner("Generating suggestions…"):
            st.session_state.suggestions = generate_suggestions(
                st.session_state.vector_db, st.session_state.chat_history
            )
        st.rerun()