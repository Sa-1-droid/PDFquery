# 📄 AI PDF Query Assistant

An intelligent PDF question-answering application that allows users to **chat with PDFs**, extract insights, and navigate directly to relevant content with **clickable, highlighted sources**.

Built using **Streamlit, Groq LLMs, and vector search**, this project transforms static PDFs into interactive knowledge systems.

---

## 🚀 Features

### 🔍 Ask Questions from PDFs

* Upload any PDF and ask questions in natural language
* Get accurate answers strictly based on document content

### 🧠 AI-Powered Responses

* Powered by **Groq (LLaMA 3.3 70B)**
* Context-aware answers using retrieved PDF chunks
* Maintains conversational memory for follow-ups

### 📌 Clickable Source References

Each answer includes source citations.

Click a source to:

* Open the PDF
* Jump to the exact page
* View the relevant text

---

### 💡 Smart Suggestions

* Dynamically generated follow-up questions
* Helps users explore documents more effectively

### 📝 PDF Summarization

Generates structured summaries:

* Overview
* Key points
* Conclusion

### 🔊 Text-to-Speech

* Converts AI responses into audio

### 📥 Export Chat

* Download conversation history as a PDF

---

## 🏗️ Tech Stack

| Component       | Technology               |
| --------------- | ------------------------ |
| Frontend        | Streamlit                |
| LLM API         | Groq (LLaMA 3.3 70B)     |
| Embeddings      | HuggingFace Transformers |
| Vector Database | FAISS                    |
| PDF Processing  | PyPDF                    |
| Text-to-Speech  | gTTS                     |
| PDF Export      | ReportLab                |

---

## ⚙️ How It Works

1. Upload a PDF
2. Text is extracted and split into chunks
3. Chunks are converted into embeddings
4. Stored in a FAISS vector database
5. User asks a question
6. Relevant chunks are retrieved
7. LLM generates an answer using context
8. Sources are displayed with page navigation

---

## 📸 Demo Flow

1. Upload a PDF
2. Ask a question
3. Get AI-generated answer
4. Click source → open PDF → view relevant section

---

## ▶️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/Sa-1-droid/PDFquery.git
cd PDFquery
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Set API Key (IMPORTANT)

This project requires a **Groq API key**.

1. Open `qa_engine.py`
2. Find this line:

```python
GROQ_API_KEY="ENTER YOUR API KEY"
```

3. Replace it with your actual API key:

```python
GROQ_API_KEY="your_actual_api_key"
```

⚠️ Do NOT share your API key publicly.

---

## ▶️ Run App

```bash
streamlit run app.py
```

---

## 📂 Project Structure

```
├── app.py              # Main Streamlit app
├── pdf_utils.py        # PDF loading & processing
├── vector_store.py     # Embeddings & FAISS setup
├── qa_engine.py        # LLM interaction logic
├── requirements.txt
└── README.md
```

---

## 🧪 Use Cases

* 📚 Study and revision from textbooks
* 📄 Research paper understanding
* 🧾 Legal or financial document analysis
* 🏫 School and academic projects

---

## ⚠️ Limitations

* Highlighting depends on browser PDF viewer
* Not pixel-perfect highlighting
* Large PDFs may load slower

---

## 🔮 Future Improvements

* Precise text highlighting using PDF.js
* Multi-PDF querying
* Persistent chat history
* Improved UI/UX

---

## 🤝 Contributing

Contributions are welcome!
Feel free to open issues or submit pull requests.

---

## ⭐ Support

If you found this project useful:

⭐ Star this repository
📢 Share it with others

---

## 📬 Contact

For queries or collaboration, feel free to reach out!

---
