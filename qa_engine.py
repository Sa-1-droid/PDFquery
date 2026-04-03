# qa_engine.py
import os
import random
from groq import Groq

# -------------------------------------------------------
# 🔑 Groq client — API key loaded from environment variable
#    Set it before running:  export GROQ_API_KEY="your_key"
#    or via st.secrets / .env file
# -------------------------------------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

MODEL = "llama-3.3-70b-versatile"


# -------------------------------------------------------
# Helper: build context string from retrieved docs
# -------------------------------------------------------
def _build_context(docs):
    parts = []
    for doc in docs:
        parts.append(
            f"[Source: {doc.metadata['source']} | Page {doc.metadata['page']}]\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


# -------------------------------------------------------
# Helper: build conversation messages for multi-turn chat
# -------------------------------------------------------
def _build_messages(context, query, chat_history):
    system_prompt = (
        "You are an expert PDF assistant. "
        "Answer ONLY using the context provided from the PDF. "
        "If the answer is not present in the context, respond with: "
        "'This information is not available in the uploaded PDF.' "
        "Always mention the page number when relevant. "
        "Be concise, accurate, and helpful."
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Add prior turns (skip the very last user message — we'll add it with context)
    history_turns = [
        (role, msg)
        for role, msg, _ in (chat_history or [])
        if role in ("user", "assistant")
    ]
    # Keep last 6 turns to stay within token limits
    for role, msg in history_turns[-6:]:
        messages.append({"role": role, "content": msg})

    # Final user message with freshly retrieved context
    user_content = (
        f"Context from the PDF:\n\n{context}\n\n"
        f"---\n\nQuestion: {query}"
    )
    messages.append({"role": "user", "content": user_content})
    return messages


# -------------------------------------------------------
# 1. Q&A
# -------------------------------------------------------
def ask_question(vector_db, query, chat_history=None, k=4):
    """
    Ask LLM a question using top-k similar chunks from the vector store.
    Returns: (answer_text, sources_list)
    """
    docs = vector_db.similarity_search(query, k=k)
    context = _build_context(docs)
    messages = _build_messages(context, query, chat_history)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=1024,
        temperature=0.3,
    )

    answer_text = response.choices[0].message.content
    sources = [
        {
            "source": doc.metadata["source"],
            "page": doc.metadata["page"],
            "text": doc.metadata["text"],
        }
        for doc in docs
    ]
    return answer_text, sources


# -------------------------------------------------------
# 2. Suggested follow-up questions
# -------------------------------------------------------
def generate_suggestions(vector_db, chat_history, k=3):
    """
    Generate 3 dynamic suggested questions based on the last user message
    and the surrounding PDF context.
    """
    if not chat_history:
        return [
            "What is this PDF about?",
            "Can you summarize the main points?",
            "What are the key takeaways?",
        ]

    user_msgs = [msg for role, msg, _ in chat_history if role == "user"]
    if not user_msgs:
        return [
            "What is this PDF about?",
            "Can you summarize the main points?",
            "What are the key takeaways?",
        ]

    last_user_msg = user_msgs[-1]

    # Retrieve context related to last question for smarter suggestions
    docs = vector_db.similarity_search(last_user_msg, k=2)
    context_snippet = _build_context(docs)[:1500]

    prompt = [
        {
            "role": "user",
            "content": (
                f"Based on this PDF context:\n\n{context_snippet}\n\n"
                f"And the user's last question: '{last_user_msg}'\n\n"
                "Generate exactly 3 short, relevant follow-up questions the user might ask next. "
                "Return ONLY a Python list of 3 strings, e.g. ['Q1?', 'Q2?', 'Q3?']. "
                "No extra text, no numbering."
            ),
        }
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=prompt,
            max_tokens=200,
            temperature=0.7,
        )
        raw = response.choices[0].message.content.strip()
        # Parse safely
        suggestions = eval(raw) if raw.startswith("[") else []
        if isinstance(suggestions, list) and len(suggestions) >= 3:
            return suggestions[:3]
    except Exception:
        pass

    # Fallback
    fallbacks = [
        f"Can you elaborate on '{last_user_msg[:40]}'?",
        f"What are the implications of '{last_user_msg[:40]}'?",
        f"Are there any examples related to '{last_user_msg[:40]}'?",
    ]
    random.shuffle(fallbacks)
    return fallbacks[:k]


# -------------------------------------------------------
# 3. PDF Summarization
# -------------------------------------------------------
def summarize_pdf(vector_db, k=6):
    """
    Summarize the PDF using top-k chunks retrieved for a broad summary query.
    """
    docs = vector_db.similarity_search("main topics overview summary introduction conclusion", k=k)
    context = _build_context(docs)

    prompt = [
        {
            "role": "user",
            "content": (
                "You are a document summarizer. "
                "Summarize the following PDF content in a clear, structured manner:\n"
                "- Start with a 1-sentence overview.\n"
                "- List the 4-6 key points or sections.\n"
                "- End with a brief conclusion.\n\n"
                f"PDF Content:\n\n{context}"
            ),
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=prompt,
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content