# 📄 AuditLens

```
 █████╗ ██╗   ██╗██████╗ ██╗████████╗██╗     ███████╗███╗   ██╗███████╗
██╔══██╗██║   ██║██╔══██╗██║╚══██╔══╝██║     ██╔════╝████╗  ██║██╔════╝
███████║██║   ██║██║  ██║██║   ██║   ██║     █████╗  ██╔██╗ ██║███████╗
██╔══██║██║   ██║██║  ██║██║   ██║   ██║     ██╔══╝  ██║╚██╗██║╚════██║
██║  ██║╚██████╔╝██████╔╝██║   ██║   ███████╗███████╗██║ ╚████║███████║
╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝
```

### ML-based document classification with a human always in the loop.

Upload it. OCR it. Classify it. Verify it — before anything is trusted.

🏆 Built for **Cognithon 2026** — College AI Hackathon (Case 29: ML-Based Document Classification System)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-TF--IDF-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-Classifier-1560bd)](https://xgboost.readthedocs.io/)
[![Tesseract OCR](https://img.shields.io/badge/Tesseract-OCR-4285F4)](https://github.com/tesseract-ocr/tesseract)
[![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-Educational-lightgrey)](#license)

---

## The Problem

Businesses drown in unstructured paperwork — invoices, purchase orders, resumes, policies, claims — arriving as scans, PDFs, and text dumps with no consistent structure. Manually sorting and validating every document before it reaches a downstream system is slow, error-prone, and impossible to audit.

**AuditLens** fixes this. It's a document-management workflow that extracts text (including OCR for scanned PDFs), predicts a category with a CPU-friendly ML model, surfaces a confidence score, and — critically — **never lets an AI decision become final without a human reviewer approving it first.**

---

## 🎥 Demo

*Add your presentation link or screen recording here.*

---

## ✨ What Makes AuditLens Different

### 🧠 CPU-Friendly ML at the Core
| Feature | What it does |
|---|---|
| **OCR-First Extraction** | Every PDF is rasterized and run through Tesseract, so scanned/image-only documents are read exactly like born-digital ones — no separate code path. |
| **TF-IDF + XGBoost Classification** | Documents are vectorized (TF-IDF, up to 5,000 features, uni+bigrams) and classified into 6 categories with a trained XGBoost model. |
| **Confidence-Aware Routing** | Predictions below a 75% confidence threshold are automatically flagged for mandatory human review instead of auto-approved. |
| **Duplicate Detection** | Each document is hashed on ingestion to flag likely duplicate submissions. |

### 👤 Human Always in the Loop
- **Reviewer Validation** — Every predicted category must be confirmed or corrected by a named reviewer before it's considered final.
- **Locked GenAI Synopsis** — A short document synopsis is only generated *after* human category validation, and only from redacted, reviewer-approved text.
- **Full Audit Trail** — Reviewer alias, timestamp, original prediction, and final category are all persisted for traceability.

### 🛡️ Guardrails by Default
- Identifier redaction on extracted text (`[REDACTED]`, `[OCR-GAP]` markers).
- File-type, MIME, and size validation before anything is processed.
- Prompt-injection pattern detection — unsafe uploads are blocked before extraction and logged for security audit, never sent to the model.
- Token/cost tracking on every GenAI call.

### ⚡ Live Ops Dashboard
- Real-time KPIs: total documents, awaiting review, verified, failed, tokens used.
- Document queue with per-file status, upload history, and full extracted-text viewer with inline redaction highlighting.

---

## 🖥️ Tech Stack

```
┌───────────────────────────────────────────────────────────┐
│                        AUDITLENS                           │
├───────────────────┬─────────────────────────────────────── │
│ Frontend / App     │ Streamlit                              │
│ ML Layer           │ scikit-learn (TF-IDF) + XGBoost        │
│ OCR                │ Tesseract OCR + pdf2image (Poppler)     │
│ Data / Persistence │ SQLite                                 │
│ Core Libraries     │ pandas, joblib, Pillow                 │
└───────────────────┴─────────────────────────────────────── │
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and on your `PATH`
- [Poppler](https://poppler.freedesktop.org/) (required by `pdf2image` for PDF rasterization)

### 1. Clone the repo
```bash
git clone https://github.com/your-username/auditlens.git
cd auditlens
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate synthetic training data
```bash
python generate_training_files.py
```

### 4. Train the classifier
```bash
python train_model.py
```
This produces `model.pkl` (TF-IDF vectorizer + XGBoost model + label encoder). Without it, the app falls back to placeholder classification so the UI still runs end-to-end.

### 5. Launch the app
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
auditlens/
├── app.py                      # Streamlit UI — upload, review, dashboard
├── db.py                       # SQLite persistence layer
├── ocr_utils.py                # Tesseract-based PDF OCR (shared by app + training)
├── train_model.py              # TF-IDF + XGBoost training pipeline
├── generate_training_files.py  # Synthetic training data generator
├── requirements.txt
└── LICENSE
```

---

## ✅ Judge-Ready Acceptance Criteria

- [x] A clear invoice and resume are classified into different categories.
- [x] An unsupported or oversized file is rejected safely.
- [x] A low-confidence document is held for review and correction.
- [x] Reviewer actions are persisted with timestamp and user/role alias.
- [x] A prompt-injection / unsafe-input test is handled safely.
- [x] The interface shows a disclaimer, confidence indicator, and token-usage info.

---

## 👥 The Team

| Name | Role |
|---|---|
| **Kaivalya** | Team Lead · Backend & ML Engineer |
| **Vivaan** | Frontend Developer |
| **Manish** | Database Engineer |
| **Shreeya** | Presentation & Deck |

<p>
  <a href="https://www.linkedin.com/in/kaivalya-thombare-930a1b386/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BAG%2FfMILITXGZuT2eBMjQow%3D%3D"><img src="https://img.shields.io/badge/Kaivalya-LinkedIn-0A66C2?logo=linkedin&logoColor=white" /></a>
  <a href="https://www.linkedin.com/in/vivaan-uchil-87a096307/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3B5Zhbol3tRy6wj25Q%2F%2BSpiQ%3D%3D"><img src="https://img.shields.io/badge/Vivaan-LinkedIn-0A66C2?logo=linkedin&logoColor=white" /></a>
  <a href="https://www.linkedin.com/in/manish-kumbhar-4372a73a5/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3Bjox3629JRmOsVTkXC8BHuA%3D%3D"><img src="https://img.shields.io/badge/Manish-LinkedIn-0A66C2?logo=linkedin&logoColor=white" /></a>
  <a href="https://www.linkedin.com/in/shreeya-mhatre-438624406/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3B%2Bol%2FOQNUQ6W8hPsCD2e%2Fcw%3D%3D"><img src="https://img.shields.io/badge/Shreeya-LinkedIn-0A66C2?logo=linkedin&logoColor=white" /></a>
</p>


---

### 🤝 Contributing

This is an educational hackathon project. Issues and suggestions are welcome — open a GitHub Issue or reach out to any team member.

### 📄 License

Built for **Cognithon 2026**. Synthetic data only. Created for educational purposes.

---

<p align="center">Document chaos in. Verified, auditable decisions out. — <b>AuditLens</b></p>
