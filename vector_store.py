# vector_store.py
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

def create_vector_store(raw_docs):
    """
    Splits raw page docs into chunks and builds a FAISS vector store.
    """
    splitter = CharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    documents = []

    for doc in raw_docs:
        chunks = splitter.split_text(doc["content"])
        for chunk in chunks:
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": doc["source"],
                        "page": doc["page"],
                        "text": chunk
                    }
                )
            )

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_db = FAISS.from_documents(documents, embeddings)
    return vector_db