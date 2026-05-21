# Azure Compliance Intelligence Platform

[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20LangGraph%20%7C%20Azure-blue?style=flat-square)](https://azure.microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

An enterprise-grade, **Azure-native agentic compliance intelligence platform** designed to audit multimodal media content against dynamic regulatory policies. The system orchestrates an **agentic LangGraph workflow** fully integrated with the **Azure Ecosystem** to index audio-visual streams via **Azure Video Indexer**, query an **Azure AI Search** vector database via RAG, perform structured audit reasoning using **Azure OpenAI Service**, and synthesize detailed reports, all backed by a real-time policy management panel and monitored via **Azure Monitor**.

---

## 🏗️ System Architecture

The platform operates on a robust, asynchronous agentic workflow orchestrated by LangGraph and built entirely on **Azure PaaS services**, dividing compliance tasks into focused, decoupled, single-responsibility nodes.

Below is the system's operational architecture showing the ingestion, agentic auditing, and telemetry logging pipelines:

<img width="1957" height="1416" alt="image" src="pics/Azure_multimodel_complaince_Agent.png" />

*Figure 1: Full-scale Agentic Auditing & Policy Management Architecture.*

---

## 🚀 Key Features

* **Azure-Integrated LangGraph Orchestration**: Decouples indexing, retrieval, auditing, and report synthesis, utilizing dynamic conditional error-routing backed by **Azure Identity (DefaultAzureCredential)**.
* **Multimodal Audio-Visual Ingestion**: **Azure Video Indexer** extracts precise audio transcripts, visual OCR text, spatial-temporal face matches, and scene transitions.
* **Dynamic Azure AI Search Policy Management**: Upload corporate PDF policies, segment, embed via **Azure OpenAI Embeddings**, and index them into **Azure AI Search** in real-time, or purge them cleanly from both **Azure Storage** and vector indexes upon deletion.
* **Structured Auditing via Azure OpenAI**: Detects, categorizes, and scores compliance violations (`CRITICAL` vs. `WARNING`) and extracts exact textual evidence using structured JSON schemas powered by **Azure OpenAI (GPT-4o-mini)**.
* **Azure Cosmos DB Synchronization**: Syncs document ingestion, indexing states, and audit transaction records in **Azure Cosmos DB** in real-time.

---

## 🖥️ Operational Dashboard

| **Compliance Management Dashboard** | **Real-time Audit Results** |
|:---:|:---:|
|<img width="1547" height="927" alt="image" src="pics/front_page.png" />|<img width="1275" height="940" alt="image" src="pics/aduit_results.png" />|
| *Intuitive Glassmorphic dashboard with live ingestion monitoring* | *In-depth structured compliance reports & policy maps* |

---

## 🔍 Monitoring & Trace Observability

Production agent systems require high observability to inspect state evolution, node latencies, and third-party dependencies. This platform integrates full telemetry pipelines using **Azure Application Insights** and **LangSmith**.

### 1. Dependency & Latency Tracking (Azure Application Map)
With native OpenTelemetry instrumentation, the system maps all database calls, API routers, and AI services. The **Azure Application Map** acts as a live cockpit to:
* **Trace Node Latencies**: Measure execution overhead inside each LangGraph node and identify slow third-party API transitions.
* **Monitor API Pipelines**: Visualize real-time request volume, HTTP statuses, and backend bottlenecks under concurrent compliance audits.
* **Audit External Dependencies**: Detect failures or slow responses in Azure OpenAI, Azure Cosmos DB, or Azure AI Search immediately.

<img width="1738" height="918" alt="image" src="pics/Insights_app_map.png" />

*Figure 2: Live Azure Application Map showcasing service dependencies, request latencies, and execution streams.*

### 2. LangGraph Agentic Tracing (LangSmith)
Every execution run is tracked in **LangSmith** to monitor LLM invocations and StateGraph transitions:
* **Node Execution Sequence**: Verify that states are modified correctly as they pass from `indexer` to `rag_retriever`, `compliance_auditor`, and `report_synthesiser`.
* **Prompt Engineering & Token Costs**: Analyze input/output prompt structures and trace token counts to manage infrastructure expenses.
* **Model Debugging**: Diagnose dynamic agent decisions, tool invocation failures, and structured JSON-generation errors in real-time.

| **LangSmith Execution Stream** | **Step-by-Step State Tracing** |
|:---:|:---:|
|<img width="1702" height="936" alt="image" src="pics/langsmith_dashboard.png" />|<img width="1911" height="915" alt="image" src="pics/langsmith_working_output.png" />|
| *High-level runs overview detailing token counts, cost, latency, and status* | *Detailed step-by-step state visualization and LLM input/output pairs* |

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.10+), Uvicorn |
| **Agentic Framework** | LangGraph, LangChain Community |
| **LLMs & Embeddings** | Azure OpenAI (GPT-4o-mini, text-embedding-3-large) |
| **Storage & Search** | Azure Cosmos DB (NoSQL), Azure AI Search (Vector Store), Azure Blob Storage |
| **Media AI** | Azure Video Indexer (VI) |
| **Frontend** | React 18, Vite, Vanilla CSS (Glassmorphism & Sleek Dark Mode) |
| **Telemetry & Logging** | OpenTelemetry, Azure Monitor Application Insights, LangSmith |

---

## 📦 Getting Started

### Prerequisites

Ensure you have the following installed:
* [Python 3.10+](https://www.python.org/)
* [Node.js v18+](https://nodejs.org/)
* [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (for `DefaultAzureCredential` authentication)

### 1. Environment Setup

Create a `.env` file inside the `ComplianceQAPipeline` directory containing your Azure credentials:

```env
# Azure OpenAI Settings
AZURE_OPENAI_API_KEY="your-api-key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o-mini"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-large"

# Azure AI Search Settings
AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_API_KEY="your-search-api-key"
AZURE_SEARCH_INDEX_NAME="compliance-rules-index"

# Azure Cosmos DB Settings
COSMOS_ENDPOINT="https://your-cosmos-account.documents.azure.com:443/"
COSMOS_KEY="your-cosmos-key"

# Azure Video Indexer Settings (Authenticated via DefaultAzureCredential)
AZURE_VI_NAME="Video-Indexer-Compliance-Intelligence"
AZURE_VI_LOCATION="eastus"
AZURE_VI_ACCOUNT_ID="your-vi-account-id"
AZURE_SUBSCRIPTION_ID="your-azure-subscription-id"
AZURE_RESOURCE_GROUP="your-resource-group-name"

# Azure Monitor Telemetry Settings (Optional but Recommended)
APPLICATIONINSIGHTS_CONNECTION_STRING="your-app-insights-connection-string"

# LangSmith Settings (Optional but Recommended)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-api-key"
LANGCHAIN_PROJECT="Azure-Compliance-Intelligence-Platform"
```

### 2. Backend Installation & Execution

We recommend using `uv` for fast package management:

```bash
# Navigate to project root
cd ComplianceQAPipeline

# Install dependencies and sync virtual environment
uv sync

# Start the FastAPI backend server
uv run uvicorn backend.src.api.server:app --reload --port 8000
```

Alternatively, using standard pip:
```bash
pip install -e .
uvicorn backend.src.api.server:app --reload --port 8000
```

To run a CLI simulation of a compliance video audit run:
```bash
uv run python main.py
```

### 3. Frontend Installation & Execution

```bash
# Navigate to the frontend directory from the project root
cd ComplianceQAPipeline/frontend

# Install UI packages
npm install

# Run the developer dashboard
npm run dev
```

Open `http://localhost:5173` in your browser to interact with the dashboard.