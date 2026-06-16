<div align="center">

# 🔍 Lork-AI

### AI-Powered Research Operating System

A fully local, privacy-first AI search engine that crawls the web, builds knowledge graphs, and synthesizes cited research reports — all from your own machine.

**Next.js 16 · FastAPI · SQLite · Multi-LLM · Knowledge Graphs · Hybrid Ranking**

---

</div>

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
  - [Backend Setup](#1-backend-setup)
  - [Frontend Setup](#2-frontend-setup)
- [Configuration](#configuration)
  - [LLM Provider Configuration](#llm-provider-configuration)
  - [API Key Protection](#api-key-protection)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
  - [Web Crawling & Ingestion Pipeline](#1-web-crawling--ingestion-pipeline)
  - [Search & Research Pipeline](#2-search--research-pipeline)
  - [Knowledge Graph Construction](#3-knowledge-graph-construction)
  - [Hybrid Ranking Algorithm](#4-hybrid-ranking-algorithm)
- [API Reference](#api-reference)
- [Frontend Components](#frontend-components)
- [Database Schema](#database-schema)
- [Agent System](#agent-system)
- [Security](#security)
- [Testing & Verification](#testing--verification)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

**Lork-AI** is a self-hosted AI research operating system that lets you build your own private search engine. Instead of relying on third-party search APIs, Lork-AI crawls websites you specify, indexes the content locally, builds a knowledge graph of entities and relationships, and uses LLM-powered agents to synthesize comprehensive, cited research reports in response to your queries.

Everything runs on your machine — your data never leaves your system.

---

## Key Features

### 🌐 Web Crawling & Content Extraction
- **Async multi-page crawler** with configurable depth and page limits
- **Robots.txt compliance** — respects website crawling policies
- **Intelligent content extraction** — strips boilerplate (nav, footer, ads, scripts) and preserves meaningful content (paragraphs, headings, tables, code blocks)
- **Internal link discovery** for recursive depth-based crawling
- **Background crawl processing** — non-blocking, queued crawl jobs

### 🔎 Hybrid Search & Ranking
- **BM25 full-text search** via SQLite FTS5 virtual tables
- **Semantic vector search** using cosine similarity over document embeddings
- **Hybrid ranking formula**: `40% Semantic + 25% BM25 + 20% Authority + 15% Freshness + Click Bonus`
- **Click-through feedback loop** — documents gain ranking boosts based on user clicks
- **Configurable result limits** with score normalization

### 🧠 Knowledge Graph (GraphRAG)
- **LLM-powered entity extraction** — automatically identifies Companies, People, Technologies, Products, Events, and Concepts from crawled content
- **Relationship mapping** — discovers and stores typed edges between entities (e.g., `OpenAI --[BACKS]--> Cursor`)
- **PageRank centrality scoring** — computes authority scores for entities using NetworkX, with a pure-Python fallback
- **Interactive graph visualization** — canvas-based force-directed graph viewer in the frontend
- **Document-to-entity linking** — connects crawled pages to the entities they mention

### 📝 AI-Powered Research Reports
- **Single-pass LLM synthesis** — generates comprehensive Markdown reports with inline citations (`[1]`, `[2]`, etc.)
- **Source attribution** — every claim links back to its crawled source document
- **Follow-up recommendations** — suggests 4 related questions for deeper research
- **Search result caching** — instant `0ms` responses for previously-answered queries via SQLite cache

### 🔌 Multi-LLM Provider Support
- **Google Gemini** (primary, recommended) — `gemini-2.5-flash`
- **OpenAI** — `gpt-4o-mini`
- **Ollama** (local, offline) — any local model (default: `gemma3:270m`)
- **Mock/Simulated mode** — works without any LLM for testing and development
- Automatic provider detection and graceful fallback chain

### 🎨 Premium Minimalist UI
- **Dark monochrome design** with mouse-tracking spotlight effect
- **Collapsible sidebar** with search history and index stats
- **Slide-over drawers** for URL ingestion and knowledge graph inspection
- **Typewriter-style answer rendering** with Markdown formatting
- **Responsive layout** with smooth animations and micro-interactions

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 16)                    │
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Search   │  │  Answer   │  │  Source     │  │   Graph    │ │
│  │  Input    │  │  Card     │  │  List      │  │   Viewer   │ │
│  └─────┬────┘  └─────┬─────┘  └──────┬──────┘  └─────┬──────┘ │
│        │              │               │               │        │
│        └──────────────┴───────────────┴───────────────┘        │
│                            │ HTTP REST                          │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                            │                                    │
│  ┌─────────────────────────┴──────────────────────────────┐    │
│  │              API Layer (api/main.py)                     │    │
│  │   /api/search · /api/crawl · /api/graph · /api/history  │    │
│  └────┬──────────────┬──────────────┬──────────────┬───────┘    │
│       │              │              │              │            │
│  ┌────┴────┐   ┌─────┴─────┐  ┌────┴────┐   ┌────┴─────┐     │
│  │Orchestr.│   │  Crawler  │  │  Graph  │   │  Ranker  │     │
│  │ Agent   │   │  Service  │  │ Service │   │  Service │     │
│  └────┬────┘   └─────┬─────┘  └────┬────┘   └────┬─────┘     │
│       │              │              │              │            │
│  ┌────┴──────────────┴──────────────┴──────────────┴───────┐   │
│  │                   LLM Service                            │   │
│  │         Gemini · OpenAI · Ollama · Mock                  │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                       │
│  ┌──────────────────────┴───────────────────────────────────┐   │
│  │              SQLite Database (search_engine.db)           │   │
│  │  pages · pages_fts · page_embeddings · nodes · edges     │   │
│  │  crawl_queue · document_entities · search_history        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer        | Technology                                                     |
| ------------ | -------------------------------------------------------------- |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Lucide Icons |
| **Backend**  | Python 3.10+, FastAPI, Uvicorn, Pydantic                       |
| **Database** | SQLite with FTS5 full-text search                              |
| **Search**   | BM25 (FTS5), Cosine Similarity (vector embeddings)             |
| **Graph**    | NetworkX (directed graph + PageRank)                           |
| **Crawling** | httpx (async), BeautifulSoup4, robots.txt parser               |
| **LLM**      | Google Gemini API, OpenAI API, Ollama (local)                  |
| **Fonts**    | Geist Sans & Geist Mono (Google Fonts via next/font)           |

---

## Project Structure

```
search-system/
├── frontend/                          # Next.js 16 web application
│   ├── app/
│   │   ├── layout.tsx                 # Root layout, metadata, fonts
│   │   ├── page.tsx                   # Main search interface (landing + results)
│   │   ├── globals.css                # Global styles and animations
│   │   └── favicon.ico                # App favicon
│   ├── components/
│   │   ├── AnswerCard.tsx             # Typewriter-style Markdown answer renderer
│   │   ├── SourceList.tsx             # Cited sources with click tracking
│   │   ├── GraphViewer.tsx            # Canvas-based force-directed graph visualization
│   │   └── AgentTrace.tsx             # Agent execution trace/log viewer
│   ├── package.json                   # Node.js dependencies and scripts
│   ├── next.config.ts                 # Next.js configuration
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── postcss.config.mjs             # PostCSS config (Tailwind)
│   ├── eslint.config.mjs              # ESLint configuration
│   └── README.md                      # ← You are here
│
├── backend/                           # FastAPI Python backend
│   ├── api/
│   │   └── main.py                    # FastAPI app, all REST endpoints, middleware
│   ├── agents/
│   │   ├── base.py                    # AgentBus (logging) + BaseAgent class
│   │   ├── orchestrator.py            # Multi-agent pipeline coordinator
│   │   ├── search_agent.py            # Search query processor
│   │   ├── query_agent.py             # Query analysis and intent detection
│   │   ├── planner_agent.py           # Research plan formulation
│   │   ├── crawler_agent.py           # Crawl task delegation
│   │   ├── retrieval_agent.py         # Document retrieval
│   │   ├── extraction_agent.py        # Content extraction
│   │   ├── ranking_agent.py           # Result ranking
│   │   ├── entity_agent.py            # Named entity extraction
│   │   ├── graph_agent.py             # Knowledge graph operations
│   │   ├── citation_agent.py          # Citation formatting and attribution
│   │   ├── fact_checker.py            # Claim verification
│   │   ├── research_agent.py          # Research synthesis
│   │   ├── recommendation_agent.py    # Follow-up question generation
│   │   └── report_agent.py            # Report compilation
│   ├── services/
│   │   ├── llm.py                     # Multi-provider LLM service (Gemini/OpenAI/Ollama/Mock)
│   │   ├── database.py                # SQLite initialization and schema definitions
│   │   ├── crawler_service.py         # Async web crawler with content extraction
│   │   ├── indexer.py                 # BM25 + vector embedding search indexer
│   │   ├── ranker.py                  # Hybrid ranking with authority and freshness
│   │   └── graph_service.py           # Knowledge graph (NetworkX + PageRank)
│   ├── tests/
│   │   └── verify.py                  # End-to-end pipeline verification script
│   ├── .env                           # Environment variables (API keys) — NOT committed
│   ├── .env.example                   # Template for environment configuration
│   ├── requirements.txt               # Python dependencies
│   └── search_engine.db               # SQLite database file (auto-created)
```

---

## Prerequisites

Before setting up Lork-AI, ensure you have the following installed:

| Requirement        | Version   | Purpose                                       |
| ------------------ | --------- | --------------------------------------------- |
| **Node.js**        | ≥ 18.x    | Run the Next.js frontend                      |
| **npm**            | ≥ 9.x     | Install frontend dependencies                 |
| **Python**         | ≥ 3.10    | Run the FastAPI backend                        |
| **pip**            | ≥ 22.x    | Install Python dependencies                   |
| **Git**            | any       | Clone the repository                          |

**Optional (for LLM features):**

| Optional                  | Purpose                                                   |
| ------------------------- | --------------------------------------------------------- |
| **Gemini API Key**        | Best quality — cloud-based generation and embeddings      |
| **OpenAI API Key**        | Alternative cloud LLM provider                            |
| **Ollama**                | Run LLMs locally without any cloud dependency             |

> **Note:** Lork-AI works even without any LLM keys — it falls back to a built-in mock/simulated mode for testing. However, for meaningful research reports, at least one LLM provider is required.

---

## Installation & Setup

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd search-system/backend

# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

**Configure environment variables:**

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and add your API key(s):

```env
# Cloud API Configuration (Highly Recommended for reasoning & citations)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
OPENAI_API_KEY=your_openai_api_key_here

# Local Ollama Configuration (Fallback if no cloud keys are provided)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:270m
OLLAMA_EMBED_MODEL=gemma3:270m
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd search-system/frontend

# Install Node.js dependencies
npm install
```

---

## Configuration

### LLM Provider Configuration

Lork-AI automatically detects and selects the best available LLM provider in this priority order:

| Priority | Provider     | Trigger                          | Models Used                                     |
| -------- | ------------ | -------------------------------- | ------------------------------------------------ |
| 1st      | **Gemini**   | `GEMINI_API_KEY` is set in `.env` | `gemini-2.5-flash` (generation), `text-embedding-004` (embeddings) |
| 2nd      | **OpenAI**   | `OPENAI_API_KEY` is set in `.env` | `gpt-4o-mini` (generation), `text-embedding-3-small` (embeddings) |
| 3rd      | **Ollama**   | Ollama server is running locally  | Configurable via `OLLAMA_MODEL` env var           |
| 4th      | **Mock**     | No keys and no Ollama detected    | Built-in simulated responses for testing          |

### API Key Protection

Lork-AI supports optional API key authentication to protect backend endpoints:

1. Set `API_KEY` in your backend `.env` file
2. Set `NEXT_PUBLIC_API_KEY` in your frontend environment (or `.env.local`)
3. All API requests will include the key via the `x-api-key` header

If `API_KEY` is not set, endpoints are open (suitable for local-only use).

---

## Running the Application

You need **two terminal windows** — one for the backend and one for the frontend.

### Terminal 1: Start the Backend

```bash
cd search-system/backend
# Activate virtual environment first if not already active
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Start the FastAPI server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: **http://localhost:8000**

### Terminal 2: Start the Frontend

```bash
cd search-system/frontend

# Start the Next.js development server
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### Quick Verification (Optional)

To verify the full pipeline works end-to-end with sample data:

```bash
cd search-system/backend
python tests/verify.py
```

This script will:
1. Initialize the SQLite database
2. Insert 3 sample pages (Aider, Cursor, OpenHands)
3. Generate vector embeddings
4. Build a knowledge graph with entities and relationships
5. Run a full search pipeline query
6. Print the research report, citations, graph stats, and recommendations

---

## How It Works

### 1. Web Crawling & Ingestion Pipeline

When you submit a URL through the **"Ingest URL"** drawer:

```
URL Submitted → Crawl Queue (SQLite) → Async Fetch (httpx)
  → robots.txt Check → HTML Download → Content Extraction (BeautifulSoup)
    → Boilerplate Removal (nav, footer, ads, scripts)
    → Clean Text + Headings + Tables + Links + Images
      → Save to `pages` table → Index in FTS5 (`pages_fts`)
        → Generate Vector Embedding → Save to `page_embeddings`
          → LLM Entity Extraction → Save to `nodes` + `edges`
            → Compute PageRank → Update `pages.authority`
```

**Key details:**
- Crawling runs **in the background** — the UI is never blocked
- **Concurrency**: up to 5 simultaneous page fetches with 0.5s polite delay
- **Deep Research Mode** (toggle): increases crawl limits from 5 pages / depth 1 to 15 pages / depth 2
- Internal links are automatically discovered and queued for recursive crawling
- The crawl status badge in the sidebar shows live index page count

### 2. Search & Research Pipeline

When you type a query and press search:

```
Query → Cache Lookup (SQLite search_history)
  → [Cache Hit] → Return instant (0ms) cached result
  → [Cache Miss] → Hybrid Ranking Pipeline:
      ├── BM25 Search (FTS5 full-text matching)
      ├── Semantic Search (cosine similarity on embeddings)
      └── Knowledge Graph Subgraph Extraction
    → Merge & Rank (Hybrid Score Formula)
    → Build LLM Prompt (sources + graph context)
    → Single-Pass LLM Generation:
        ├── Cited Markdown Answer
        └── 4 Follow-up Recommendations
    → Cache Result to search_history
    → Return to Frontend
```

### 3. Knowledge Graph Construction

The knowledge graph is built **incrementally** as new pages are crawled:

- **Entity extraction**: The LLM identifies entities from page content and classifies them into 6 types:
  - `Company`, `Person`, `Technology`, `Product`, `Event`, `Concept`
- **Relationship extraction**: Discovers typed relationships between entities (e.g., `CREATED`, `DEVELOPED`, `POWERS`, `BACKS`)
- **PageRank computation**: Runs after each extraction pass to update entity authority scores
- **Document linking**: Each page is linked to the entities it mentions via the `document_entities` table
- **Authority propagation**: Page authority scores are computed as the average PageRank of their linked entities

### 4. Hybrid Ranking Algorithm

The ranking formula combines four signals with an additive click bonus:

```
Final Score = (0.40 × Semantic Similarity)
            + (0.25 × BM25 Relevance)
            + (0.20 × PageRank Authority)
            + (0.15 × Freshness Decay)
            + (0.02 × log(1 + click_count))
```

| Signal                | Weight | Description                                                       |
| --------------------- | ------ | ----------------------------------------------------------------- |
| **Semantic Similarity** | 40%    | Cosine similarity between query embedding and document embedding  |
| **BM25 Relevance**     | 25%    | FTS5 probabilistic keyword matching score                         |
| **PageRank Authority**  | 20%    | Entity-derived authority via knowledge graph centrality            |
| **Freshness Decay**     | 15%    | Exponential decay: `0.15 × e^(-0.05 × days_since_crawl)`         |
| **Click Bonus**         | Additive | Logarithmic user engagement signal: `0.02 × log(1 + clicks)`    |

Scores are min-max normalized per signal before combining.

---

## API Reference

All endpoints are served from `http://localhost:8000`. If `API_KEY` is configured, include `x-api-key: <your_key>` in request headers.

### `GET /api/search`

Run the full research pipeline for a query.

| Parameter | Type   | Required | Description          |
| --------- | ------ | -------- | -------------------- |
| `q`       | string | Yes      | The search query     |

**Response:**

```json
{
  "query": "open-source coding assistants",
  "report": {
    "title": "Research Report: open-source coding assistants",
    "content": "Markdown answer with [1] inline citations..."
  },
  "sources": [
    { "id": 1, "url": "https://...", "title": "...", "score": 0.85 }
  ],
  "graph": {
    "nodes": [{ "id": "Aider", "label": "Aider", "type": "Product" }],
    "links": [{ "source": "OpenAI", "target": "Aider", "relation": "POWERS" }]
  },
  "recommendations": ["question 1", "question 2", "question 3", "question 4"],
  "logs": []
}
```

---

### `POST /api/crawl`

Submit a URL for background crawling and indexing.

**Request body:**

```json
{
  "url": "https://example.com",
  "max_pages": 5,
  "max_depth": 1
}
```

**Response:**

```json
{
  "status": "queued",
  "message": "Crawling queued in background for: https://example.com"
}
```

---

### `GET /api/crawl/status`

Check the current crawling and indexing status.

**Response:**

```json
{
  "pages_crawled": 12,
  "queue_stats": { "pending": 2, "done": 10, "failed": 0 },
  "recent_queue": [
    { "url": "https://...", "status": "done", "depth": 0 }
  ]
}
```

---

### `GET /api/graph`

Retrieve the full knowledge graph (all nodes and edges).

**Response:**

```json
{
  "nodes": [
    { "id": "OpenAI", "label": "OpenAI", "type": "Company" }
  ],
  "links": [
    { "source": "OpenAI", "target": "Cursor", "relation": "BACKS" }
  ]
}
```

---

### `GET /api/history`

Get the 10 most recent search queries.

**Response:**

```json
[
  { "query": "open-source coding assistants", "created_at": "2026-06-16 12:00:00" }
]
```

---

### `POST /api/click`

Register a click on a source document (used for ranking feedback).

**Request body:**

```json
{
  "page_id": 1
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Click count incremented."
}
```

---

## Frontend Components

| Component                  | File                    | Purpose                                                                                                   |
| -------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------- |
| **Main Page**              | `app/page.tsx`          | Full search interface — landing screen, search input, result display, crawl drawer, graph drawer           |
| **AnswerCard**             | `components/AnswerCard.tsx` | Renders the LLM-generated Markdown answer with inline citation highlighting                            |
| **SourceList**             | `components/SourceList.tsx` | Displays ranked source documents with URLs, titles, scores, and click-to-open behavior                 |
| **GraphViewer**            | `components/GraphViewer.tsx` | Canvas-based interactive force-directed graph — drag nodes, zoom, color-coded entity types             |
| **AgentTrace**             | `components/AgentTrace.tsx` | Displays timestamped agent execution logs (for debugging and transparency)                             |

---

## Database Schema

Lork-AI uses a single **SQLite** database file (`backend/search_engine.db`) with the following tables:

| Table                | Purpose                                                     |
| -------------------- | ----------------------------------------------------------- |
| `pages`              | Crawled web pages (URL, title, content, authority, freshness, clicks) |
| `pages_fts`          | FTS5 virtual table for BM25 full-text search                |
| `page_embeddings`    | Vector embeddings (JSON-serialized float arrays) per page   |
| `crawl_queue`        | URL crawl job queue with status tracking (pending/crawling/done/failed) |
| `nodes`              | Knowledge graph entities (id, label, type, metadata)        |
| `edges`              | Knowledge graph relationships (source, target, relation, weight) |
| `document_entities`  | Many-to-many link between pages and graph entities          |
| `search_history`     | Cached search results for instant repeat query responses    |

---

## Agent System

Lork-AI includes a modular multi-agent architecture. The orchestrator coordinates the pipeline, while individual agents handle specialized tasks:

| Agent                       | File                          | Responsibility                                          |
| --------------------------- | ----------------------------- | ------------------------------------------------------- |
| **Orchestrator**            | `orchestrator.py`             | Coordinates the full research pipeline end-to-end       |
| **Search Agent**            | `search_agent.py`             | Processes and dispatches search queries                 |
| **Query Agent**             | `query_agent.py`              | Analyzes query intent and extracts keywords             |
| **Planner Agent**           | `planner_agent.py`            | Formulates research plans and strategies                |
| **Crawler Agent**           | `crawler_agent.py`            | Delegates web crawling tasks                            |
| **Retrieval Agent**         | `retrieval_agent.py`          | Retrieves relevant documents from the index             |
| **Extraction Agent**        | `extraction_agent.py`         | Extracts structured content from raw pages              |
| **Ranking Agent**           | `ranking_agent.py`            | Applies scoring and ranking to results                  |
| **Entity Agent**            | `entity_agent.py`             | Performs named entity recognition and classification    |
| **Graph Agent**             | `graph_agent.py`              | Manages knowledge graph operations                      |
| **Citation Agent**          | `citation_agent.py`           | Formats and attributes inline citations                 |
| **Fact Checker**            | `fact_checker.py`             | Verifies claims against source documents                |
| **Research Agent**          | `research_agent.py`           | Synthesizes research findings into coherent answers     |
| **Recommendation Agent**   | `recommendation_agent.py`     | Generates follow-up question suggestions                |
| **Report Agent**            | `report_agent.py`             | Compiles final structured research reports              |

All agents extend the `BaseAgent` class and communicate through the `AgentBus` logging system.

---

## Security

Lork-AI includes several security measures for safe local operation:

| Feature                      | Implementation                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| **CORS Restriction**         | Only `http://localhost:3000` and `http://127.0.0.1:3000` are allowed origins                |
| **API Key Authentication**   | Optional `x-api-key` header validation via `API_KEY` env var                                |
| **Security Headers**         | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy: no-referrer` |
| **Content Security Policy**  | `default-src 'self'; frame-ancestors 'none';`                                                |
| **HTTP Method Restriction**  | CORS only allows `GET` and `POST` methods                                                   |
| **Robots.txt Compliance**    | Crawler respects `robots.txt` rules before fetching any page                                |
| **Input Validation**         | URL format validation, empty query rejection, page existence checks                          |

---

## Testing & Verification

### Run the End-to-End Pipeline Test

```bash
cd search-system/backend

# Activate virtual environment
.venv\Scripts\activate

# Run verification
python tests/verify.py
```

**What the test does:**
1. Initializes the SQLite database schema
2. Inserts 3 sample pages about AI coding tools (Aider, Cursor, OpenHands)
3. Generates vector embeddings for all pages
4. Builds a knowledge graph with 5 entities and 3 relationships
5. Computes PageRank authority scores
6. Runs the full search pipeline with query: `"open-source coding assistants like Aider"`
7. Prints the research report, citations, graph stats, and recommendations

**Expected output sections:**
- `=== Initializing SQLite Database ===`
- `=== Populating Demo Content ===`
- `=== Generating Vector Embeddings ===`
- `=== Building Knowledge Graph ===`
- `=== Running Multi-Agent Search Pipeline ===`
- `=== PIPELINE OUTPUT RESULT ===`
- `=== Test Verification Completed Successfully ===`

---

## Troubleshooting

### Common Issues

| Issue                                    | Cause                                        | Solution                                                                                                |
| ---------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `Backend API is unreachable`             | FastAPI server not running                   | Start the backend with `uvicorn api.main:app --reload --port 8000`                                      |
| `Unauthorized. Invalid API Key.`         | API key mismatch                             | Ensure `API_KEY` in backend `.env` matches `NEXT_PUBLIC_API_KEY` in frontend                            |
| `No index match found`                   | No pages have been crawled yet               | Use the "Ingest URL" drawer to crawl a website first                                                    |
| `Generation failed`                      | LLM provider is misconfigured               | Check your `.env` file — ensure at least one API key is set, or Ollama is running                       |
| `Gemini API Error` / `OpenAI API Error`  | Invalid or expired API key                   | Verify your API key is correct and has not expired                                                       |
| `Ollama is offline`                      | Ollama service not started                   | Start Ollama with `ollama serve` and pull a model: `ollama pull gemma3:270m`                             |
| `BM25 Search Error`                      | FTS5 not available in SQLite build           | The system auto-falls back to FTS3; ensure SQLite is installed with full-text search support             |
| Frontend shows blank page                | Node modules not installed                   | Run `npm install` in the `frontend/` directory                                                           |
| Graph viewer shows no data               | No entities extracted yet                    | Crawl some pages first — entity extraction runs automatically after crawling                             |

### Checking LLM Provider Status

When the backend starts, check the logs for the active LLM provider:

```
INFO: LLM service using Gemini API (Cloud)          ← Gemini active
INFO: LLM service using OpenAI API (Cloud)          ← OpenAI active
INFO: LLM service using local Ollama (Model: ...)   ← Ollama active
WARNING: Running in Mock/Simulated mode              ← No LLM available
```

---

## License

This project is provided as-is for personal and educational use.

---

<div align="center">

**Built with ❤️ by the Lork-AI team**

</div>
