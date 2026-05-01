# 🧠 CodeCritic AI - Complete Architecture Walkthrough

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Flow Pipeline](#data-flow-pipeline)
4. [RAG Implementation](#rag-implementation)
5. [AST Analysis & Graph Creation](#ast-analysis--graph-creation)
6. [Code Chunking Strategy](#code-chunking-strategy)
7. [Retrieval System](#retrieval-system)
8. [Agentic Workflow](#agentic-workflow)
9. [Frontend & API](#frontend--api)
10. [Component Deep Dives](#component-deep-dives)

---

## Project Overview

**CodeCritic AI** is an AI-powered codebase assistant that combines multiple advanced techniques:

- **RAG (Retrieval-Augmented Generation)**: Vector-based semantic search over code
- **AST Analysis**: Abstract Syntax Tree parsing for understanding code structure
- **Graph RAG**: Knowledge graph enhancement for relationship-aware retrieval
- **Agentic Workflows**: Multi-step reasoning with tool use (LangGraph)
- **Multi-LLM Support**: Gemini, Groq (Llama 3.3)

### Key Features
| Feature | Description |
|---------|-------------|
| 💬 Chat Mode | Natural language Q&A about codebase |
| 🔍 Search Mode | Regex pattern search across files |
| 🔧 Refactor Mode | AI-assisted code refactoring |
| ✨ Generate Mode | Spec generation (PO-friendly, Dev Specs, User Stories) |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CODECRITIC AI SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐        │
│  │   DATA INGEST   │────▶│   PROCESSING    │────▶│    STORAGE      │        │
│  │                 │     │                 │     │                 │        │
│  │ • ZIP Files     │     │ • AST Parsing   │     │ • Vector DB     │        │
│  │ • GitHub URLs   │     │ • Chunking      │     │   (Chroma/FAISS)│        │
│  │ • Local Dirs    │     │ • Embeddings    │     │ • AST Graph     │        │
│  │ • Web Docs      │     │ • Graph Build   │     │   (GraphML)     │        │
│  └─────────────────┘     └─────────────────┘     └────────┬────────┘        │
│                                                           │                  │
│                                                           ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        RETRIEVAL LAYER                               │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   Vector    │  │    LLM      │  │   Graph     │  │  Reranker   │ │    │
│  │  │  Retriever  │──│  Retriever  │──│  Enhanced   │──│  (Cross-    │ │    │
│  │  │             │  │             │  │  Retriever  │  │   Encoder)  │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         CHAT ENGINE                                  │    │
│  │                                                                      │    │
│  │   ┌──────────────────┐        ┌──────────────────────────┐          │    │
│  │   │   Linear RAG     │   OR   │   Agentic Workflow       │          │    │
│  │   │   (Simple)       │        │   (LangGraph)            │          │    │
│  │   │                  │        │                          │          │    │
│  │   │  Query → Retrieve│        │  Agent → Tool → Agent    │          │    │
│  │   │      → Answer    │        │       ↓                  │          │    │
│  │   │                  │        │  search_codebase         │          │    │
│  │   │                  │        │  read_file               │          │    │
│  │   │                  │        │  list_files              │          │    │
│  │   │                  │        │  find_callers            │          │    │
│  │   └──────────────────┘        └──────────────────────────┘          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       FRONTEND LAYER                                 │    │
│  │                                                                      │    │
│  │   Streamlit App          FastAPI (REST)         Next.js (React)     │    │
│  │   ├── app.py             ├── /api/index         ├── /chat           │    │
│  │   └── Code_Studio.py     ├── /api/chat          ├── /generate       │    │
│  │                          └── /api/health        └── /search         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Pipeline

### 1. Ingestion Flow

```
User Input (ZIP/GitHub/Local)
         │
         ▼
┌─────────────────────────────────────────┐
│      UniversalIngestor                  │
│      (universal_ingestor.py)            │
│                                         │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ _detect_    │  │ Handler Classes │   │
│  │  handler()  │──▶│                 │   │
│  └─────────────┘  │ • ZIPFileManager│   │
│                   │ • GitHubRepoMgr │   │
│                   │ • LocalDirMgr   │   │
│                   │ • WebDocManager │   │
│                   └─────────────────┘   │
└────────────────────┬────────────────────┘
                     │
                     ▼
            List[Document] + local_path
```

**Example: GitHub Repository Processing**

```python
# 1. User provides: "https://github.com/owner/repo"

# 2. UniversalIngestor detects GitHub URL
ingestor = UniversalIngestor(source)
# delegate = GitHubRepoManager

# 3. Download (clone or ZIP fallback)
ingestor.download()
# Clones to: /tmp/code_chatbot/owner_repo/

# 4. Walk files
for content, metadata in ingestor.walk():
    # content = "def hello(): ..."
    # metadata = {"file_path": "/tmp/.../main.py", "source": "main.py"}
```

### 2. Indexing Flow

```
Documents
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Indexer                                   │
│                       (indexer.py)                               │
│                                                                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │ StructuralChunker│──▶│ Embedding Model │──▶│  Vector Store │  │
│  │                  │   │ (Gemini/HF)     │   │ (Chroma/FAISS)│  │
│  └─────────────────┘   └─────────────────┘   └───────────────┘  │
│                                                                  │
│  Additionally:                                                   │
│  ┌─────────────────┐   ┌─────────────────┐                      │
│  │ ASTGraphBuilder │──▶│  GraphML File   │                      │
│  └─────────────────┘   └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## RAG Implementation

The RAG system in this project is implemented in `code_chatbot/rag.py` with these key components:

### ChatEngine Class

```python
class ChatEngine:
    def __init__(self, retriever, model_name, provider, ...):
        # 1. Base retriever (from vector store)
        self.base_retriever = retriever

        # 2. Enhanced retriever with reranking
        self.vector_retriever = build_enhanced_retriever(
            base_retriever=retriever,
            use_multi_query=use_multi_query,
            use_reranking=True  # Uses Cross-Encoder
        )

        # 3. LLM Retriever (file-aware)
        self.llm_retriever = LLMRetriever(llm, repo_files)

        # 4. Ensemble Retriever (combines both)
        self.retriever = EnsembleRetriever(
            retrievers=[self.vector_retriever, self.llm_retriever],
            weights=[0.6, 0.4]  # 60% vector, 40% LLM
        )
```

### RAG Flow Example

```
User Query: "How does the authentication work?"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. RETRIEVAL                                                │
│    ┌──────────────────┐      ┌──────────────────┐           │
│    │ Vector Retriever │      │ LLM Retriever    │           │
│    │                  │      │                  │           │
│    │ Semantic search  │      │ LLM picks files  │           │
│    │ in Chroma DB     │      │ from structure   │           │
│    └────────┬─────────┘      └────────┬─────────┘           │
│             │                         │                      │
│             └────────────┬────────────┘                      │
│                          ▼                                   │
│              ┌─────────────────────┐                         │
│              │ EnsembleRetriever   │                         │
│              │ (60% + 40% weighted)│                         │
│              └─────────┬───────────┘                         │
│                        │                                     │
│                        ▼                                     │
│              ┌─────────────────────┐                         │
│              │ Reranker            │                         │
│              │ (Cross-Encoder)     │                         │
│              │ ms-marco-MiniLM     │                         │
│              └─────────┬───────────┘                         │
│                        │                                     │
│                        ▼                                     │
│              Top 5 Most Relevant Docs                        │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. GENERATION                                               │
│                                                             │
│    System Prompt + Context + History + Question             │
│                        │                                    │
│                        ▼                                    │
│              ┌─────────────────────┐                        │
│              │ LLM (Gemini/Groq)   │                        │
│              └─────────┬───────────┘                        │
│                        │                                    │
│                        ▼                                    │
│                   Answer + Sources                          │
└─────────────────────────────────────────────────────────────┘
```

---

## AST Analysis & Graph Creation

The AST analysis is implemented in `code_chatbot/ast_analysis.py` using **tree-sitter** for multi-language parsing.

### How AST Parsing Works

```python
# Example: Parsing a Python file

# Source code:
"""
from typing import List

class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id: int) -> User:
        return self.db.find(user_id)

    def create_user(self, name: str) -> User:
        user = User(name=name)
        self.db.save(user)
        return user
"""

# tree-sitter parses this into an AST:
"""
module
├── import_from_statement
│   ├── module: "typing"
│   └── names: ["List"]
├── class_definition
│   ├── name: "UserService"
│   └── block
│       ├── function_definition (name: "__init__")
│       ├── function_definition (name: "get_user")
│       │   └── call (function: "self.db.find")
│       └── function_definition (name: "create_user")
│           ├── call (function: "User")
│           └── call (function: "self.db.save")
"""
```

### EnhancedCodeAnalyzer

```python
class EnhancedCodeAnalyzer:
    """Builds a knowledge graph from code"""

    def __init__(self):
        self.graph = nx.DiGraph()  # NetworkX directed graph
        self.functions = {}         # node_id -> FunctionInfo
        self.classes = {}           # node_id -> ClassInfo
        self.imports = {}           # file_path -> [ImportInfo]
        self.definitions = {}       # name -> [node_ids]
```

### Graph Structure Example

```
┌─────────────────────────────────────────────────────────────────┐
│                    AST KNOWLEDGE GRAPH                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Nodes:                                                         │
│  ┌──────────────────┐                                          │
│  │ Type: "file"     │                                          │
│  │ Name: "api.py"   │                                          │
│  └────────┬─────────┘                                          │
│           │ defines                                             │
│           ▼                                                     │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ Type: "class"    │         │ Type: "function" │             │
│  │ Name: "UserAPI"  │         │ Name: "main"     │             │
│  └────────┬─────────┘         └──────────────────┘             │
│           │ has_method                                          │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ Type: "method"   │───calls───▶ UserService.get_user         │
│  │ Name: "get"      │                                          │
│  └──────────────────┘                                          │
│                                                                 │
│  Edges:                                                         │
│  • defines: file -> class/function                              │
│  • has_method: class -> method                                  │
│  • calls: function -> function                                  │
│  • imports: file -> module                                      │
│  • inherits_from: class -> class                                │
└─────────────────────────────────────────────────────────────────┘
```

### Call Graph Resolution

```python
def resolve_call_graph(self):
    """
    After parsing all files, resolve function calls to their definitions.

    Example:
    - File A has: service.get_user(id)
    - File B has: def get_user(self, id): ...

    Resolution:
    - Finds that "get_user" is defined in File B
    - Creates edge: A::caller_func --calls--> B::UserService.get_user
    """
    for caller_id, callee_name, line in self.unresolved_calls:
        # Try direct match
        if callee_name in self.definitions:
            for target_id in self.definitions[callee_name]:
                self.graph.add_edge(caller_id, target_id, relation="calls")
```

---

## Code Chunking Strategy

The chunking system in `code_chatbot/chunker.py` uses **structural chunking** based on AST boundaries.

### Chunking Philosophy

```
Traditional Text Chunking:
┌─────────────────────────────────────────┐
│ def process_data():        │ CHUNK 1    │
│     data = load()          │            │
│     # Some processing      │            │
│ ───────────────────────────┼────────────│
│     result = transform()   │ CHUNK 2    │  ← Breaks mid-function!
│     return result          │            │
└─────────────────────────────────────────┘

Structural Chunking (This Project):
┌─────────────────────────────────────────┐
│ def process_data():        │            │
│     data = load()          │ CHUNK 1    │  ← Complete function
│     result = transform()   │            │
│     return result          │            │
├─────────────────────────────────────────┤
│ def another_function():    │            │
│     ...                    │ CHUNK 2    │  ← Complete function
└─────────────────────────────────────────┘
```

### StructuralChunker Implementation

```python
class StructuralChunker:
    """Uses tree-sitter to chunk code at semantic boundaries"""

    def __init__(self, max_tokens: int = 800):
        self.max_tokens = max_tokens
        self._init_parsers()  # Python, JS, TS parsers

    def _chunk_node(self, node, file_content, file_metadata):
        """
        Recursive chunking algorithm:

        1. If node fits in max_tokens → return as single chunk
        2. If node is too large → recurse into children
        3. Merge neighboring small chunks
        """
        chunk = FileChunk(file_content, file_metadata,
                         node.start_byte, node.end_byte)

        # Fits? Return it
        if chunk.num_tokens <= self.max_tokens:
            return [chunk]

        # Too large? Recurse
        child_chunks = []
        for child in node.children:
            child_chunks.extend(self._chunk_node(child, ...))

        # Merge small neighbors
        return self._merge_small_chunks(child_chunks)
```

### Chunk Metadata (Rich Context)

Each chunk carries rich metadata:

```python
@dataclass
class FileChunk:
    file_content: str
    file_metadata: Dict
    start_byte: int
    end_byte: int

    # Enhanced metadata
    symbols_defined: List[str]    # ["UserService", "UserService.get_user"]
    imports_used: List[str]       # ["from typing import List"]
    complexity_score: int         # Cyclomatic complexity
    parent_context: str           # "UserService" (parent class)
```

This metadata is stored in the vector DB and used for filtering/ranking.

---

## Retrieval System

### Multi-Stage Retrieval Pipeline

```
Query: "How does user authentication work?"
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  STAGE 1: Initial Retrieval (k=10)                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               Vector Store (Chroma)                      │  │
│  │                                                          │  │
│  │  Query Embedding ──similarity──▶ Document Embeddings     │  │
│  │                                                          │  │
│  │  Returns: 10 candidate documents                         │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  STAGE 2: LLM-Based File Selection                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              LLMRetriever                                │  │
│  │                                                          │  │
│  │  File Tree:                                              │  │
│  │  ├── src/                                                │  │
│  │  │   ├── auth/                                           │  │
│  │  │   │   ├── login.py      ◄── LLM selects this         │  │
│  │  │   │   └── middleware.py ◄── And this                 │  │
│  │  │   └── api/                                            │  │
│  │  └── tests/                                              │  │
│  │                                                          │  │
│  │  LLM Prompt: "Select top 5 relevant files for: ..."      │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  STAGE 3: Ensemble Combination                                │
│                                                               │
│  Vector Results (weight: 0.6) + LLM Results (weight: 0.4)     │
│                                                               │
│  Combined: 12-15 unique documents                             │
└───────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  STAGE 4: Graph Enhancement                                   │
│                                                               │
│  For each retrieved document:                                 │
│  1. Find its node in AST graph                                │
│  2. Get neighboring nodes (related files)                     │
│  3. Add related files to context                              │
│                                                               │
│  Example: login.py found → adds auth_utils.py (imports it)    │
└───────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  STAGE 5: Reranking                                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Cross-Encoder Reranker                      │  │
│  │              (ms-marco-MiniLM-L-6-v2)                     │  │
│  │                                                          │  │
│  │  For each (query, document) pair:                        │  │
│  │  score = cross_encoder.predict([query, doc.content])     │  │
│  │                                                          │  │
│  │  Sort by score, return top 5                             │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                    │
                    ▼
            Final: Top 5 Documents
```

### Reranker (Cross-Encoder)

```python
class Reranker:
    """
    Uses a Cross-Encoder for precise relevance scoring.

    Unlike bi-encoders (used for initial retrieval), cross-encoders
    process query AND document together, giving more accurate scores.
    """

    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Document], top_k=5):
        # Score each document against the query
        pairs = [[query, doc.page_content] for doc in documents]
        scores = self.model.predict(pairs)

        # Sort by score
        scored = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[:top_k]]
```

---

## Agentic Workflow

The agentic workflow uses **LangGraph** to enable multi-step reasoning with tool use.

### Agent Graph Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────┐                              │
│         ┌─────────│   START     │─────────┐                     │
│         │         └─────────────┘         │                     │
│         ▼                                 │                     │
│  ┌─────────────────────────────────────┐  │                     │
│  │           AGENT NODE                │  │                     │
│  │                                     │  │                     │
│  │  1. Process messages                │  │                     │
│  │  2. Call LLM with tools bound       │  │                     │
│  │  3. LLM decides:                    │  │                     │
│  │     - Call a tool? → go to TOOLS    │  │                     │
│  │     - Final answer? → go to END     │  │                     │
│  └──────────────┬──────────────────────┘  │                     │
│                 │                         │                     │
│       has_tool_call?                      │                     │
│         │     │                           │                     │
│    Yes  │     │  No                       │                     │
│         │     │                           │                     │
│         ▼     └──────────────────────────▶┤                     │
│  ┌─────────────────────────────────────┐  │                     │
│  │           TOOLS NODE                │  │                     │
│  │                                     │  │                     │
│  │  Execute tool calls:                │  │                     │
│  │  • search_codebase(query)           │  │                     │
│  │  • read_file(path)                  │  │                     │
│  │  • list_files(dir)                  │  │                     │
│  │  • find_callers(func)               │  │                     │
│  │  • find_callees(func)               │  │                     │
│  │  • find_call_chain(a, b)            │  │                     │
│  │                                     │  │                     │
│  │  Add tool results to messages       │  │                     │
│  └──────────────┬──────────────────────┘  │                     │
│                 │                         │                     │
│                 └─────────────────────────┘                     │
│                                                                 │
│                         ▼                                       │
│                  ┌─────────────┐                                │
│                  │     END     │                                │
│                  └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### Available Tools

```python
# 1. search_codebase - Semantic search in vector store
@tool("search_codebase")
def search_codebase(query: str):
    """Search the codebase for relevant code snippets."""
    docs = retriever.invoke(query)
    return format_results(docs[:5])

# 2. read_file - Read complete file content
@tool("read_file")
def read_file(file_path: str):
    """Read the content of a specific file."""
    with open(full_path, "r") as f:
        return f.read()

# 3. list_files - Directory listing
@tool("list_files")
def list_files(path: str = "."):
    """List files in a directory."""
    return "\n".join(os.listdir(target_path))

# 4. find_callers - Call graph: who calls this?
@tool("find_callers")
def find_callers(function_name: str):
    """Find all functions that call this function."""
    return analyzer.get_callers(function_name)

# 5. find_callees - Call graph: what does this call?
@tool("find_callees")
def find_callees(function_name: str):
    """Find all functions called by this function."""
    return analyzer.get_callees(function_name)

# 6. find_call_chain - Call graph: trace execution path
@tool("find_call_chain")
def find_call_chain(start: str, end: str):
    """Find the call path from one function to another."""
    return analyzer.get_call_chain(start, end)
```

### Agent Execution Example

```
User: "How does the login function handle invalid passwords?"

Agent Thought: I need to find the login function first.
Agent Action: search_codebase("login function authentication")
Tool Result: [login.py snippet showing authenticate() function]

Agent Thought: I found authenticate(). Let me see the full implementation.
Agent Action: read_file("src/auth/login.py")
Tool Result: [Full file content]

Agent Thought: I see it calls verify_password(). Let me check that.
Agent Action: find_callees("authenticate")
Tool Result: verify_password, get_user, create_session

Agent Action: search_codebase("verify_password invalid password")
Tool Result: [password_utils.py with error handling]

Agent Final Answer: The login function handles invalid passwords by...
```

---

## Frontend & API

### Streamlit App Structure

```
app.py (Main Entry)
    │
    ├── Ingestion Screen
    │   ├── Source Type Selection (ZIP/GitHub/Web)
    │   ├── File Upload / URL Input
    │   └── "Process & Index" Button
    │
    └── Redirects to → pages/1_⚡_Code_Studio.py

Code_Studio.py
    │
    ├── Left Panel (Tabs)
    │   ├── 📁 Explorer - File tree navigation
    │   ├── 🔍 Search - Regex pattern search
    │   ├── 💬 Chat - RAG conversation
    │   └── ✨ Generate - Spec generation
    │
    └── Right Panel
        └── Code Viewer - Syntax highlighted file view
```

### FastAPI REST API

```
/api
  ├── /health     GET   - Health check
  │
  ├── /index      POST  - Index a codebase
  │   Body: {
  │     source: "https://github.com/...",
  │     provider: "gemini",
  │     use_agent: true
  │   }
  │
  └── /chat       POST  - Ask questions
      Body: {
        question: "How does auth work?",
        provider: "gemini",
        use_agent: true
      }
      Response: {
        answer: "...",
        sources: [...],
        mode: "agent",
        processing_time: 2.5
      }
```

---

## Component Deep Dives

### Merkle Tree (Incremental Indexing)

```python
class MerkleTree:
    """
    Enables incremental indexing by detecting file changes.

    How it works:
    1. Build a hash tree mirroring directory structure
    2. Each file node has SHA-256 hash of content
    3. Each directory node has hash of children hashes
    4. Compare old vs new tree to find changes
    """

    def compare_trees(self, old, new) -> ChangeSet:
        # Returns: added, modified, deleted, unchanged files
```

**Example:**

```
First Index:
  project/
  ├── main.py    (hash: abc123)
  └── utils.py   (hash: def456)

  Root hash: sha256(abc123 + def456) = xyz789

Second Index (utils.py changed):
  project/
  ├── main.py    (hash: abc123)  ← unchanged
  └── utils.py   (hash: ghi012)  ← NEW HASH!

  Root hash changed! → Only re-index utils.py
```

### Path Obfuscation (Privacy)

```python
class PathObfuscator:
    """
    Obfuscates file paths for sensitive codebases.

    Original: /home/user/secret-project/src/auth/login.py
    Obfuscated: /f8a3b2c1/d4e5f6a7/89012345.py

    Mapping stored securely, reversible only with key.
    """
```

### Rate Limiter (API Management)

```python
class AdaptiveRateLimiter:
    """
    Handles rate limits for free-tier APIs.

    Gemini Free Tier: 15 RPM, 32K TPM, 1500 RPD

    Strategies:
    1. Track usage in rolling window
    2. Adaptive delay based on remaining quota
    3. Exponential backoff on 429 errors
    4. Model fallback chain (flash → pro → legacy)
    """
```

---

## Configuration System

```python
@dataclass
class RAGConfig:
    """Central configuration for entire pipeline"""

    # Chunking
    chunking: ChunkingConfig
        max_chunk_tokens: int = 800
        min_chunk_tokens: int = 100
        preserve_imports: bool = True
        calculate_complexity: bool = True

    # Privacy
    privacy: PrivacyConfig
        enable_path_obfuscation: bool = False

    # Indexing
    indexing: IndexingConfig
        enable_incremental_indexing: bool = True
        batch_size: int = 100
        ignore_patterns: List[str] = [...]

    # Retrieval
    retrieval: RetrievalConfig
        enable_reranking: bool = True
        retrieval_k: int = 10
        rerank_top_k: int = 5
        similarity_threshold: float = 0.5
```

---

## File Dependency Map

```
app.py
├── code_chatbot/universal_ingestor.py
├── code_chatbot/indexer.py
│   ├── code_chatbot/chunker.py (StructuralChunker)
│   ├── code_chatbot/merkle_tree.py (MerkleTree)
│   ├── code_chatbot/config.py (RAGConfig)
│   └── code_chatbot/db_connection.py (Chroma client)
├── code_chatbot/rag.py (ChatEngine)
│   ├── code_chatbot/retriever_wrapper.py
│   │   └── code_chatbot/reranker.py (Reranker)
│   ├── code_chatbot/llm_retriever.py (LLMRetriever)
│   ├── code_chatbot/agent_workflow.py
│   │   └── code_chatbot/tools.py
│   └── code_chatbot/prompts.py
├── code_chatbot/ast_analysis.py (EnhancedCodeAnalyzer)
└── code_chatbot/graph_rag.py (GraphEnhancedRetriever)

pages/1_⚡_Code_Studio.py
├── components/file_explorer.py
├── components/code_viewer.py
├── components/panels.py
└── components/style.py

api/main.py
├── api/routes/chat.py
├── api/routes/index.py
├── api/routes/health.py
├── api/schemas.py
└── api/state.py
```

---

## Summary

This project implements a sophisticated code understanding system with:

1. **Multi-Source Ingestion**: ZIP, GitHub, Local, Web
2. **Structural Chunking**: AST-aware code splitting
3. **Hybrid Retrieval**: Vector + LLM + Graph-enhanced
4. **Cross-Encoder Reranking**: Precision at the top
5. **Agentic Workflow**: Multi-step reasoning with tools
6. **Call Graph Analysis**: Function relationship tracking
7. **Incremental Indexing**: Merkle tree change detection
8. **Multi-LLM Support**: Gemini, Groq with fallbacks

The architecture is designed for scalability, accuracy, and developer experience.
