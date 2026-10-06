# 🤖 AI RAG Chatbot Agent

A production-oriented **Retrieval-Augmented Generation (RAG) chatbot** built using **Gemini 2.5 Flash, LangGraph, PostgreSQL, Pinecone, Sentence Transformers, and Streamlit**.

The application supports both:

- 🌐 **General AI conversations**
- 📄 **Question answering from uploaded documents**

Users can upload **PDF, DOCX, or TXT files**, which are processed, chunked, stored in PostgreSQL, converted into embeddings, and indexed in Pinecone for semantic retrieval.

The chatbot also uses **PostgreSQL-backed LangGraph memory** to maintain conversation history across different chat threads.

---

## ✨ Features

### 💬 General AI Chat

Users can ask normal questions such as:

```text
What is machine learning?
```

When no relevant document context is found, the chatbot answers using **Gemini 2.5 Flash's general knowledge**.

The UI displays:

```text
🌐 General knowledge
```

---

### 📄 Document Question Answering

Users can upload supported documents directly from the Streamlit sidebar.

Supported formats:

```text
PDF
DOCX
TXT
```

The system:

```text
Upload Document
       ↓
Extract Text
       ↓
Split into Chunks
       ↓
Store Chunks in PostgreSQL
       ↓
Generate Embeddings
       ↓
Store Vectors in Pinecone
       ↓
Semantic Search
       ↓
Retrieve Relevant Chunks
       ↓
Send Context to Gemini
       ↓
Generate Answer
```

When relevant document information is retrieved, the UI displays:

```text
📄 From uploaded document
```

---

## 🧠 Conversation Memory

The application uses:

```text
LangGraph
    +
PostgreSQL
    +
PostgresSaver
```

to maintain conversation state.

Each conversation receives a unique thread ID such as:

```text
streamlit-7b8d91c2...
```

LangGraph uses this thread ID to retrieve the correct conversation history.

This allows the chatbot to understand follow-up questions within the same conversation.

Example:

```text
User:
What is machine learning?

Assistant:
Machine learning is a branch of artificial intelligence...

User:
What are its main types?
```

The second question can be interpreted using the previous conversation context.

---

## 🗂️ Multiple Conversations

The application supports multiple chat threads.

The sidebar provides:

```text
💬 Conversations

Current Thread ID

Previous Chats

🆕 New Conversation
```

Each new conversation receives its own unique thread ID.

The first user message is automatically used to create the conversation title.

For example:

```text
What is machine learning?
```

can become:

```text
What is machine learning?
```

in the previous-chat list.

Users can switch between conversations and restore their saved LangGraph conversation history.

---

# 🏗️ Current Architecture

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │  Streamlit  │
                    │     UI      │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Semantic Search │
                  └────────┬────────┘
                           │
                           ▼
                     ┌──────────┐
                     │ Pinecone │
                     └────┬─────┘
                          │
                     Chunk IDs
                          │
                          ▼
                  ┌────────────────┐
                  │   PostgreSQL   │
                  │ Document Chunks│
                  └───────┬────────┘
                          │
                   Retrieved Context
                          │
                          ▼
                  ┌────────────────┐
                  │   LangGraph    │
                  └───────┬────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Gemini 2.5 Flash │
                 └────────┬─────────┘
                          │
                          ▼
                     AI Response
                          │
                          ▼
                       Streamlit
```

---

# 📚 RAG Pipeline

The current RAG pipeline works as follows.

## 1. Document Upload

Documents are uploaded through the Streamlit sidebar.

```text
User
 ↓
Streamlit File Uploader
 ↓
uploaded_documents/
```

Uploaded documents are temporarily stored inside:

```text
uploaded_documents/
```

---

## 2. Document Loading

The document loader extracts text depending on the file type.

File:

```text
app/ingestion/loader.py
```

Libraries used include:

```text
pypdf
python-docx
```

PDF documents are processed page by page so that page information can be retained.

---

## 3. Document Chunking

File:

```text
app/ingestion/chunker.py
```

The application uses:

```python
RecursiveCharacterTextSplitter
```

Current configuration:

```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

This converts large documents into smaller pieces suitable for embedding generation and retrieval.

---

## 4. PostgreSQL Storage

Document metadata and text chunks are stored in PostgreSQL.

The primary tables are:

```text
documents
document_chunks
```

### `documents`

Stores information such as:

```text
id
filename
file_type
file_path
created_at
```

### `document_chunks`

Stores:

```text
id
document_id
chunk_number
content
page_number
created_at
```

Each chunk is connected to its original document using:

```text
document_id
```

---

## 5. Embedding Generation

File:

```text
app/retrieval/embeddings.py
```

The project uses the Sentence Transformers model:

```text
all-MiniLM-L6-v2
```

Embedding dimension:

```text
384
```

Embeddings are normalized before being sent to Pinecone.

---

## 6. Pinecone Vector Storage

File:

```text
app/retrieval/pinecone_store.py
```

Each PostgreSQL document chunk is converted into an embedding and uploaded to Pinecone.

Each vector contains metadata such as:

```text
chunk_id
document_id
chunk_number
filename
page_number
```

Pinecone is therefore responsible for **vector similarity search**, while PostgreSQL remains the primary storage location for the actual document text.

---

## 7. Semantic Search

File:

```text
app/retrieval/vector_search.py
```

When the user asks a question:

```text
User Question
      ↓
Sentence Transformer
      ↓
Query Embedding
      ↓
Pinecone
      ↓
Top-K Similar Vectors
      ↓
Chunk IDs
      ↓
PostgreSQL
      ↓
Full Chunk Content
```

The current application retrieves:

```python
top_k = 5
```

results.

---

## 8. Document Relevance Detection

The application currently uses a semantic similarity threshold:

```python
DOCUMENT_RELEVANCE_THRESHOLD = 0.40
```

If the best retrieved result meets the threshold:

```text
score >= 0.40
```

the retrieved document chunks are supplied to Gemini.

The response is marked:

```text
📄 From uploaded document
```

If the threshold is not met, no document context is supplied and Gemini answers using general knowledge.

The response is marked:

```text
🌐 General knowledge
```

---

## 9. LangGraph

LangGraph controls the chatbot workflow and conversation state.

Important files:

```text
app/state.py
app/nodes.py
app/graph.py
app/graph_runtime.py
```

The graph currently follows a simple workflow:

```text
START
  ↓
Chatbot Node
  ↓
END
```

The graph state contains:

```text
messages
context
```

`messages` stores conversation history.

`context` contains relevant document information retrieved for the current question.

---

## 10. Gemini 2.5 Flash

The application currently uses:

```text
Gemini 2.5 Flash
```

through:

```text
langchain-google-genai
```

Gemini receives:

```text
System Instructions
        +
Retrieved Document Context
        +
Conversation History
        +
Current User Question
```

When document context exists, Gemini is instructed to use the retrieved information as the primary source.

When document context is unavailable, Gemini answers using general knowledge.

---

# 🧰 Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.11 |
| Frontend | Streamlit |
| LLM | Gemini 2.5 Flash |
| LLM Integration | LangChain Google GenAI |
| Workflow | LangGraph |
| Conversation Memory | LangGraph PostgresSaver |
| Relational Database | PostgreSQL |
| Vector Database | Pinecone |
| Embedding Model | all-MiniLM-L6-v2 |
| Embedding Library | Sentence Transformers |
| Text Splitting | LangChain Text Splitters |
| PDF Processing | PyPDF |
| DOCX Processing | python-docx |
| Environment Management | uv |
| Configuration | python-dotenv |

---

# 📁 Project Structure

A typical project structure is:

```text
AI_Chatbot_Agent/
│
├── app/
│   │
│   ├── __init__.py
│   │
│   ├── state.py
│   ├── nodes.py
│   ├── graph.py
│   ├── graph_runtime.py
│   ├── chat_threads.py
│   │
│   ├── ingestion/
│   │   │
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── database.py
│   │   └── ingest.py
│   │
│   └── retrieval/
│       │
│       ├── __init__.py
│       ├── embeddings.py
│       ├── pinecone_store.py
│       └── vector_search.py
│
├── uploaded_documents/
│
├── index_documents.py
├── streamlit_app.py
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Move into the project:

```bash
cd AI_Chatbot_Agent
```

---

## 2. Install `uv`

If `uv` is not installed:

```bash
pip install uv
```

Verify:

```bash
uv --version
```

---

## 3. Create the Environment

Create the virtual environment:

```bash
uv venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

---

## 4. Install Dependencies

If the project already contains `pyproject.toml` and `uv.lock`:

```bash
uv sync
```

Alternatively, the main dependencies can be installed using:

```bash
uv add streamlit
uv add python-dotenv
uv add psycopg
uv add langgraph
uv add langgraph-checkpoint-postgres
uv add langchain
uv add langchain-google-genai
uv add langchain-text-splitters
uv add sentence-transformers
uv add pinecone
uv add pypdf
uv add python-docx
```

---

# 🐘 PostgreSQL Setup

Install PostgreSQL and create a database.

Example database:

```text
chatbot_db
```

Open PostgreSQL:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -p 5432 -d chatbot_db
```

---

## Document Tables

The application uses tables similar to:

```sql
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```sql
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE
);
```

The application also creates a `chat_threads` table for conversation management.

LangGraph's `PostgresSaver` creates the checkpoint tables required for conversation memory.

---

# 🌲 Pinecone Setup

Create a Pinecone index using:

```text
Dimension: 384
Metric: cosine
```

Example index name:

```text
ai-chatbot-rag-384
```

The dimension must match the Sentence Transformer embedding model:

```text
all-MiniLM-L6-v2
```

which produces:

```text
384-dimensional embeddings
```

---

# 🔐 Environment Variables

Create a `.env` file in the project root.

```env
GEMINI_API_KEY=your_google_gemini_api_key

DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/chatbot_db

PINECONE_API_KEY=your_pinecone_api_key

PINECONE_INDEX_NAME=ai-chatbot-rag-384
```

Do **not** commit `.env` to GitHub.

Add it to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
uploaded_documents/
*.pyc
```

---

# ▶️ Running the Application

From the project directory:

```powershell
uv run --active streamlit run streamlit_app.py
```

Streamlit should provide a local URL similar to:

```text
http://localhost:8501
```

Open it in your browser.

---

# 🧪 Testing the Chatbot

## General Knowledge

Ask:

```text
What is machine learning?
```

Expected source:

```text
🌐 General knowledge
```

---

## Document RAG

Upload a PDF, DOCX, or TXT document.

Wait until the application displays:

```text
uploaded successfully
```

and confirms that chunks were indexed.

Then ask:

```text
What is this document about?
```

or:

```text
Summarize the uploaded document.
```

or a specific question such as:

```text
What does the document say about machine learning?
```

When relevant information is retrieved, the chatbot should display:

```text
📄 From uploaded document
```

---

# 🧠 Conversation Memory Test

Start with:

```text
My favorite programming language is Python.
```

Then ask:

```text
What programming language did I say I like?
```

The chatbot should use the conversation history stored through LangGraph/PostgreSQL.

Create a new conversation using:

```text
🆕 New Conversation
```

The new chat receives a different thread ID and independent conversation history.

---

# 🔎 Current Retrieval Strategy

The current implementation uses:

```text
Semantic Search
```

with:

```text
Sentence Transformers
        ↓
Pinecone
        ↓
Top-K Results
        ↓
PostgreSQL Chunks
        ↓
Gemini
```

This is the current MVP retrieval architecture.

---

# 🚧 Planned Retrieval Architecture

The next stages of the project will improve retrieval quality.

Planned architecture:

```text
                    User Query
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     Semantic Search          Keyword Search
        Pinecone              PostgreSQL FTS
            │                       │
            └───────────┬───────────┘
                        ▼
                 Reciprocal Rank
                    Fusion
                     (RRF)
                        │
                        ▼
                    Reranker
                        │
                        ▼
                 Best Documents
                        │
                        ▼
                  RAG Context
                        │
                        ▼
                 Gemini / LLM
                        │
                        ▼
                     Answer
```

---

# 🗺️ Development Roadmap

### Phase 1 — Basic LangGraph Chatbot

- [x] Gemini integration
- [x] LangGraph state
- [x] Chatbot node
- [x] Basic graph workflow

### Phase 2 — PostgreSQL Memory

- [x] PostgreSQL setup
- [x] LangGraph PostgresSaver
- [x] Thread-based memory
- [x] Multiple conversations
- [x] Conversation titles
- [x] Previous chat loading

### Phase 3 — Document Ingestion

- [x] PDF loading
- [x] DOCX loading
- [x] TXT loading
- [x] Document chunking
- [x] PostgreSQL document storage
- [x] Streamlit file upload

### Phase 4 — Vector Search

- [x] Sentence Transformer embeddings
- [x] Pinecone setup
- [x] Vector indexing
- [x] Semantic search
- [x] PostgreSQL chunk retrieval
- [x] RAG context generation

### Phase 5 — PostgreSQL Full-Text Search

- [ ] Add PostgreSQL FTS
- [ ] Keyword-based retrieval
- [ ] Rank keyword results

### Phase 6 — Hybrid Search + RRF

- [ ] Combine semantic search and FTS
- [ ] Implement Reciprocal Rank Fusion
- [ ] Deduplicate retrieved chunks
- [ ] Improve retrieval relevance

### Phase 7 — Reranking

- [ ] Add reranking model
- [ ] Rerank hybrid retrieval results
- [ ] Select highest-quality context

### Phase 8 — LangGraph Retrieval Workflow

- [ ] Move retrieval deeper into LangGraph
- [ ] Add retrieval nodes
- [ ] Add routing logic
- [ ] Improve RAG state management

### Phase 9 — Agentic Capabilities

- [ ] Query routing
- [ ] Tool selection
- [ ] Web search tools
- [ ] External API tools
- [ ] Intelligent fallback behavior

### Phase 10 — MCP

- [ ] Model Context Protocol integration
- [ ] External tool connections
- [ ] Expand chatbot capabilities

### Phase 11 — Production API & Frontend

- [ ] FastAPI backend
- [ ] Production frontend
- [ ] Authentication
- [ ] User-specific conversations
- [ ] Document management
- [ ] Logging
- [ ] Monitoring
- [ ] Deployment

---

# 🔮 Self-Healing RAG — Future Goal

A major future goal is to extend the project into a **Self-Healing RAG Pipeline**.

The planned architecture is:

```text
User Query
    ↓
Query Processing
    ↓
Hybrid Retrieval
    ↓
RRF
    ↓
Reranking
    ↓
Context Construction
    ↓
LLM Generation
    ↓
Critic / Evaluation Agent
    ↓
Is the answer good?
    │
    ├── YES → Return Answer
    │
    └── NO
         ↓
     Self-Healing Loop
         ↓
     Rewrite Query
         ↓
     Retrieve Again
         ↓
     Rerank Again
         ↓
     Regenerate Answer
         ↓
     Evaluate Again
```

The critic/evaluation layer can eventually evaluate responses for:

- Factual accuracy
- Relevance
- Completeness
- Hallucinations
- Context support
- Retrieval quality

If an answer fails evaluation, the system can retry the relevant part of the RAG pipeline.

---

# 🔒 Security Notes

Never commit API keys or database passwords to GitHub.

Keep credentials inside:

```text
.env
```

The `.env` file should always be included in:

```text
.gitignore
```

For production deployment, use a secure secrets-management solution rather than storing production credentials directly in source code.

---

# ⚠️ Current Limitations

The current version is still under active development.

Some current limitations include:

- Retrieval currently uses semantic search only.
- PostgreSQL Full-Text Search is not implemented yet.
- Hybrid retrieval is not implemented yet.
- RRF is not implemented yet.
- Reranking is not implemented yet.
- Document relevance currently depends on a fixed similarity threshold.
- Conversation source labels are maintained mainly at the Streamlit UI layer.
- Authentication and user-level isolation are not yet implemented.
- Production monitoring and evaluation are not yet implemented.

These limitations are planned to be addressed in future phases.

---

# 💡 Why This Project?

Traditional LLM chatbots rely primarily on information learned during model training.

A RAG system allows an LLM to retrieve external/private information before generating an answer.

This project combines:

```text
LLM
+
Conversation Memory
+
Private Documents
+
Vector Search
+
Relational Storage
+
Workflow Orchestration
```

to build a more practical AI assistant.

The long-term goal is to evolve the application from a basic RAG chatbot into a more reliable **production-oriented, self-healing RAG system**.

---

# 🛠️ Main Technologies

**Gemini 2.5 Flash**

Used as the primary Large Language Model for answer generation.

**LangGraph**

Used to manage chatbot workflow, state, and conversation execution.

**PostgreSQL**

Used for document storage, document chunks, conversation thread information, and LangGraph checkpoint persistence.

**Pinecone**

Used as the vector database for semantic similarity search.

**Sentence Transformers**

Used to generate local text embeddings with:

```text
all-MiniLM-L6-v2
```

**Streamlit**

Used to build the current chatbot user interface.

---

# 📌 Current Project Status

Current working stage:

```text
General Chat
     +
PostgreSQL Conversation Memory
     +
Multiple Conversation Threads
     +
Document Upload
     +
Document Ingestion
     +
Sentence Transformer Embeddings
     +
Pinecone Vector Search
     +
Semantic Retrieval
     +
RAG Context
     +
Gemini 2.5 Flash
     +
Streamlit UI
```

Next major development step:

```text
PostgreSQL Full-Text Search
            ↓
Hybrid Search
            ↓
Reciprocal Rank Fusion
            ↓
Reranking
```

---

# 👨‍💻 Author

**Murali Krishna**

AI / Machine Learning & Generative AI Developer

Project:

```text
AI_Chatbot_Agent
```

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

Contributions, suggestions, and improvements are welcome.

---

## 📄 License

Add the appropriate license for the repository before public or commercial distribution.

A common choice for open-source projects is the **MIT License**.