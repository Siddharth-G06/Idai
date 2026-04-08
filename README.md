# 🗳️ Vaakazhipeer Accountability Dashboard

**Tamil Nadu Political Accountability Tracker (2016 - 2026)**

A real-time, AI-powered system built to track, measure, and transparently score the fulfillment of political promises made by major Tamil Nadu political parties (DMK and AIADMK).

## 🚀 The Gist
- **What it is:** A platform that automatically extracts promises from election manifestos, scans live news sources for corresponding government actions, and scores each party on their fulfillment metrics.
- **Frontend:** React + Vite + Tailwind CSS (Bilingual Tamil/English UI)
- **Backend API:** FastAPI
- **Automation:** GitHub Actions runs 6-hourly pipelines to fetch news, run ML matching, and push updated static JSON data. 
- **Resilience:** Integrates active dead-link fallbacks, free-tier cold-start handlers, and intelligent background prefetching for a seamless user experience.

---

## 🧠 Machine Learning Pipeline

The core intelligence of the platform relies on a sophisticated, multi-stage NLP pipeline designed to bridge the cross-lingual gap between Tamil manifestos and primarily English news sources.

### 1. Optical Character Recognition (OCR)
*   **Tech:** `pytesseract` + Poppler
*   **Role:** Extracts raw text from legacy scanned PDF manifestos. Features a custom garbled-text detector that automatically triggers forced OCR passes specifically tuned for Tamil typography if text extraction fails.

### 2. Auto-Translation
*   **Tech:** `Helsinki-NLP/opus-mt-ta-en` (MarianMT)
*   **Role:** Converts all Tamil promises into English to standardize the dataset and optimize compatibility with downstream embedding models and APIs.

### 3. Semantic Vector Matching
*   **Tech:** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence-BERT) + FAISS
*   **Role:** Converts translated promises and scraped news articles into high-dimensional vector embeddings. FAISS enables lightning-fast cosine-similarity searches to identify the most relevant news coverage for any given promise, overcoming variations in phrasing.

### 4. LLM Verification & Scoring
*   **Tech:** Groq API (Llama 3 8B / 70B Models)
*   **Role:** Acts as the final cognitive layer. The LLM evaluates the semantically matched news article against the original promise. It performs zero-shot reasoning to categorize the promise (e.g., Healthcare, Infrastructure) and rigorously verify its fulfillment status (*Fulfilled*, *Unfulfilled*, or *Pending*), determining the party's ultimate score.

---

## 💻 Tech Stack
- Frontend: `React`, `Vite`, `TailwindCSS`, `TanStack Query`
- Backend: `FastAPI`, `Python`
- Deployment: `Vercel` (Frontend), `Render` (API), `GitHub Actions` (Pipeline)
