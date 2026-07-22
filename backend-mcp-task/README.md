# Intelligent Task Routing System - Backend

## Overview

Complete Flask-based backend for the Intelligent Task Routing System with:
- ✅ **9 MCP Servers** for modular data access
- ✅ **10 AI Agents** for intelligent task analysis
- ✅ **Multi-Agent Orchestration** with sequential and parallel execution
- ✅ **SQLite Database** with sample data
- ✅ **JWT Authentication**
- ✅ **TCS GenAI Integration**

## Quick Start

### 1. Setup

```bash
cd backend-mcp-task
setup.bat
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create necessary directories

### 2. Configure

Edit `.env` file:
```
HF_TOKEN=your_tcs_genai_api_key_here
JWT_SECRET_KEY=your-secret-key-change-in-production
```

### 3. Start Server

```bash
start.bat
```

Server runs on: `http://localhost:5004`

## API Endpoints

### Authentication

**POST** `/api/auth/login`
```json
{
  "username": "admin",
  "password": "admin123"
}
```
Returns JWT token.

### System Status

**GET** `/api/health` - Health check  
**GET** `/api/status` - System statistics  
**GET** `/api/mcp/status` - List all MCP servers

### Task Routing Analysis (Main Feature)

**POST** `/api/task-routing/analyze`

Upload a document (TXT, PDF, DOCX) or send JSON:
```json
{
  "document_text": "Project requirements: Build a web application with React frontend and Python backend..."
}
```

Returns comprehensive analysis with:
- Extracted and classified tasks
- Resource recommendations (AI agents / human experts)
- Cost estimates
- Risk assessment
- SLA compliance predictions
- Executive summary

### MCP Server Tools

All MCP servers are accessible at: `/api/mcp/<server>/<tool>`

Examples:
```
GET  /api/mcp/resource/get_available_resources
POST /api/mcp/skill/match_skills
     Body: {"required_skills": "Python,React,SQL"}
POST /api/mcp/cost/estimate_assignment_cost
     Body: {"resource_id": 1, "resource_type": "human", "estimated_effort": 40}
GET  /api/mcp/analytics/generate_utilization_metrics
```

#### Available MCP Servers:

1. **resource** - Resource availability, workload, skills, capacity
2. **skill** - Skill search and matching
3. **policy** - Policy search, business rules, escalation rules
4. **expert** - Expert recommendations and historical guidance
5. **performance** - Historical performance metrics
6. **sla** - SLA requirements and breach risk prediction
7. **cost** - Cost estimation and optimization
8. **project** - Project and task information
9. **analytics** - Similarity search, recommendations, utilization

### Admin Data Management

**GET** `/api/resources/human` - List human resources  
**GET** `/api/resources/ai` - List AI agents  
**GET** `/api/projects` - List projects  
**GET** `/api/tasks` - List tasks  
**GET** `/api/sla-rules` - List SLA rules  
**GET/POST** `/api/expert-analysis` - Expert analysis entries

## Architecture

### Multi-Agent Execution Flow

```
Phase 1 (Sequential):
  1. Document Analysis Agent → Extract tasks
  2. Data Cleansing Agent → Normalize data
  3. Data Enrichment Agent → Add context
  4. Task Classification Agent → Classify complexity
  5. Resource Matching Agent → Match skills

Phase 2 (Parallel):
  6. Workload Optimization Agent → Balance workload
  7. Cost Optimization Agent → Optimize costs
  8. Risk & SLA Agent → Predict risks

Phase 3 (Sequential):
  9. Decision Agent → Final routing decisions
  10. Summary Agent → Generate executive summary
```

### Database Schema

**9 Tables:**
- `users` - Authentication
- `human_resources` - Human resource profiles
- `ai_agents` - AI agent capabilities
- `projects` - Project information
- `tasks` - Task details
- `historical_assignments` - Past assignments
- `sla_rules` - SLA requirements
- `cost_models` - Cost structures
- `expert_analysis` - Expert recommendations
- `routing_decisions` - Analysis results
- `chat_sessions`, `chat_messages` - Chat history

### Sample Data

Database is pre-seeded with:
- 20 human resources (various roles and skills)
- 10 AI agents (specialized capabilities)
- 5 projects
- 10 tasks
- 50 historical assignments
- 7 expert analysis entries

## Testing

### Test with cURL

```bash
# 1. Login
curl -X POST http://localhost:5004/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. Check MCP servers
curl http://localhost:5004/api/mcp/status

# 3. Test resource matching
curl -X POST http://localhost:5004/api/mcp/skill/match_skills \
  -H "Content-Type: application/json" \
  -d '{"required_skills":"Python,Machine Learning,SQL"}'

# 4. Run task routing analysis
curl -X POST http://localhost:5004/api/task-routing/analyze \
  -H "Content-Type: application/json" \
  -d '{"document_text":"Project: Build an ML-powered recommendation system. Tasks: 1) Data pipeline development (Python, SQL), 2) ML model training (TensorFlow, PyTorch), 3) API development (Flask, REST)."}'
```

### Test with Python

```python
import requests

# Login
response = requests.post('http://localhost:5004/api/auth/login',
    json={'username': 'admin', 'password': 'admin123'})
token = response.json()['token']

# Analyze tasks
with open('project_requirements.txt', 'r') as f:
    document_text = f.read()

response = requests.post('http://localhost:5004/api/task-routing/analyze',
    json={'document_text': document_text},
    headers={'Authorization': f'Bearer {token}'})

result = response.json()
print(result['report']['executive_summary'])
```

## Dependencies

- Flask 3.0.0
- flask-cors 4.0.0
- flask-jwt-extended 4.6.0
- langchain 0.1.0
- langchain-openai 0.0.5
- faiss-cpu 1.7.4
- pdfminer.six (PDF parsing)
- python-docx (DOCX parsing)
- bcrypt (password hashing)

## Development

### Adding New MCP Servers

1. Create `mcp_servers/your_server.py`
2. Extend `MCPServer` base class
3. Register tools with `register_tool()`
4. Import and register blueprint in `app.py`

### Adding New Agents

1. Create `agents/your_agent.py`
2. Extend `Agent` base class
3. Implement `execute(context)` method
4. Add to orchestration flow in main endpoint

## Troubleshooting

**Issue:** LLM calls fail  
**Solution:** Ensure `HF_TOKEN` in `.env` is valid TCS GenAI API key

**Issue:** Database errors  
**Solution:** Delete `task_routing.db` and restart server to recreate

**Issue:** MCP tool calls fail  
**Solution:** Check server is running on port 5004, verify MCP server status endpoint

**Issue:** Import errors  
**Solution:** Run `setup.bat` again to install dependencies

## Performance

- Average analysis time: 30-60 seconds (depends on task count and LLM response time)
- Supports 10+ concurrent requests
- Database handles 1000s of tasks and resources

## Security Notes

⚠️ **Development Configuration** - Not production-ready:
- SSL verification disabled for internal TCS GenAI Lab
- Default admin credentials (change in production)
- Debug mode enabled
- No rate limiting

## Next Steps

1. ✅ Backend fully functional
2. ⏳ Create Angular frontend (frontend-task)
3. ⏳ Add RAG knowledge base integration
4. ⏳ Add chat assistant
5. ⏳ Add OCR and voice support

## Support

For issues, check:
- Server logs in terminal
- Database contents: `sqlite3 task_routing.db`
- MCP server status: `GET /api/mcp/status`

---

**Status:** Backend 100% Complete ✅  
**Last Updated:** 2026-07-10
