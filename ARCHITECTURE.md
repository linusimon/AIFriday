# System Architecture & Technical Specifications

## Intelligent Task Routing & Information Chunking System

---

## 1. Executive Summary & System Overview

The **Intelligent Task Routing System** is an enterprise-grade AI solution developed for the TCS AI Friday Challenge. It combines **Multi-Agent AI Orchestration**, **Model Context Protocol (MCP)** servers, and **Retrieval-Augmented Generation (RAG)** to automatically analyze project requirements documents, classify tasks, optimize resource allocations (human experts & AI agents), evaluate cost/SLA risks, and provide conversational voice/text assistance with adaptive information chunking.

---

## 2. High-Level System Architecture (System Context)

```mermaid
graph TD
    subgraph Client Layer [Frontend - Angular 17 SPA]
        UI[Angular 17 Web App / Glassmorphism UI]
        Admin[Admin Portal]
        TaskUI[Task Analysis & Breakdown]
        ChatUI[Voice & Text Chat Assistant]
        OCR[OCR & File Upload Module]
    end

    subgraph API Gateway & Service Layer [Flask Backend :5004]
        Flask[Flask Application & REST Gateway]
        JWT[JWT Authentication Interceptor]
        Router[Task Analysis API & Endpoint Routers]
    end

    subgraph Multi-Agent Orchestration Layer
        Orchestrator[Multi-Agent Pipeline Orchestrator]
        A1[1. Document Analysis Agent]
        A2[2. Data Cleansing Agent]
        A3[3. Task Classification Agent]
        A4[4. Data Enrichment / RAG Agent]
        A5[5. Resource Matching Agent]
        A6[6. Workload Optimization Agent]
        A7[7. Cost Optimization Agent]
        A8[8. Risk & SLA Agent]
        A9[9. Decision Synthesis Agent]
        A10[10. Summary Agent]
    end

    subgraph MCP Server Mesh [Model Context Protocol]
        MCP_Res[Resource Mgmt Server]
        MCP_Skill[Skill Repository Server]
        MCP_Pol[Policy Mgmt Server]
        MCP_Exp[Expert Knowledge Server]
        MCP_SLA[SLA Mgmt Server]
        MCP_Cost[Cost Optimization Server]
        MCP_Hist[Historical Performance Server]
        MCP_Proj[Project Mgmt Server]
        MCP_Analytics[Analytics Server]
    end

    subgraph Data & Storage Layer
        DB[(SQLite Database - task_routing.db)]
        FAISS[(FAISS Vector DB Index)]
        TCS_Embed[TCS GenAI / HuggingFace Embeddings]
    end

    UI -->|HTTP / REST / JWT| Flask
    Flask --> JWT
    Flask --> Router
    Router --> Orchestrator

    Orchestrator --> A1 --> A2 --> A3 --> A4 --> A5 --> A6 --> A7 --> A8 --> A9 --> A10

    A4 <--> FAISS
    A4 <--> TCS_Embed

    A5 <--> MCP_Res
    A5 <--> MCP_Skill
    A6 <--> MCP_Res
    A6 <--> MCP_Hist
    A7 <--> MCP_Cost
    A8 <--> MCP_SLA
    A8 <--> MCP_Pol
    A9 <--> MCP_Exp
    A9 <--> MCP_Proj

    MCP_Res <--> DB
    MCP_Skill <--> DB
    MCP_Pol <--> DB
    MCP_Exp <--> DB
    MCP_SLA <--> DB
    MCP_Cost <--> DB
    MCP_Hist <--> DB
    MCP_Proj <--> DB
    MCP_Analytics <--> DB
```

---

## 3. Data Flow & Subsystem Interaction Architecture (C4 Level 2)

```mermaid
graph LR
    subgraph Frontend Subsystems
        Comp_Upload[Upload & Drag-Drop Component]
        Comp_Results[Results & Task Extraction View]
        Comp_Charts[Chart.js / ngx-charts Visualizer]
        Comp_Voice[Web Speech Voice Synthesizer]
        Comp_Chat[Conversational Chat Component]
    end

    subgraph Backend Core Services
        Svc_Auth[JWT Auth Blueprint /auth/login]
        Svc_Analyze[Task Routing Blueprint /analyze]
        Svc_MCP[MCP Gateway Router /api/mcp]
        Svc_RAG[RAG Service Vector Store Engine]
    end

    subgraph Data & Pipeline Operations
        Pipeline[Agent Execution Pipeline]
        MCP_Mesh[9 MCP Tool Servers]
        VectorDB[FAISS Index Vector Database]
        RelationalDB[SQLite Database File]
    end

    Comp_Upload -->|Document Payload| Svc_Analyze
    Svc_Analyze -->|Trigger| Pipeline
    Pipeline -->|Query Policies & SOPs| Svc_RAG
    Svc_RAG -->|Similarity Search| VectorDB
    Pipeline -->|Tool Call Execution| Svc_MCP
    Svc_MCP -->|Read/Write Operations| MCP_Mesh
    MCP_Mesh -->|SQL Transactions| RelationalDB
    Pipeline -->|Aggregated Task Plan| Svc_Analyze
    Svc_Analyze -->|Structured Analysis JSON| Comp_Results
    Comp_Results -->|Render Metrics| Comp_Charts
    Comp_Results -->|Text/Speech Output| Comp_Voice
    Comp_Chat -->|Conversational Q&A| Svc_MCP
```

---

## 4. Infrastructure & Deployment Topology Diagram

```mermaid
graph TB
    subgraph Client Workstation Browser
        Browser[Web Browser - Angular 17 SPA :4204]
    end

    subgraph Host Machine Environment [Windows / Linux]
        subgraph Frontend Node Environment
            AngularDev[Angular Dev Server / Node.js Engine]
            Proxy[Angular HTTP Proxy Config :4204 -> :5004]
        end

        subgraph Python Virtual Environment
            FlaskApp[Flask WSGI / Gunicorn App :5004]
            AgentRunner[Agent Orchestrator Worker Pool]
            MCPRegistry[MCP Server Blueprints Registry]
        end

        subgraph Local File System Storage
            UploadsDir[uploads/ Directory]
            FaissDir[faiss_index/ Storage]
            SQLiteFile[data/task_routing.db]
        end
    end

    subgraph Remote AI Cloud Services
        GenAI_API[TCS GenAI / HuggingFace API Endpoint]
    end

    Browser -->|HTTP Requests| AngularDev
    AngularDev --> Proxy
    Proxy -->|Forward REST Calls| FlaskApp
    FlaskApp --> AgentRunner
    FlaskApp --> MCPRegistry
    AgentRunner -->|Store Uploads| UploadsDir
    AgentRunner -->|Embeddings & RAG| GenAI_API
    AgentRunner -->|Index Queries| FaissDir
    MCPRegistry -->|Database Reads/Writes| SQLiteFile
```

---

## 5. Voice & Information Chunking State Machine Architecture

```mermaid
stateDiagram-v2
    [*] --> Idle: User Opens Chat / Voice Assistant
    Idle --> Listening: Speech / Text Input Triggered
    Listening --> Processing: User Utterance Captured
    Processing --> Segmenting: Agent Generates Full Response
    
    state Segmenting {
        [*] --> SplitChunks: Divide Text into Micro-Chunks
        SplitChunks --> OrderChunks: Sequence by Priority & Context
    }

    Segmenting --> PresentingChunk: Deliver Chunk N (Audio + Highlighted Text)

    state PresentingChunk {
        [*] --> SpeakingText: TTS Playback Active
        SpeakingText --> AwaitingFeedback: Audio Finish / Pause
    }

    AwaitingFeedback --> ComprehensionCheck: System Prompts ("Did that make sense?")
    
    ComprehensionCheck --> PresentingChunk: User says "Repeat" / "Replay" (Replay current chunk)
    ComprehensionCheck --> SimplifyingChunk: User says "Explain simpler" / "Confused"
    ComprehensionCheck --> PresentingChunk: User says "Yes" / "Next" (Advance to Chunk N+1)
    
    SimplifyingChunk --> PresentingChunk: Re-present simplified chunk text

    AwaitingFeedback --> Completed: All Chunks Delivered & Confirmed
    Completed --> Idle: Wait for next query
```

---

## 6. Multi-Agent Execution Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Admin
    participant Gateway as Flask Backend Gateway
    participant Orchestrator as Agent Orchestrator
    participant RAG as RAG & FAISS Vector Service
    participant MCP as MCP Server Mesh
    participant DB as SQLite DB

    User->>Gateway: POST /api/task-routing/analyze (Upload Requirement Doc)
    Gateway->>Orchestrator: Execute Multi-Agent Task Routing Workflow

    rect rgb(240, 248, 255)
        note right of Orchestrator: Step 1: Document Processing
        Orchestrator->>Orchestrator: 1. Document Analysis Agent (Extract raw sections)
        Orchestrator->>Orchestrator: 2. Data Cleansing Agent (Normalize & format text)
        Orchestrator->>Orchestrator: 3. Task Classification Agent (Decompose into granular tasks)
    end

    rect rgb(255, 245, 238)
        note right of Orchestrator: Step 2: RAG Enrichment & Skill Matching
        Orchestrator->>RAG: 4. Data Enrichment Agent (Search vector index for contextual SOPs)
        RAG-->>Orchestrator: Contextual policies & domain knowledge
        Orchestrator->>MCP: 5. Resource Matching Agent (Query skill matching tool)
        MCP->>DB: Query available resources & skill matrix
        DB-->>MCP: Candidate resources
        MCP-->>Orchestrator: Ranked resource-skill fit scores
    end

    rect rgb(240, 255, 240)
        note right of Orchestrator: Step 3: Workload, Cost & Risk Analysis
        Orchestrator->>MCP: 6. Workload Optimization Agent (Check capacity & balance)
        Orchestrator->>MCP: 7. Cost Optimization Agent (Estimate resource & agent costs)
        Orchestrator->>MCP: 8. Risk & SLA Agent (Assess SLA compliance & risk rating)
    end

    rect rgb(255, 250, 240)
        note right of Orchestrator: Step 4: Decision Synthesis & Output
        Orchestrator->>MCP: 9. Decision Synthesis Agent (Consolidate optimal assignment)
        Orchestrator->>Orchestrator: 10. Summary Agent (Generate Executive Brief & Action Plan)
    end

    Orchestrator-->>Gateway: Consolidated Analysis Result JSON
    Gateway-->>User: Structured Response (Tasks, Assignments, Charts, Costs, Risks)
```

---

## 7. Model Context Protocol (MCP) Server Specification

| MCP Server | Key Capabilities & Exposed Tools |
| :--- | :--- |
| **Resource Management** | `get_available_resources`, `get_resource_workload`, `update_workload`, `get_resource_skills` |
| **Skill Repository** | `match_skills`, `search_skills_by_category`, `get_all_skills`, `evaluate_skill_gap` |
| **Policy Management** | `search_policies`, `check_policy_compliance`, `get_escalation_rules` |
| **Expert Knowledge** | `search_expert_insights`, `get_similar_historical_tasks`, `recommend_approach` |
| **SLA Management** | `verify_sla_compliance`, `calculate_target_deadline`, `get_sla_rules` |
| **Cost Optimization** | `estimate_assignment_cost`, `calculate_agent_vs_human_cost`, `optimize_budget` |
| **Historical Performance** | `get_resource_performance_history`, `get_completion_rate`, `get_quality_score` |
| **Project Management** | `get_active_projects`, `create_project_task`, `update_task_status` |
| **Analytics** | `generate_utilization_metrics`, `get_cost_breakdown_analytics`, `get_risk_summary` |

---

## 8. Database Entity Relationship Diagram

```mermaid
erDiagram
    PROJECTS ||--o{ TASKS : contains
    RESOURCES ||--o{ TASK_ASSIGNMENTS : assigned_to
    TASKS ||--o{ TASK_ASSIGNMENTS : receives
    KNOWLEDGE_BASE ||--o{ RAG_EMBEDDINGS : indexed_by
    SLA_RULES ||--o{ TASKS : governs
    COST_MODELS ||--o{ RESOURCES : applies_to

    PROJECTS {
        int id PK
        string name
        string description
        string status
        datetime created_at
    }

    TASKS {
        int id PK
        int project_id FK
        string task_name
        string complexity
        int estimated_hours
        string status
    }

    RESOURCES {
        int id PK
        string name
        string type "human / ai_agent"
        string role
        string skills_json
        float hourly_rate
        int current_workload
        int max_capacity
    }

    KNOWLEDGE_BASE {
        int id PK
        string title
        string document_type
        string content
        string tags
    }
```
