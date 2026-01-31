<p align="center">
  <h1 align="center">🎯 Rizzume</h1>
  <p align="center">
    <strong>AI-Powered Resume Scoring with RAG Technology</strong>
  </p>
  <p align="center">
    Intelligent resume analysis that matches candidates to job requirements using semantic understanding
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/Ollama-LLM-purple?style=for-the-badge" alt="Ollama">
  <img src="https://img.shields.io/badge/Groq-LLM-orange?style=for-the-badge" alt="Groq">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

---

## ✨ Overview

**Rizzume** is an intelligent resume scoring system that leverages **Retrieval-Augmented Generation (RAG)** to evaluate how well a candidate's resume matches a job description. Unlike simple keyword matching, Rizzume uses semantic understanding to provide nuanced, explainable scoring.

### 🔑 Key Features

- 🤖 **AI-Powered Analysis** — Supports Ollama (local) or Groq (cloud) LLMs
- 📊 **RAG-Based Scoring** — Semantic retrieval ensures relevant resume sections are evaluated
- 🎯 **Category-Based Breakdown** — Scores across Education, Experience, Technical Skills, and Soft Skills
- 💡 **Explainable Results** — Each score comes with reasoning and evidence from the resume
- 📄 **PDF Support** — Upload resumes and job descriptions as PDFs or plain text
- 🌙 **Modern UI** — Beautiful dark/light theme with responsive design
- 🐳 **Docker Ready** — One-command deployment with Docker Compose

---

## 💡 Why I Built This

### The Problem

I noticed that there were **tons of websites charging money** for resume scoring services. After using several of them, I realized most resume scorers are *horrible*. I spoke with a bunch of HR professionals and recruiters, and **no one liked traditional ATS systems** or the results they produce. The existing solutions felt:

- 💸 **Overpriced** — Charging for basic functionality that should be free
- 🤖 **Opaque** — No explanation of *why* a resume scored a certain way
- 📋 **Keyword-focused** — Missing the semantic meaning behind requirements
- 🔒 **Closed-source** — No way to customize or run locally

### My Solution

I wanted to create a resume scorer that is:

1. **🆓 Free & Open Source** — Accessible to everyone, no paywalls
2. **🏠 Runs Locally** — Your resume data never leaves your machine
3. **🧠 Actually Smart** — Uses semantic understanding, not just keyword matching
4. **📖 Transparent** — Shows exactly why each score was given

### Why RAG Architecture?

Here's the thing: I know modern LLMs have **huge context windows** that can easily fit an entire resume. But those large models require expensive cloud APIs or powerful GPUs.

I wanted Rizzume to work with **small, local models** (like `qwen3:1.7b` or `gemma3:12b`) that anyone can run on their laptop. These smaller models don't have the luxury of massive context windows, so I needed a smarter approach.

#### How I Mimicked My Own Process

I observed **how I manually score resumes** and realized I was essentially:

1. **Reading the job description** and forming questions in my head
2. **Asking those questions to the resume** — "Does this person have a B.Tech?", "Do they have 3+ years of Python experience?"
3. **Finding the relevant sections** in the resume to answer each question
4. **Scoring based on the evidence** I found

So that's exactly what Rizzume does:

```
JD → Structured Questions → RAG Retrieval → Focused Scoring
```

**The structured question categories:**
- 📚 **Education** — Degree requirements, certifications
- 💼 **Experience** — Years of experience, specific roles  
- 🛠️ **Technical Skills** — Programming languages, tools, frameworks
- 🤝 **Soft Skills** — Communication, leadership, collaboration
- ⭐ **Mandatory vs Optional** — Weighted importance

By using **RAG to retrieve only the relevant chunks** for each question, I can:
- ✅ Use smaller, faster models that run locally
- ✅ Get more accurate answers (focused context = better responses)
- ✅ Provide detailed explanations with evidence
- ✅ Give users full control over how scoring works

This architecture means **you own your data**, and you can run the entire system on your personal machine without sending your resume to any external service.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│   Landing → Input (Resume + JD) → Loading → Analysis Dashboard   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │  JD Question    │   │   RAG Resume    │   │   Ollama      │  │
│  │  Generator      │──▶│   Scorer        │──▶│   Client      │  │
│  └─────────────────┘   └─────────────────┘   └───────────────┘  │
│          │                     │                                 │
│          ▼                     ▼                                 │
│  ┌─────────────────┐   ┌─────────────────┐                      │
│  │  Ollama LLM     │   │ SentenceTransf. │                      │
│  │  (qwen3:1.7b)   │   │  Embeddings     │                      │
│  └─────────────────┘   └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 How It Works

### 1️⃣ Job Description Analysis
The system extracts requirements from the job description and converts them into **atomic screening questions** across four categories:
- **Education** — Degree requirements, certifications
- **Experience** — Years of experience, specific roles
- **Technical Skills** — Programming languages, tools, frameworks
- **Soft Skills** — Communication, leadership, collaboration

### 2️⃣ Resume Chunking & Indexing
The resume is split into semantic chunks and embedded using **SentenceTransformers** to create a searchable vector index.

### 3️⃣ RAG Retrieval
For each screening question, the system retrieves the **top-k most relevant chunks** from the resume using cosine similarity.

### 4️⃣ LLM Scoring
Each question is evaluated by the LLM with the retrieved evidence, producing:
- **Score (0-10)** — How well the requirement is met
- **Answer** — Direct yes/no response
- **Reasoning** — Explanation referencing the resume evidence

### 5️⃣ Aggregate Results
Scores are aggregated by category and overall, providing a comprehensive match analysis.

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Required)
- **Git**

### ⚡ One-Command Start (Recommended)

The easiest way to run Rizzume. This script handles environment setup, installs the AI model, and starts the application.

```bash
# Clone the repository
git clone https://github.com/yourusername/rizzume.git
cd final_resume_scorer

# Run the auto-setup script
./start.sh
```

That's it! Access the app at:
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend**: http://localhost:8000

#### Available Scripts

| Script | Description |
|--------|-------------|
| `./start.sh` | **Automated Setup & Start** (Recommended) |
| `./run.sh` | Start in production mode (Docker) |
| `./dev.sh` | Start in development mode (Local or Docker) |
| `./stop.sh` | Stop all containers |

#### Docker Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up --build -d

# Stop everything
docker-compose down
```

---

### 🖥️ Option 2: Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup

```bash
# Navigate to project root
cd final_resume_scorer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export EMBED_MODEL_NAME="all-MiniLM-L6-v2"
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_DEFAULT_MODEL="qwen3:1.7b"

# Start the backend
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd rizzume-web-app

# Install dependencies
npm install

# Start development server
npm run dev
```

</details>

### Ollama Setup

```bash
# Install Ollama (https://ollama.ai)
# Then pull the model
ollama pull qwen3:1.7b

# Ensure Ollama is running
ollama serve
```

---

## 📁 Project Structure

```
final_resume_scorer/
├── app/                          # FastAPI Backend
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Pydantic settings & configuration
│   ├── routes/
│   │   └── scoring_route.py      # API endpoints (/score, /estimate-tokens)
│   ├── service/
│   │   ├── jd_question_generator.py   # JD → Questions using LLM
│   │   ├── resume_rag_scorer.py       # RAG scoring pipeline
│   │   ├── embedding_service.py       # SentenceTransformer embeddings
│   │   ├── chunking.py                # Resume text chunking
│   │   └── ollama_client.py           # Ollama API client
│   ├── prompts/
│   │   └── jd_prompts.py         # LLM system prompts
│   ├── schemas/                  # Pydantic models
│   ├── helper/                   # Utility functions
│   └── validator/                # Input validation
│
├── rizzume-web-app/              # Next.js Frontend
│   ├── app/
│   │   └── page.tsx              # Main application flow
│   ├── components/
│   │   ├── landing-hero.tsx      # Welcome screen
│   │   ├── data-input-step.tsx   # Resume & JD upload
│   │   ├── loading-state.tsx     # Processing indicator
│   │   ├── analysis-layout.tsx   # Results dashboard
│   │   ├── question-card.tsx     # Individual question display
│   │   └── ui/                   # Radix UI components
│   ├── lib/
│   │   └── api.ts                # Backend API client
│   └── Dockerfile                # Frontend container config
│
├── Dockerfile                    # Backend production container
├── Dockerfile.dev                # Backend development container
├── docker-compose.yml            # Multi-container orchestration
├── requirements.txt              # Python dependencies
├── run.sh                        # 🚀 Production start script
├── dev.sh                        # 🔧 Development start script
├── stop.sh                       # 🛑 Stop all containers
└── .env                          # Environment variables
```

---

## 🔧 Configuration

### General Settings

| Environment Variable | Description | Default |
|---------------------|-------------|---------:|
| `EMBED_MODEL_NAME` | SentenceTransformer model name | **Required** |
| `MAX_JD_CHARS` | Max job description length | `8000` |
| `MAX_RESUME_CHARS` | Max resume length | `20000` |
| `MAX_PDF_PAGES` | Max PDF pages to process | `20` |

### 🧠 LLM Provider Configuration

Rizzume supports **multiple LLM providers**. Switch between them via environment variables:

| Environment Variable | Description | Default |
|---------------------|-------------|---------:|
| `LLM_PROVIDER` | Provider to use: `ollama` or `groq` | `ollama` |

#### Ollama (Local, Free)

| Variable | Description | Default |
|----------|-------------|---------:|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_DEFAULT_MODEL` | Model name | `qwen3:1.7b` |

```bash
# .env for Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen3:1.7b
```

#### Groq (Cloud, Fast)

| Variable | Description | Default |
|----------|-------------|---------:|
| `GROQ_API_KEY` | Your Groq API key | **Required** |
| `GROQ_MODEL` | Model name | `llama-3.3-70b-versatile` |

```bash
# .env for Groq
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

> 💡 **Get your Groq API key** at [console.groq.com/keys](https://console.groq.com/keys) — it's free!

---

## 📡 API Endpoints

### `POST /score`
Score a resume against a job description.

**Request** (`multipart/form-data`):
- `jd_file` or `jd_text` — Job description (PDF or text)
- `resume_file` or `resume_text` — Resume (PDF or text)

**Response**:
```json
{
  "success": true,
  "result": {
    "questions": [...],
    "average_score": 7.5
  },
  "jd_text_length": 2500,
  "resume_text_length": 4200,
  "questions": {...}
}
```

### `POST /estimate-tokens`
Estimate token usage before full analysis.

### `GET /health`
Health check endpoint.

### `GET /metrics`
Basic request metrics.

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — High-performance async web framework
- **Pydantic** — Data validation and settings management
- **Ollama** — Local LLM inference
- **SentenceTransformers** — Semantic text embeddings
- **NumPy** — Efficient vector operations

### Frontend
- **Next.js 16** — React framework with App Router
- **TypeScript** — Type-safe JavaScript
- **Tailwind CSS** — Utility-first styling
- **Radix UI** — Accessible component primitives
- **Recharts** — Data visualization
- **Lucide Icons** — Beautiful icons

---

## 🎨 Features Showcase

### 📝 Smart Input
- Drag-and-drop PDF upload
- Direct text input option
- Real-time token estimation

### 📊 Detailed Analysis
- Category-wise score breakdown
- Per-question scores with reasoning
- Evidence highlighting from resume
- Interactive filtering by category and score

### 🌓 Modern Design
- Responsive layout
- Dark/Light theme toggle
- Smooth animations
- Accessible components

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  <strong>Built with ❤️ by Shubhdeep Das</strong>
</p>
