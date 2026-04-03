# 🗳️ Vaakazhipeer (வாக்களிப்பீர்)

**Tamil Nadu Election Accountability Dashboard**

A real-time, mobile-friendly AI system built to track, measure, and score the fulfillment of political promises made by major Tamil Nadu political parties (DMK and ADMK) over the past decade (2016 → 2026).

---

## 🎯 Problem Statement
Tamil Nadu voters have witnessed two major parties — DMK and ADMK — alternate power since 2016, making hundreds of pre-election promises. However:
- No structured system exists to track promise fulfillment across administrations.
- Information is scattered across vernacular news, government portals, and social media.
- Citizens lack a real-time, accessible tool to hold respective parties accountable.
- The language barrier (Tamil + English) makes automated analysis harder.

## 🚀 Objective
Build a real-time AI accountability dashboard that:
1. **Extracts** promises from DMK & ADMK election manifestos (2016 → 2026).
2. **Maps** them to verified government actions and news using AI semantic matching.
3. **Scores** each party's fulfillment transparently.
4. **Updates live** as new policies/news emerge.
5. **Presents** everything in a beautiful, accessible UI.

## 📊 Scope: Two-Party, One Decade
| Party | Manifesto | Governance Period |
|-------|-----------|-------------------|
| ADMK  | 2016 State Election | 2016 – 2021 |
| DMK   | 2021 State Election | 2021 – Present |

*Data window: 2016 → 2026 (Tracking in Real-Time)*

## 🏗️ System Architecture

### Stage 1: Data Ingestion (Real-Time)
- **Manifesto PDFs** → `pdfplumber` + `pytesseract` (for Tamil OCR)
- **Live News** → NewsAPI / RSS feeds (The Hindu, Dinamalar, Times of India Tamil)
- **Government Actions** → Custom scraper for PRS India, TN govt portals.
- **Scheduler** → GitHub Actions CRON runs pipeline every 6 hours.

### Stage 2: Promise Extraction
- **Sentence segmentation** via heuristic filters (e.g., *"will", "shall", "நாம்", "செய்வோம்"*).
- **Classification** via Zero-shot classification (`BART MNLI`) into categories (Healthcare, Education, etc.).
- Output is standardized as structured JSON per party.

### Stage 3: Semantic Matching (Core ML)
- Uses **Sentence-BERT embeddings** supporting multilingual text (`paraphrase-multilingual-MiniLM`).
- **FAISS vector indexing** enables lightning-fast real-time lookup.
- Cosine similarity identifies the best matching news/actions for each promise.
- Augmented with an **LLM-based verifier** (via OpenAI) for exact confirmation context.

### Stage 4: Fulfillment Scoring
- `Score = (Fulfilled / Total) × 100` based on a tunable similarity threshold (default `0.35` base mapping).
- Granular tracking across key categories: *Healthcare, Education, Agriculture, Infrastructure, Women & Youth, Economy*.

### Stage 5: Real-Time Dashboard (Frontend)
- Built with **React + Vite** (mobile-first UI).
- Real-time data sync using **Firebase Firestore** / **Supabase**.
- Tamil/English language toggle for accessibility.

## 💻 Tech Stack

| Layer | Technologies Used |
|-------|-------------------|
| **Backend NLP ML** | Python, HuggingFace Transformers, FAISS, OpenAI API |
| **Data Storage** | JSON, Firebase Firestore / Supabase |
| **Scheduling** | GitHub Actions YAML, Python Scheduler |
| **Frontend UI** | React + Vite, TailwindCSS |
| **Deployment** | Vercel (frontend), Render / Github Actions (pipeline) |
| **OCR / Extracts**| Tesseract (Tamil-trained models), `pdfplumber` |
| **News / Feeds**| NewsAPI.org, `newspaper3k`, RSS (Dinamalar, The Hindu) |

## 🌟 Key UI Features (Mobile-First)
- 🏆 **Accountability Score Cards:** Direct Party vs Party comparison.
- 📊 **Category-wise Trackers:** Radial charts isolating specific domain performance.
- 📰 **Live News Feed:** Real-world sources linked implicitly to each promise.
- 🔍 **Universal Search:** Search specific policies and promises directly.
- 🌐 **Seamless Localization:** Bilingual Tamil / English toggle.
- 📅 **Timeline View:** chronological tracing from 2016 → now.
- 🔔 **Promise of the Day:** Daily engaging widgets.

---

*This project aims to bridge the gap between promises made and governance delivered using state-of-the-art NLP, bringing transparency to Tamil Nadu politics.*
