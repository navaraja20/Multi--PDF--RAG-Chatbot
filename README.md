# 📚 Otaku Oracle — Anime/Game PDF RAG

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/API-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![LangChain](https://img.shields.io/badge/RAG-LangChain-orange?style=for-the-badge)
![FAISS](https://img.shields.io/badge/Vector-FAISS-0a9396?style=for-the-badge)
![Ollama](https://img.shields.io/badge/LLM-Ollama-000?style=for-the-badge&logo=ollama&logoColor=white)
![HF Embeddings](https://img.shields.io/badge/Embeddings-HF_MiniLM-dc2626?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

**Anime/Game-first local RAG:** scrape → clean → export PDFs → chat with cited sources. Runs fully offline with LangChain, FAISS, and Ollama or Hugging Face embeddings. Animated red/orange UI inspired by anime.

[Features](#-features) • [Tech Stack](#-tech-stack) • [Install](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Challenges](#-challenges--solutions) • [Roadmap](#-roadmap) • [License](#-license)

</div>

---

## 🌟 Overview
**Otaku Oracle** is a local-first Retrieval-Augmented Generation app tailored for anime/game PDFs. It ships with a scraper pipeline to build your library, a motion-heavy landing/chat UI, and a LangChain RAG core that cites page numbers. Switch between HF MiniLM embeddings or Ollama `nomic-embed-text`; chat with `llama3.1:8b` by default.

### 🎯 Highlights
- 🔒 **Local & private** — PDFs + vectors stay on your machine
- 🧠 **RAG with citations** — FAISS + LangChain, page-aware answers
- 🎨 **Anime UI** — Glassmorphism, red/orange theme, custom background
- 🔄 **Pluggable embeddings** — HF MiniLM (default) or Ollama `nomic-embed-text`
- ⚡ **Auto indexing** — First chat builds FAISS from `data/pdf_files`

---

## ✨ Features
- 📚 **PDF Q&A** — multi-PDF corpus in `data/pdf_files`, chunked and indexed
- 🧩 **History-aware chat** — follow-up questions via `create_history_aware_retriever`
- 🔍 **Vector search** — FAISS store per embedding backend (`faiss_hf` / `faiss_ollama`)
- 🖥️ **Animated UI** — landing (`/`) and chat (`/chat-ui`) with anime-themed background
- 🛠️ **Scraper pipeline** — requests/bs4 + MediaWiki fallback → DOCX/PDF outputs
- 🧭 **Cited sources** — returns page numbers from PDFs

---

## 🛠 Tech Stack
- **API/UI**: Flask, vanilla HTML/CSS (no build step)
- **RAG**: LangChain 0.3.x, FAISS, RecursiveCharacterTextSplitter
- **LLM**: ChatOllama (`llama3.1:8b` by default, configurable)
- **Embeddings**: HF `sentence-transformers/all-MiniLM-L6-v2` (default) or Ollama `nomic-embed-text`
- **Scraping**: requests, beautifulsoup4, lxml, MediaWiki API fallback
- **Formats**: PyPDFLoader ingest; outputs in `data/pdf_files` / `data/docx_files`

---

## 📦 Installation
Prereqs: Python 3.11, Ollama installed (for chat + optional embeddings). If using HF embeddings, no model pull required.

```bash
pip install -r requirements.txt
pip install sentence-transformers
# optional: ollama pull nomic-embed-text (if EMBED_BACKEND=ollama)
ollama pull llama3.1:8b
```

Env defaults (adjust in `.env`):
```env
CHAT_MODEL=llama3.1:8b
EMBED_BACKEND=hf                        # or ollama
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2  # or nomic-embed-text
```

---

## 🚀 Usage
1) Run the server (from project root):
```bash
./.venv/Scripts/python.exe app.py
```
2) Open UI:
- Landing: `http://localhost:5000/`
- Chat UI: `http://localhost:5000/chat-ui`
- Health: `http://localhost:5000/health`

3) API call:
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the main conflict in Death Note", "session_id": "demo"}'
```

4) Rebuild index (if you change embeddings or PDFs): delete `data/index` and restart; first chat will re-index.

---

## 🧭 Architecture
```
PDFs (data/pdf_files)
    └─ PyPDFLoader -> RecursiveCharacterTextSplitter
        └─ Embeddings (HF MiniLM or Ollama)
            └─ FAISS (data/index/faiss_<backend>)
                └─ Retriever (k=4) + history-aware wrapper
                    └─ ChatOllama (llama3.1:8b) -> cited answer
```

---

## 🔧 Challenges & Solutions
- **Embedding bug in Ollama**: early runs returned identical vectors; added HF backend and backend-specific FAISS paths.
- **Context missing for titles**: ensured prompt includes `{context}` and page citations; added MediaWiki fallback in scraper to avoid 403s.
- **Index drift**: added per-backend FAISS folders (`faiss_hf`, `faiss_ollama`) to prevent stale loads when switching embeddings.

---

## 🗺️ Roadmap
- [ ] Dark/Light toggle with additional color schemes
- [ ] Drag-and-drop PDF upload to bypass file system placement
- [ ] Streaming responses in chat UI
- [ ] Per-session index cache & eviction controls

---

## 📂 Project Structure (key paths)
- `app.py` — API, RAG chain, UI routes
- `static/` — `index.html`, `chat.html`, `style.css` (anime theme)
- `data/pdf_files/` — source PDFs
- `data/index/` — FAISS stores (`faiss_hf`, `faiss_ollama`)
- `scraper/` — scraping, cleaning, DOCX/PDF conversion
- `urls/urls.txt` — seed URLs

---

## 📜 License
MIT

---

<div align="center">

⭐ If you find this useful, drop a star and share your anime/game RAG ideas!

</div>
