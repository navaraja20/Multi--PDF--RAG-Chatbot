from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

PDF_DIR = Path("data/pdf_files")
INDEX_DIR = Path("data/index")
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "ollama").lower()
EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2" if EMBED_BACKEND == "hf" else "nomic-embed-text",
)
INDEX_PATH = INDEX_DIR / f"faiss_{EMBED_BACKEND}"
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1:8b")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

conversation_store: Dict[str, ChatMessageHistory] = {}
app = Flask(__name__)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in conversation_store:
        conversation_store[session_id] = ChatMessageHistory()
    return conversation_store[session_id]


def load_documents():
    if not PDF_DIR.exists():
        raise FileNotFoundError(f"PDF folder not found: {PDF_DIR}")
    loader = DirectoryLoader(
        str(PDF_DIR), glob="**/*.pdf", show_progress=True, loader_cls=PyPDFLoader
    )
    return loader.load()


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len
    )
    return splitter.split_documents(documents)


def get_embeddings():
    if EMBED_BACKEND == "hf":
        return HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return OllamaEmbeddings(model=EMBED_MODEL)


def get_vectorstore():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    if INDEX_PATH.exists():
        return FAISS.load_local(
            str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True
        )
    docs = load_documents()
    chunks = chunk_documents(docs)
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(str(INDEX_PATH))
    return db


def build_chain():
    llm = ChatOllama(model=CHAT_MODEL)
    retriever = get_vectorstore().as_retriever(search_kwargs={"k": 4})

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Given the chat history and a follow up question, rewrite the question to be standalone."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful RAG assistant. Use the provided context to answer concisely. If unsure, say you don't know. Provide source page numbers.\n\nContext:\n{context}",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    qa_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

    return RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@app.route("/", methods=["GET"])
def landing():
    return app.send_static_file("index.html")


@app.route("/chat-ui", methods=["GET"])
def chat_ui_page():
    return app.send_static_file("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    question = data.get("question", "").strip()
    session_id = data.get("session_id", "default")
    if not question:
        return jsonify({"error": "question is required"}), 400

    chain = build_chain()
    response = chain.invoke(
        {"input": question},
        config={"configurable": {"session_id": session_id}},
    )

    answer = response.get("answer", "")
    sources = []
    for doc in response.get("context", []):
        meta = doc.metadata or {}
        sources.append(
            {
                "source": meta.get("source"),
                "page": meta.get("page"),
            }
        )

    return jsonify({"answer": answer, "sources": sources})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
