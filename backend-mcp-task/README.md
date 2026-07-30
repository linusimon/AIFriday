# Intelligent Task Routing System - Backend Engine

## Overview

Enterprise Flask backend and standalone MCP server infrastructure for the Intelligent Task Routing System featuring:
- ✅ **Standalone Generic SQLite MCP Server (`:5001`)**: Independent FastMCP SSE server exposing application-agnostic database tools (`execute_query`, `execute_statement`, `execute_batch`, `list_tables`, `describe_table`).
- ✅ **9 Domain MCP Tool Servers (`:5004`)**: Flask Blueprint servers for resources, skills, policies, expert knowledge, SLAs, costs, historical performance, project management, and analytics.
- ✅ **Two-Tier Intent & Guardrail Validation**: `PrivacyGuardrail.validate_scope` checking security rules & domain scope (returning immediate UI guidance if off-topic) and `TaskIntentAgent` categorizing valid queries.
- ✅ **10 AI Agents & Asynchronous Parallel Orchestrator**: Dynamic flow dispatching and concurrent execution via `ThreadPoolExecutor` for workload, cost, and SLA risk agents.
- ✅ **Agile Plan Generation**: Automatic decomposition into User Stories, Fibonacci points, resource/AI agent assignments, and 3-Sprint timelines.
- ✅ **RAG & FAISS Vector Search**: Semantic context retrieval for SOPs, guidelines, and policies.
- ✅ **SQLite Database Gateway**: Generic MCP statement execution for database initialization, schema creation, and transaction management.

---

## Quick Start

### 1. Setup Environment

```bash
cd backend-mcp-task
setup.bat
```

This will:
- Create a Python virtual environment (`venv`)
- Install all required dependencies
- Create necessary directories (`uploads`, `faiss_index`, `data`)

---

### 2. Configuration

Edit `.env` file:
```env
HF_TOKEN=your_tcs_genai_api_key_here
JWT_SECRET_KEY=your-secret-key-change-in-production
SQLITE_DB_PATH=task_routing.db
```

---

### 3. Start Backend & MCP Server

```bash
start.bat
```

This launches:
* **Standalone Generic SQLite MCP Server**: `http://127.0.0.1:5001/sse`
* **Flask Backend API Gateway**:          `http://localhost:5004/api`

---

## System Architecture & Endpoints

### 1. Standalone Generic SQLite MCP Server (`:5001`)

Runs independently via FastMCP SSE transport. Provides reusable tools for any SQLite database:

| Generic Tool | Description |
| :--- | :--- |
| `execute_query(sql, params, db_path)` | Executes read-only `SELECT` queries and returns row dicts |
| `execute_statement(sql, params, db_path)` | Executes `INSERT`, `UPDATE`, `DELETE`, `CREATE TABLE` DDLs and commits |
| `execute_batch(statements, db_path)` | Executes multiple SQL statements in a single transaction |
| `list_tables(db_path)` | Lists all user tables in the SQLite database |
| `describe_table(table_name, db_path)` | Returns column names, data types, and nullability |

---

### 2. Domain MCP Servers (`:5004`)

Accessible at `/api/mcp/<server>/<tool>`, routing SQL queries to the generic SQLite MCP execution engine:

1. **resource**: `get_available_resources`, `get_current_workload`, `get_resource_skills`, `get_resource_capacity`
2. **skill**: `search_skills`, `match_skills`, `get_skill_profiles`
3. **policy**: `search_policies`, `get_business_rules`, `get_escalation_rules`
4. **expert**: `search_expert_recommendations`, `get_historical_guidance`, `get_expert_by_category`
5. **performance**: `get_historical_assignments`, `get_success_rates`, `get_quality_scores`
6. **sla**: `get_sla_requirements`, `predict_breach_risk`, `check_sla_compliance`
7. **cost**: `estimate_assignment_cost`, `compare_assignment_options`, `get_cost_optimization_recommendations`
8. **project**: `get_project_details`, `get_project_status`, `get_task_information`, `get_tasks_by_status`
9. **analytics**: `find_similar_tasks`, `recommend_best_resource`, `generate_utilization_metrics`

---

### 3. Multi-Agent Orchestration Flow

```
Phase 0 (Guardrail & Intent):
  • PrivacyGuardrail.validate_scope → Verify security & business domain scope (return immediate UI response if off-topic)
  • TaskIntentAgent → Categorize intent (FULL_TASK_ROUTING, EXECUTION_PLAN, RESOURCE_MATCH, COST_SLA)

Phase 1 (Sequential Pre-processing):
  1. Document Analysis Agent → Extract raw task sections
  2. Data Cleansing Agent → Normalize & scrub data
  3. Data Enrichment Agent → Retrieve RAG context & SOPs
  4. Task Classification Agent → Assess complexity & effort
  5. Resource Matching Agent → Score skill matrix fit

Phase 2 (Parallel Asynchronous Workers via ThreadPoolExecutor):
  6. Workload Optimization Agent ──┐
  7. Cost Optimization Agent     ──┼── Execute concurrently in parallel
  8. Risk & SLA Agent           ──┘

Phase 3 (Sequential Synthesis & Planning):
  9. Decision Synthesis Agent → Consolidate optimal resource assignments
  10. Summary Agent & Project Execution Agent → Produce executive brief & Agile 3-Sprint Roadmap
```

---

## API Endpoints Reference

### Authentication
* **POST** `/api/auth/login` - Authenticate & obtain JWT Bearer token

### Task Routing & Guardrails
* **POST** `/api/task-routing/analyze` - Document upload & multi-agent task routing analysis pipeline
* **POST** `/api/guardrails/validate` - Validate domain scope & security rules
* **GET** `/api/guardrails/audit_logs` - Retrieve security audit trail

### System Status
* **GET** `/api/health` - System health status
* **GET** `/api/mcp/status` - List all 9 domain MCP servers and tools

---

## Testing & Verification

### Run Verification Test Script

```bash
python -c "from mcp_servers.sqlite_server import list_tables, describe_table, execute_query; print(list_tables())"
```

---

**Backend Complete & Verified ✅**
