# System Architecture & Technical Specifications

## Intelligent Task Routing & Information Chunking System

---

## 1. Executive Summary & System Overview

The **Intelligent Task Routing System** is an enterprise-grade AI solution developed for the TCS AI Friday Challenge. It combines **Multi-Agent AI Orchestration**, **Model Context Protocol (MCP)** servers (including an independent, reusable **Generic SQLite MCP Server**), and **Retrieval-Augmented Generation (RAG)** to automatically analyze project requirements documents, classify tasks, optimize resource allocations (human experts & AI agents), evaluate cost/SLA risks, generate Agile User Stories & 3-Sprint Execution Plans, and provide conversational voice/text assistance with adaptive information chunking.

### Key Architectural Highlights
* 🛡️ **Two-Tier Scope & Intent Validation**: Input is evaluated by `PrivacyGuardrail.validate_scope` for security rules (prompt injection, jailbreak, toxicity, SQL injection, PII masking, rate limiting) and business domain scope. If off-topic, a polite guidance response is immediately returned to the UI. Valid inputs are processed by `TaskIntentAgent` to dynamically route requests.
* ⚡ **Asynchronous Parallel Agent Pipeline**: `AgentOrchestrator` dynamically selects specialist agents based on business intent and executes independent agents (`WorkloadOptimizationAgent`, `CostOptimizationAgent`, `RiskSLAAgent`) asynchronously in parallel using `ThreadPoolExecutor`.
* 🔌 **Standalone Generic SQLite MCP Server (`:5001`)**: Independent FastMCP server process running on port `5001` (SSE transport) providing application-agnostic database tools (`execute_query`, `execute_statement`, `execute_batch`, `list_tables`, `describe_table`). Has zero domain business logic and can be reused for any SQLite database across external applications.
* 🧩 **Domain MCP Server Mesh (`:5004`)**: 9 specialized Flask Blueprint tool servers (`resource`, `skill`, `policy`, `expert`, `performance`, `sla`, `cost`, `project`, `analytics`) that process domain operations and execute SQL via the generic SQLite MCP execution engine.

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

    subgraph API Gateway & Guardrail Layer [Flask Backend :5004]
        Flask[Flask Application Gateway :5004]
        JWT[JWT Authentication Interceptor]
        Guardrail[PrivacyGuardrail & Scope Validator]
    end

    subgraph Multi-Agent Orchestration Layer
        IntentAgent[0. Task Intent Classification Agent]
        Orchestrator[Multi-Agent Pipeline Orchestrator]
        A1[1. Document Analysis Agent]
        A2[2. Data Cleansing Agent]
        A3[3. Task Classification Agent]
        A4[4. Data Enrichment / RAG Agent]
        A5[5. Resource Matching Agent]
        
        subgraph Parallel Async Workers [ThreadPoolExecutor]
            A6[6. Workload Optimization Agent]
            A7[7. Cost Optimization Agent]
            A8[8. Risk & SLA Agent]
        end
        
        A9[9. Decision Synthesis Agent]
        A10[10. Summary & Agile Execution Plan Agent]
    end

    subgraph Domain MCP Server Mesh [Port :5004]
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

    subgraph Standalone MCP Layer [FastMCP SSE :5001]
        GenericMCP[Generic SQLite MCP Server :5001]
    end

    subgraph Data & Storage Layer
        DB[(SQLite Database - task_routing.db)]
        FAISS[(FAISS Vector DB Index)]
        TCS_Embed[TCS GenAI / HuggingFace Embeddings]
    end

    UI -->|HTTP / REST / JWT| Flask
    Flask --> JWT
    Flask --> Guardrail
    Guardrail -->|Off-Topic / Violation| UI
    Guardrail -->|Valid Business Scope| IntentAgent
    IntentAgent --> Orchestrator

    Orchestrator --> A1 --> A2 --> A3 --> A4 --> A5
    A5 --> Parallel
    Parallel --> A6 & A7 & A8
    A6 & A7 & A8 --> A9 --> A10

    A4 <--> FAISS
    A4 <--> TCS_Embed

    A5 <--> MCP_Skill
    A6 <--> MCP_Res
    A7 <--> MCP_Cost
    A8 <--> MCP_SLA & MCP_Pol
    A9 <--> MCP_Exp & MCP_Proj & MCP_Analytics

    MCP_Res & MCP_Skill & MCP_Pol & MCP_Exp & MCP_SLA & MCP_Cost & MCP_Hist & MCP_Proj & MCP_Analytics <--> GenericMCP
    GenericMCP <--> DB
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
        Svc_Guard[Scope & Security Guardrail Engine]
        Svc_Analyze[Task Routing Blueprint /analyze]
        Svc_RAG[RAG Service Vector Store Engine]
    end

    subgraph Execution & MCP Layer
        Intent[Task Intent Agent]
        Orchestration[Parallel ThreadPool Orchestrator]
        DomainMCP[9 Domain MCP Blueprints :5004]
        GenericMCP[Standalone SQLite MCP Server :5001]
    end

    subgraph Storage Layer
        VectorDB[FAISS Index Vector Database]
        RelationalDB[SQLite Database File - task_routing.db]
    end

    Comp_Upload -->|Document Payload| Svc_Analyze
    Svc_Analyze -->|Evaluate Scope| Svc_Guard
    Svc_Guard -->|Pass| Intent
    Intent -->|Classify Intent & Launch| Orchestration
    Orchestration -->|Vector Query| Svc_RAG
    Svc_RAG -->|Similarity Search| VectorDB
    Orchestration -->|Domain Tool Invocation| DomainMCP
    DomainMCP -->|Generic execute_query / execute_statement| GenericMCP
    GenericMCP -->|SQL Connection & Transaction| RelationalDB
    Orchestration -->|Structured Analysis JSON| Comp_Results
    Comp_Results -->|Render Metrics| Comp_Charts
    Comp_Results -->|Text/Speech Output| Comp_Voice
    Comp_Chat -->|Conversational Q&A| Svc_Analyze
```

---

## 4. Infrastructure & Deployment Topology Diagram

```mermaid
graph TB
    subgraph Client Workstation Browser
        Browser[Web Browser - Angular 17 SPA :4204]
    end

    subgraph Host Machine Environment [Windows / Linux / macOS]
        subgraph Frontend Node Environment
            AngularDev[Angular Dev Server / Node.js Engine :4204]
            Proxy[Angular HTTP Proxy Config :4204 -> :5004]
        end

        subgraph Python Virtual Environment
            FlaskApp[Flask WSGI Backend Server :5004]
            AgentRunner[Agent Orchestrator Worker Pool]
            DomainMCP[9 Domain MCP Blueprints :5004]
            FastMCPProcess[Standalone FastMCP SQLite Server Process :5001]
        end

        subgraph Local File System Storage
            UploadsDir[uploads/ Directory]
            FaissDir[faiss_index/ Storage]
            SQLiteFile[task_routing.db]
        end
    end

    subgraph Remote AI Cloud Services
        GenAI_API[TCS GenAI / HuggingFace API Endpoint]
    end

    Browser -->|HTTP Requests| AngularDev
    AngularDev --> Proxy
    Proxy -->|Forward REST Calls| FlaskApp
    FlaskApp --> AgentRunner
    FlaskApp --> DomainMCP
    AgentRunner -->|Store Uploads| UploadsDir
    AgentRunner -->|Embeddings & RAG| GenAI_API
    AgentRunner -->|Index Queries| FaissDir
    DomainMCP -->|HTTP / SSE Generic MCP Calls| FastMCPProcess
    FastMCPProcess -->|Direct SQLite Reads/Writes| SQLiteFile
```

---

## 5. Multi-Agent Execution Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Frontend UI
    participant Gateway as Flask Gateway (:5004)
    participant Guard as Scope Guardrail Engine
    participant Intent as Intent Classification Agent
    participant Orchestrator as Agent Orchestrator
    participant RAG as RAG & FAISS Vector Service
    participant DomainMCP as Domain MCP Servers (:5004)
    participant GenericMCP as Generic SQLite MCP Server (:5001)
    participant DB as SQLite DB

    User->>Gateway: POST /api/task-routing/analyze (Document / Text Query)
    Gateway->>Guard: Validate Domain Scope & Security Rules
    
    alt Off-Topic / Security Violation
        Guard-->>Gateway: Blocked (Scope Violation / Prompt Injection)
        Gateway-->>User: Refusal & Guidance Response
    else Valid Business Scope
        Guard->>Intent: Classify User Intent & Requirements
        Intent-->>Orchestrator: Categorized Intent (e.g., FULL_TASK_ROUTING_ANALYSIS)
        
        rect rgb(240, 248, 255)
            note right of Orchestrator: Phase 1: Sequential Parsing & Classification
            Orchestrator->>Orchestrator: 1. Document Analysis Agent (Extract raw requirements)
            Orchestrator->>Orchestrator: 2. Data Cleansing Agent (Normalize & format text)
            Orchestrator->>Orchestrator: 3. Task Classification Agent (Decompose into granular tasks)
        end

        rect rgb(255, 245, 238)
            note right of Orchestrator: Phase 2: RAG Enrichment & Skill Matching
            Orchestrator->>RAG: 4. Data Enrichment Agent (Vector search for SOPs & policies)
            RAG-->>Orchestrator: Contextual policies & domain knowledge
            Orchestrator->>DomainMCP: 5. Resource Matching Agent (Query skill repository)
            DomainMCP->>GenericMCP: execute_query("SELECT * FROM human_resources...", params)
            GenericMCP->>DB: Execute SQL query
            DB-->>GenericMCP: Rows
            GenericMCP-->>DomainMCP: JSON Rows
            DomainMCP-->>Orchestrator: Ranked resource-skill fit scores
        end

        rect rgb(240, 255, 240)
            note right of Orchestrator: Phase 3: Parallel Asynchronous Workers (ThreadPoolExecutor)
            par Workload Optimization
                Orchestrator->>DomainMCP: 6. Workload Optimization Agent (Check capacity & workload)
                DomainMCP->>GenericMCP: execute_query(...)
                GenericMCP-->>DomainMCP: Workload metrics
            and Cost Optimization
                Orchestrator->>DomainMCP: 7. Cost Optimization Agent (Estimate resource & agent costs)
                DomainMCP->>GenericMCP: execute_query(...)
                GenericMCP-->>DomainMCP: Cost estimates
            and Risk & SLA Assessment
                Orchestrator->>DomainMCP: 8. Risk & SLA Agent (Assess SLA compliance & risk rating)
                DomainMCP->>GenericMCP: execute_query(...)
                GenericMCP-->>DomainMCP: SLA breach risks
            end
        end

        rect rgb(255, 250, 240)
            note right of Orchestrator: Phase 4: Decision Synthesis & Output Generation
            Orchestrator->>Orchestrator: 9. Decision Synthesis Agent (Consolidate optimal assignments)
            Orchestrator->>Orchestrator: 10. Summary Agent & Project Execution Agent (Generate Agile Plan & Executive Brief)
        end

        Orchestrator-->>Gateway: Consolidated Analysis Result JSON
        Gateway-->>User: Structured Response (Tasks, Assignments, Charts, Sprint Roadmap, Costs, Risks)
    end
```

---

## 6. Model Context Protocol (MCP) Server Specification

| MCP Server | Hosting / Port | Capabilities & Exposed Tools |
| :--- | :--- | :--- |
| **Generic SQLite MCP Server** | Standalone FastMCP (`:5001`) | `execute_query` (SELECT), `execute_statement` (INSERT/UPDATE/DELETE/DDL), `execute_batch` (transactions), `list_tables`, `describe_table` |
| **Resource Management** | Flask Blueprint (`:5004`) | `get_available_resources`, `get_current_workload`, `get_resource_skills`, `get_resource_capacity` |
| **Skill Repository** | Flask Blueprint (`:5004`) | `search_skills`, `match_skills`, `get_skill_profiles` |
| **Policy Management** | Flask Blueprint (`:5004`) | `search_policies`, `get_business_rules`, `get_escalation_rules` |
| **Expert Knowledge** | Flask Blueprint (`:5004`) | `search_expert_recommendations`, `get_historical_guidance`, `get_expert_by_category` |
| **SLA Management** | Flask Blueprint (`:5004`) | `get_sla_requirements`, `predict_breach_risk`, `check_sla_compliance` |
| **Cost Optimization** | Flask Blueprint (`:5004`) | `estimate_assignment_cost`, `compare_assignment_options`, `get_cost_optimization_recommendations` |
| **Historical Performance** | Flask Blueprint (`:5004`) | `get_historical_assignments`, `get_success_rates`, `get_quality_scores` |
| **Project Management** | Flask Blueprint (`:5004`) | `get_project_details`, `get_project_status`, `get_task_information`, `get_tasks_by_status` |
| **Analytics** | Flask Blueprint (`:5004`) | `find_similar_tasks`, `recommend_best_resource`, `generate_utilization_metrics` |

---

## 7. Database Entity Relationship Diagram

```mermaid
erDiagram
    PROJECTS ||--o{ TASKS : contains
    RESOURCES ||--o{ HISTORICAL_ASSIGNMENTS : assigned_to
    TASKS ||--o{ HISTORICAL_ASSIGNMENTS : receives
    TASKS ||--o{ ROUTING_DECISIONS : produces
    PROJECTS ||--o{ PROJECT_EXECUTION_PLANS : generates
    SLA_RULES ||--o{ TASKS : governs
    COST_MODELS ||--o{ RESOURCES : applies_to
    CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains

    USERS {
        int id PK
        string username
        string password_hash
        string role
    }

    PROJECTS {
        int project_id PK
        string project_name
        string priority
        string status
        string business_area
        string sla
    }

    TASKS {
        int task_id PK
        int project_id FK
        string task_name
        string description
        string skills_required
        string complexity
        float estimated_effort
        string priority
        string status
    }

    RESOURCES {
        int resource_id PK
        string name
        string role
        string skills
        int experience
        string availability
        float current_workload
        float quality_score
        float performance_score
        float cost_per_hour
    }

    AI_AGENTS {
        int agent_id PK
        string agent_name
        string capabilities
        string specialization
        string availability
        float performance_score
        float quality_score
        float cost_per_hour
    }

    PROJECT_EXECUTION_PLANS {
        int plan_id PK
        string plan_name
        int total_user_stories
        int total_story_points
        float total_effort_hours
        float total_cost
        int sprint_count
        string user_stories_json
        string timeline_json
    }
```
