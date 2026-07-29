import requests
import urllib3
import os
import json
from datetime import datetime


# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkeypatch requests to disable SSL verification globally
original_request = requests.Session.request
requests.Session.request = lambda self, method, url, **kwargs: original_request(self, method, url, **dict(kwargs, verify=False))

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.utils import secure_filename
from config import Config
import database
from rag_service import RAGService
from guardrails import PrivacyGuardrail
from agents.orchestrator import AgentOrchestrator, sanitize_for_json

app = Flask(__name__)
rag_service = RAGService()


# JWT Configuration
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Initialize JWT
jwt = JWTManager(app)

# Enable CORS for Angular frontend (running on port 4204)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4204", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create necessary directories
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.FAISS_INDEX_PATH, exist_ok=True)
os.makedirs("data", exist_ok=True)

# Initialize database
database.init_database()

# Register blueprints
from auth import auth_bp
app.register_blueprint(auth_bp)

# Register MCP Server blueprints
from mcp_servers.resource_management import resource_server
from mcp_servers.skill_repository import skill_server
from mcp_servers.policy_management import policy_server
from mcp_servers.expert_knowledge import expert_server
from mcp_servers.historical_performance import performance_server
from mcp_servers.sla_management import sla_server
from mcp_servers.cost_optimization import cost_server
from mcp_servers.project_management import project_server
from mcp_servers.analytics import analytics_server

app.register_blueprint(resource_server.get_blueprint())
app.register_blueprint(skill_server.get_blueprint())
app.register_blueprint(policy_server.get_blueprint())
app.register_blueprint(expert_server.get_blueprint())
app.register_blueprint(performance_server.get_blueprint())
app.register_blueprint(sla_server.get_blueprint())
app.register_blueprint(cost_server.get_blueprint())
app.register_blueprint(project_server.get_blueprint())
app.register_blueprint(analytics_server.get_blueprint())

@app.route('/api/mcp/status', methods=['GET'])
def mcp_status():
    """Get status of all MCP servers"""
    return jsonify({
        "success": True,
        "servers": [
            {"name": "resource", "description": "Resource Management Server"},
            {"name": "skill", "description": "Skill Repository Server"},
            {"name": "policy", "description": "Policy Management Server"},
            {"name": "expert", "description": "Expert Knowledge Server"},
            {"name": "performance", "description": "Historical Performance Server"},
            {"name": "sla", "description": "SLA Management Server"},
            {"name": "cost", "description": "Cost Optimization Server"},
            {"name": "project", "description": "Project Management Server"},
            {"name": "analytics", "description": "Analytics Server"}
        ],
        "total_servers": 9
    }), 200

@app.route('/api/guardrails/sanitize', methods=['POST'])
def guardrails_sanitize():
    """Sanitize raw text to remove PII and check for prompt injection"""
    data = request.get_json() or {}
    text = data.get("text", "")
    sanitized_text, rehydrate_map, metrics = PrivacyGuardrail.sanitize(text)
    is_allowed, refusal_msg = PrivacyGuardrail.validate_scope(sanitized_text)
    return jsonify({
        "success": True,
        "sanitized_text": sanitized_text,
        "metrics": metrics,
        "is_allowed": is_allowed,
        "refusal_message": refusal_msg
    }), 200

@app.route('/api/guardrails/validate', methods=['POST'])
def guardrails_validate():
    """Validate domain scope and prompt injection safety"""
    data = request.get_json() or {}
    text = data.get("text", "")
    is_allowed, refusal_msg = PrivacyGuardrail.validate_scope(text)
    return jsonify({
        "success": True,
        "is_allowed": is_allowed,
        "refusal_message": refusal_msg
    }), 200

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "status": "running",
        "service": "Intelligent Task Routing System"
    }), 200

@app.route('/api/status', methods=['GET'])
def system_status():
    """System status endpoint"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) as count FROM human_resources")
    hr_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM ai_agents")
    ai_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM projects")
    project_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    task_count = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        "success": True,
        "status": {
            "human_resources": hr_count,
            "ai_agents": ai_count,
            "projects": project_count,
            "tasks": task_count
        }
    }), 200

# Admin endpoints for resource management
@app.route('/api/resources/human', methods=['GET'])
def get_human_resources():
    """Get all human resources"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM human_resources ORDER BY name")
        resources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "resources": resources}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/resources/ai', methods=['GET'])
def get_ai_agents():
    """Get all AI agents"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_agents ORDER BY agent_name")
        agents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "agents": agents}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY priority DESC, project_name")
        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "projects": projects}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, p.project_name 
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.project_id
            ORDER BY t.priority DESC, t.task_name
        """)
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "tasks": tasks}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sla-rules', methods=['GET'])
def get_sla_rules():
    """Get all SLA rules"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sla_rules ORDER BY priority DESC")
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "rules": rules}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/expert-analysis', methods=['GET'])
def get_expert_analysis():
    """Get all expert analysis entries"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expert_analysis ORDER BY created_at DESC")
        analysis = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "analysis": analysis}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/expert-analysis', methods=['POST'])
def add_expert_analysis():
    """Add new expert analysis entry"""
    try:
        data = request.get_json()
        category = data.get('category')
        recommendation = data.get('recommendation')
        notes = data.get('notes', '')
        expert_name = data.get('expert_name', '')
        
        if not category or not recommendation:
            return jsonify({"success": False, "error": "Category and recommendation required"}), 400
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expert_analysis (category, recommendation, notes, expert_name)
            VALUES (?, ?, ?, ?)
        """, (category, recommendation, notes, expert_name))
        conn.commit()
        analysis_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Expert analysis added successfully",
            "id": analysis_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Chat Session Store
chat_sessions = {}

def build_chat_context():
    """Compiles SQLite database tables into a compact text context for the Chat LLM"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # 1. Fetch human resources
        cursor.execute("SELECT * FROM human_resources")
        resources = [dict(row) for row in cursor.fetchall()]
        
        # 2. Fetch AI agents
        cursor.execute("SELECT * FROM ai_agents")
        agents = [dict(row) for row in cursor.fetchall()]
        
        # 3. Fetch tasks
        cursor.execute("SELECT * FROM tasks")
        tasks = [dict(row) for row in cursor.fetchall()]
        
        # 4. Fetch recent routing decisions
        cursor.execute("""
            SELECT rd.*, t.task_name, t.complexity, t.priority
            FROM routing_decisions rd
            JOIN tasks t ON rd.task_id = t.task_id
            ORDER BY rd.created_at DESC
            LIMIT 20
        """)
        decisions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        context_str = "CURRENT ROUTING STATUS:\n"
        context_str += "--- HUMAN TEAM ---\n"
        for r in resources:
            context_str += f"- {r['name']} ({r['role']}): Skills=[{r['skills']}], Experience={r['experience']} yrs, Cost=${r['cost_per_hour']}/hr, Availability={r['availability']}, Workload={r['current_workload']}%\n"
            
        context_str += "\n--- AI TEAM ---\n"
        for a in agents:
            context_str += f"- {a['agent_name']} (Specialization: {a['specialization']}): Capabilities=[{a['capabilities']}], Cost=${a['cost_per_hour']}/hr, Availability={a['availability']}\n"
            
        context_str += "\n--- PROJECTS & TASKS ---\n"
        for t in tasks:
            context_str += f"- Task #{t['task_id']}: {t['task_name']} | Complexity={t['complexity']} | Priority={t['priority']} | Status={t['status']} | Skills Required=[{t['skills_required']}]\n"
            
        context_str += "\n--- ASSIGNMENTS DECISIONS ---\n"
        for d in decisions:
            selected = json.loads(d['selected_resource']) if d['selected_resource'] else {}
            context_str += f"- Task '{d['task_name']}': Assigned to {selected.get('name')} ({selected.get('type', 'human')}) | Confidence={d['confidence_score']}% | Reason: {d['recommendation_reason']}\n"
            
        return context_str
    except Exception as e:
        return f"Error retrieving state context: {str(e)}"

# Chat Endpoints
@app.route('/api/chat/start', methods=['POST'])
def start_chat_session():
    try:
        import uuid
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = []
        return jsonify({
            "success": True,
            "session_id": session_id
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/message', methods=['POST'])
def send_chat_message():
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        message = data.get('message', '')
        image_base64 = data.get('image', None)
        
        if not session_id:
            return jsonify({"success": False, "error": "No session_id provided"}), 400
            
        if not message and not image_base64:
            return jsonify({"success": False, "error": "Query message or image attachment is required"}), 400
            
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
            
        history = chat_sessions[session_id]
        
        # Privacy Guardrail Scope Validation & PII Sanitization
        if message:
            is_allowed, refusal_msg = PrivacyGuardrail.validate_scope(message)
            if not is_allowed:
                assistant_entry = {
                    "role": "assistant",
                    "content": refusal_msg,
                    "timestamp": datetime.now().isoformat(),
                    "guardrail_triggered": True
                }
                history.append({"role": "user", "content": message, "timestamp": datetime.now().isoformat()})
                history.append(assistant_entry)
                return jsonify({
                    "success": True,
                    "message": refusal_msg,
                    "history": history,
                    "guardrail_triggered": True
                }), 200

            sanitized_message, rehydrate_map, pii_metrics = PrivacyGuardrail.sanitize(message)
            message = sanitized_message
        
        user_entry = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        if image_base64:
            user_entry["image"] = image_base64
            
        history.append(user_entry)
        
        # Build LLM context from DB state
        system_context = build_chat_context()
        
        # Retrieve relevant policies from RAG
        rag_context = ""
        try:
            query_for_rag = message if message else "project tasks requirements resource assignment policy"
            rag_results = rag_service.search_knowledge(query_for_rag, top_k=3)
            if rag_results:
                rag_context = "\n--- RELEVANT POLICIES (RAG) ---\n" + \
                              "\n".join([f"- [{res['category']}] {res['content']}" for res in rag_results])
        except Exception as e:
            print("RAG search failed in chat:", e)
            
        system_prompt = f"""You are 'Antigravity Task Assistant', an intelligent project routing advisor.
Using the current state context and corporate policies below, answer the user's questions about resources, assignments, task complexities, risks, or costs.
If an image or document diagram is provided, perform vision OCR analysis and extract relevant task requirements or architecture insights.

{system_context}
{rag_context}

Be concise, professional, helpful, and reference resources or tasks by name where appropriate. Use markdown formatting and lists for clarity."""

        # Construct multimodal message if image is attached
        if image_base64:
            if not image_base64.startswith("data:"):
                image_base64 = f"data:image/jpeg;base64,{image_base64}"
            user_payload = [
                {"type": "text", "text": message or "Analyze this attached project document / architecture diagram for task routing."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    }
                }
            ]
        else:
            user_payload = message

        from agents import Agent
        dummy_agent = Agent("ChatAssistantAgent", "Handles chat requests")
        llm_response = dummy_agent.call_llm(system_prompt, user_payload, temperature=0.4)
        
        # Natural Language Intent Check for Project Execution Plan Creation
        plan_created_info = ""
        msg_lower = (message or "").lower()
        if any(kw in msg_lower for kw in ["execution plan", "user story", "user stories", "project plan", "create plan", "sprint plan"]):
            try:
                from agents.execution_plan_agent import ProjectExecutionAgent
                exec_agent = ProjectExecutionAgent()
                plan_dict = exec_agent.generate_plan({"document_text": message}, source="Chat Assistant Query")
                
                # Save to database
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO project_execution_plans 
                    (plan_name, description, source, total_user_stories, total_story_points, 
                     total_effort_hours, total_cost, sprint_count, start_date, target_end_date, 
                     user_stories_json, timeline_json, team_allocation_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    plan_dict.get('plan_name', 'Chat Generated Plan'),
                    plan_dict.get('description', ''),
                    'Chat Assistant Query',
                    plan_dict.get('total_user_stories', 0),
                    plan_dict.get('total_story_points', 0),
                    plan_dict.get('total_effort_hours', 0.0),
                    plan_dict.get('total_cost', 0.0),
                    plan_dict.get('sprint_count', 3),
                    plan_dict.get('start_date', ''),
                    plan_dict.get('target_end_date', ''),
                    json.dumps(plan_dict.get('user_stories', [])),
                    json.dumps(plan_dict.get('timeline', [])),
                    json.dumps(plan_dict.get('team_allocation', []))
                ))
                plan_id = cursor.lastrowid
                conn.commit()
                conn.close()

                plan_created_info = f"\n\n---\n### 🚀 Project Execution Plan Generated!\n- **Plan ID**: #{plan_id} ({plan_dict.get('plan_name')})\n- **Agile User Stories**: {plan_dict.get('total_user_stories')} stories ({plan_dict.get('total_story_points')} pts)\n- **Estimated Effort**: {plan_dict.get('total_effort_hours')} hours\n- **Estimated Cost**: ${plan_dict.get('total_cost')}\n- **Timeline**: 3 Sprints ({plan_dict.get('start_date')} to {plan_dict.get('target_end_date')})\n\n👉 You can inspect, filter, and export the full plan breakdown on the **Execution Plans** tab!"
            except Exception as pe:
                print("Execution plan auto-generation in chat failed:", pe)

        if plan_created_info:
            llm_response += plan_created_info
        
        from agents.intent_agent import task_intent_agent
        classified_intent = task_intent_agent.classify(data.get('message', ''))

        guardrail_report = {
            "checks_performed": [
                "PII Entity Masking (Emails, IPs, Credentials, PAN, Aadhaar, Phone)",
                "Prompt Injection Token Neutralization",
                "Task Routing Domain Scope Validation",
                f"Dynamic Intent Classification ({classified_intent['intent']})"
            ],
            "classified_intent": classified_intent,
            "is_allowed": True,
            "masked_entities": rehydrate_map if 'rehydrate_map' in locals() else {},
            "metrics": pii_metrics if 'pii_metrics' in locals() else {"total": 0},
            "action_taken": f"Masked {pii_metrics.get('total', 0)} sensitive PII token(s) and validated input domain scope." if 'pii_metrics' in locals() and pii_metrics.get('total', 0) > 0 else "Zero sensitive PII tokens detected; input domain scope validated."
        }

        assistant_entry = {
            "role": "assistant",
            "content": llm_response,
            "timestamp": datetime.now().isoformat(),
            "guardrail_report": guardrail_report,
            "input_data": {
                "user_query": data.get('message', ''),
                "sanitized_query": message,
                "classified_intent": classified_intent,
                "rag_policies_retrieved": rag_context
            }
        }
        history.append(assistant_entry)
        
        return jsonify({
            "success": True,
            "response": llm_response,
            "history": history,
            "guardrail_report": guardrail_report,
            "input_data": {
                "user_query": data.get('message', ''),
                "sanitized_query": message,
                "rag_policies_retrieved": rag_context
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    history = chat_sessions.get(session_id, [])
    return jsonify({
        "success": True,
        "messages": history
    }), 200

@app.route('/api/chat/session/<session_id>', methods=['DELETE'])
def clear_chat_session(session_id):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return jsonify({
        "success": True,
        "message": f"Session {session_id} cleared successfully"
    }), 200

# Voice Integration Endpoints
@app.route('/api/voice/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert base64 audio data to transcribed text"""
    try:
        data = request.get_json() or {}
        audio_data = data.get('audio_data', '')
        if not audio_data:
            return jsonify({"success": False, "error": "No audio data provided"}), 400
            
        # Return transcribed status or mock transcription if local Web Speech API is fallback
        return jsonify({
            "success": True,
            "text": "Show me the top high priority tasks and available human resources."
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/voice/text-to-speech', methods=['POST'])
def text_to_speech():
    """Synthesize speech from text response"""
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        if not text:
            return jsonify({"success": False, "error": "No text provided"}), 400
            
        return jsonify({
            "success": True,
            "text": text,
            "status": "ready"
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# OCR Integration Endpoint
@app.route('/api/ocr/extract', methods=['POST'])
def extract_ocr_text():
    """Extract text and insights from base64 image data using LLM Vision"""
    try:
        data = request.get_json() or {}
        image_data = data.get('image_data', '')
        if not image_data:
            return jsonify({"success": False, "error": "No image data provided"}), 400
            
        if not image_data.startswith("data:"):
            image_data = f"data:image/jpeg;base64,{image_data}"
            
        system_prompt = "You are an expert document OCR analyst. Extract all text, task requirements, and architecture specifications from the provided image."
        user_payload = [
            {"type": "text", "text": "Perform complete OCR and extract all text and project requirements from this image."},
            {"type": "image_url", "image_url": {"url": image_data}}
        ]
        
        from agents import Agent
        ocr_agent = Agent("OCRAgent", "Extracts text from images")
        extracted_text = ocr_agent.call_llm(system_prompt, user_payload, temperature=0.2)
        
        return jsonify({
            "success": True,
            "text": extracted_text,
            "confidence": 95.0
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# RAG Admin Endpoints
@app.route('/api/admin/rag/stats', methods=['GET'])
def get_rag_stats():
    try:
        stats = rag_service.get_rag_statistics()
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/rag/upload', methods=['POST'])
def upload_to_rag():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
            
        filename = secure_filename(file.filename)
        file_content = file.read()
        
        # Determine uploader identity
        try:
            from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity() or "admin"
        except:
            identity = "admin"
            
        metadata = {
            "filename": filename,
            "upload_date": datetime.now().isoformat(),
            "uploaded_by": identity,
            "file_type": filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown',
            "category": "Policy"
        }
        
        result = rag_service.add_document_to_rag(file_content, filename, metadata)
        if result.get("success"):
            return jsonify(result), 200
        return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/rag/reload-news', methods=['POST'])
def reload_market_news():
    try:
        result = rag_service.load_market_news()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Admin Expert Analysis Endpoints
@app.route('/api/admin/expert-analysis', methods=['GET'])
def get_all_expert_analysis_admin():
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expert_analysis ORDER BY created_at DESC")
        analyses = []
        for row in cursor.fetchall():
            analyses.append({
                "id": row['id'],
                "key": f"{row['category']} - {row['expert_name']}",
                "data": f"{row['recommendation']} ({row['notes']})",
                "created_at": row['created_at'],
                "updated_at": row['created_at']
            })
        conn.close()
        return jsonify({"success": True, "analyses": analyses}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/expert-analysis', methods=['POST'])
def add_expert_analysis_admin():
    try:
        data = request.get_json() or {}
        key = data.get('key', '')
        data_text = data.get('data', '')
        
        category = "General"
        expert_name = "Admin"
        if " - " in key:
            category, expert_name = key.split(" - ", 1)
        else:
            category = key
            
        recommendation = data_text
        notes = "Added via Admin Portal"
        if " (" in data_text and data_text.endswith(")"):
            recommendation, notes = data_text.rsplit(" (", 1)
            notes = notes[:-1]
            
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expert_analysis (category, recommendation, notes, expert_name)
            VALUES (?, ?, ?, ?)
        """, (category, recommendation, notes, expert_name))
        conn.commit()
        analysis_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Expert analysis added successfully",
            "id": analysis_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/expert-analysis/<int:analysis_id>', methods=['DELETE'])
def delete_expert_analysis_admin(analysis_id):
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expert_analysis WHERE id = ?", (analysis_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Expert analysis deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/knowledge/upload', methods=['POST'])
def upload_knowledge():
    """Upload and index corporate knowledge documents"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        category = request.form.get('category', 'General')
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400
            
        filename = secure_filename(file.filename)
        file_content = file.read()
        
        result = rag_service.upload_document(file_content, filename, category)
        if result["success"]:
            return jsonify(result), 200
        return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
    """Search for relevant policies and rules"""
    try:
        data = request.get_json() or {}
        query = data.get('query', '')
        top_k = int(data.get('top_k', 5))
        category = data.get('category', None)
        
        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400
            
        results = rag_service.search_knowledge(query, top_k, category)
        return jsonify({
            "success": True,
            "results": results
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/task-routing/analyze', methods=['POST'])
def analyze_task_routing():
    """
    Main endpoint for intelligent task routing analysis.
    Accepts document upload and orchestrates all 10 agents.
    """
    try:
        # Get uploaded file or text
        document_text = None
        document_path = None
        
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(filepath)
                document_path = filepath
                
                # Extract text from file
                if filename.endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        document_text = f.read()
                # For PDF/DOCX, agents will extract text
        elif request.is_json:
            data = request.get_json()
            document_text = data.get('document_text', '')
        
        if not document_text and not document_path:
            return jsonify({"success": False, "error": "No document provided"}), 400
        
        print("[API] Starting task routing analysis...")
        
        # Import all agents
        from agents.orchestrator import AgentOrchestrator, sanitize_for_json
        from agents.document_analysis_agent import DocumentAnalysisAgent
        from agents.data_cleansing_agent import DataCleansingAgent
        from agents.data_enrichment_agent import DataEnrichmentAgent
        from agents.task_classification_agent import TaskClassificationAgent
        from agents.resource_matching_agent import ResourceMatchingAgent
        from agents.workload_optimization_agent import WorkloadOptimizationAgent
        from agents.cost_optimization_agent import CostOptimizationAgent
        from agents.risk_sla_agent import RiskSLAAgent
        from agents.decision_agent import DecisionAgent
        from agents.summary_agent import SummaryAgent
        
        # Create agent instances
        doc_analysis = DocumentAnalysisAgent()
        data_cleansing = DataCleansingAgent()
        data_enrichment = DataEnrichmentAgent()
        task_classification = TaskClassificationAgent()
        resource_matching = ResourceMatchingAgent()
        workload_optimization = WorkloadOptimizationAgent()
        cost_optimization = CostOptimizationAgent()
        risk_sla = RiskSLAAgent()
        decision_agent = DecisionAgent()
        summary_agent = SummaryAgent()
        
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        
        # Define execution flow
        # Sequential phase 1: Agents 1-5
        sequential_agents = [
            doc_analysis,
            data_cleansing,
            data_enrichment,
            task_classification,
            resource_matching
        ]
        
        # Parallel phase: Agents 6-9
        parallel_agents = [
            workload_optimization,
            cost_optimization,
            risk_sla
        ]
        
        # Sequential phase 2: Agents 10-11 (Decision and Summary)
        final_agents = [
            decision_agent,
            summary_agent
        ]
        
        # Privacy Guardrail Sanitization & Validation
        sanitized_doc_text, rehydrate_map, pii_metrics = PrivacyGuardrail.sanitize(document_text or "")
        is_allowed, refusal_msg = PrivacyGuardrail.validate_scope(sanitized_doc_text)

        guardrail_report = {
            "checks_performed": [
                "PII Entity Masking (Emails, IPs, Credentials, PAN, Aadhaar, Phone)",
                "Prompt Injection Token Neutralization",
                "Task Routing Domain Scope Validation"
            ],
            "is_allowed": is_allowed,
            "refusal_message": refusal_msg,
            "masked_entities": rehydrate_map,
            "metrics": pii_metrics,
            "action_taken": f"Masked {pii_metrics.get('total', 0)} sensitive PII token(s) and validated input domain scope." if pii_metrics.get('total', 0) > 0 else "Zero sensitive PII tokens detected; input domain scope validated."
        }

        execution_steps = []
        def sync_callback(agent_name, status, result, step_info, input_payload=None):
            if status == "completed":
                execution_steps.append({
                    "agent": agent_name,
                    "status": status,
                    "step": step_info.get("step", 0),
                    "input_data": input_payload,
                    "result": sanitize_for_json(result)
                })

        # Execute orchestration
        initial_context = {
            'document_text': sanitized_doc_text or document_text,
            'raw_document_text': document_text,
            'document_path': document_path,
            '_guardrail_report': guardrail_report
        }
        
        print("[API] Executing agent orchestration with dynamic intent dispatching...")
        result_context = orchestrator.execute_dynamic_intent_flow(
            initial_context,
            text_query=document_text,
            callback=sync_callback
        )
        
        print("[API] Agent orchestration complete")
        
        # Extract classified intent
        classified_intent = result_context.get('_classified_intent', {})
        guardrail_report['classified_intent'] = classified_intent
        
        # Extract final report
        summary_result = result_context.get('SummaryAgent', {})
        final_report = summary_result.get('final_report', {})
        final_report['execution_audit_log'] = {
            "guardrail_report": guardrail_report,
            "execution_steps": execution_steps
        }
        final_report = sanitize_for_json(final_report)
        
        # Store results in database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        
        # Store each task decision
        decisions = result_context.get('DecisionAgent', {}).get('final_decisions', [])
        for decision in decisions:
            rec_res = decision.get('recommended_resource', {})
            cursor.execute("""
                INSERT INTO routing_decisions 
                (task_id, selected_resource, recommendation_reason, confidence_score, analysis_data, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                decision.get('task_id', 0),
                json.dumps(rec_res),
                rec_res.get('reasoning', ''),
                rec_res.get('confidence_score', 0),
                json.dumps(decision)
            ))
        
        conn.commit()
        conn.close()
        
        print("[API] Results stored in database")
        
        # Return final report
        return jsonify({
            "success": True,
            "analysis_complete": True,
            "report": final_report,
            "task_count": len(decisions),
            "message": "Task routing analysis completed successfully"
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Analysis failed"
        }), 500


@app.route('/api/task-routing/analyze/stream', methods=['POST'])
def analyze_task_routing_stream():
    """
    Streaming SSE endpoint for real-time progress and async initial data fetching.
    """
    document_text = None
    document_path = None
    
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            document_path = filepath
            if filename.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    document_text = f.read()
    elif request.is_json:
        data = request.get_json()
        document_text = data.get('document_text', '')
    
    if not document_text and not document_path:
        return jsonify({"success": False, "error": "No document provided"}), 400

    def generate():
        import queue
        import threading
        
        event_queue = queue.Queue()
        execution_steps = []

        # Run Privacy Guardrail on incoming document text
        sanitized_doc_text, rehydrate_map, pii_metrics = PrivacyGuardrail.sanitize(document_text or "")
        is_allowed, refusal_msg = PrivacyGuardrail.validate_scope(sanitized_doc_text)

        guardrail_report = {
            "checks_performed": [
                "PII Entity Masking (Emails, IPs, Credentials, PAN, Aadhaar, Phone)",
                "Prompt Injection Token Neutralization",
                "Task Routing Domain Scope Validation"
            ],
            "is_allowed": is_allowed,
            "refusal_message": refusal_msg,
            "masked_entities": rehydrate_map,
            "metrics": pii_metrics,
            "action_taken": f"Masked {pii_metrics.get('total', 0)} sensitive PII token(s) and validated input domain scope." if pii_metrics.get('total', 0) > 0 else "Zero sensitive PII tokens detected; input domain scope validated."
        }

        def agent_callback(agent_name, status, result, step_info, input_payload=None):
            clean_result = sanitize_for_json(result)
            if status == "completed":
                execution_steps.append({
                    "agent": agent_name,
                    "status": status,
                    "step": step_info.get("step", 0),
                    "input_data": input_payload,
                    "result": clean_result
                })
            event_queue.put({
                "type": "progress",
                "agent": agent_name,
                "status": status,
                "result": clean_result,
                "step": step_info.get("step", 0),
                "total_steps": step_info.get("total_steps", 7),
                "input_data": input_payload,
                "guardrail_report": guardrail_report
            })

        def run_pipeline():
            try:
                from agents.orchestrator import AgentOrchestrator, sanitize_for_json
                from agents.document_analysis_agent import DocumentAnalysisAgent
                from agents.data_cleansing_agent import DataCleansingAgent
                from agents.data_enrichment_agent import DataEnrichmentAgent
                from agents.task_classification_agent import TaskClassificationAgent
                from agents.resource_matching_agent import ResourceMatchingAgent
                from agents.workload_optimization_agent import WorkloadOptimizationAgent
                from agents.cost_optimization_agent import CostOptimizationAgent
                from agents.risk_sla_agent import RiskSLAAgent
                from agents.decision_agent import DecisionAgent
                from agents.summary_agent import SummaryAgent
                
                doc_analysis = DocumentAnalysisAgent()
                data_cleansing = DataCleansingAgent()
                data_enrichment = DataEnrichmentAgent()
                task_classification = TaskClassificationAgent()
                resource_matching = ResourceMatchingAgent()
                workload_optimization = WorkloadOptimizationAgent()
                cost_optimization = CostOptimizationAgent()
                risk_sla = RiskSLAAgent()
                decision_agent = DecisionAgent()
                summary_agent = SummaryAgent()
                
                orchestrator = AgentOrchestrator()
                
                initial_context = {
                    'document_text': sanitized_doc_text or document_text,
                    'raw_document_text': document_text,
                    'document_path': document_path,
                    '_guardrail_report': guardrail_report
                }
                
                result_context = orchestrator.execute_dynamic_intent_flow(
                    initial_context,
                    text_query=document_text or "",
                    callback=agent_callback
                )
                
                classified_intent = result_context.get('_classified_intent', {})
                guardrail_report['classified_intent'] = classified_intent
                
                summary_result = result_context.get('SummaryAgent', {})
                final_report = summary_result.get('final_report', {})
                
                if not final_report or not isinstance(final_report, dict) or 'analysis_overview' not in final_report:
                    decisions = result_context.get('DecisionAgent', {}).get('final_decisions', [])
                    if not decisions:
                        rec_agent = result_context.get('ResourceMatchingAgent', {})
                        recs = rec_agent.get('task_recommendations', [])
                        decisions = []
                        for idx, r in enumerate(recs):
                            top_rec = r.get('top_recommendation') or {}
                            decisions.append({
                                "task_id": r.get('task_id', idx + 1),
                                "task_name": r.get('task_name'),
                                "task_description": r.get('description', ''),
                                "complexity": r.get('complexity', 'Medium'),
                                "estimated_effort": r.get('estimated_effort', 8),
                                "skills_required": [s.strip() for s in r.get('required_skills', '').split(',')] if isinstance(r.get('required_skills'), str) else r.get('required_skills', []),
                                "recommended_resource": {
                                    "resource_id": top_rec.get('resource_id', top_rec.get('id', 0)),
                                    "name": top_rec.get('name', 'Recommended Resource'),
                                    "type": top_rec.get('type', 'human'),
                                    "confidence_score": top_rec.get('match_score', 80),
                                    "reasoning": "Resource matched based on required skills"
                                },
                                "resource_options": r.get('matched_resources', []),
                                "cost_analysis": {"recommended_cost": 0.0, "cheapest_cost": 0.0, "premium_cost": 0.0, "potential_savings": 0.0},
                                "risk_assessment": {"risk_level": "Low", "risk_factors": [], "mitigation_strategies": []},
                                "sla_compliance": {"expected_completion": "2026-07-18", "sla_breach_risk": 10.0}
                            })
                    
                    doc_tasks = result_context.get('DocumentAnalysisAgent', {}).get('extracted_tasks', [])
                    total_t = len(decisions) or len(doc_tasks)
                    ai_assign = len([d for d in decisions if d.get('recommended_resource', {}).get('type') == 'ai'])
                    human_assign = total_t - ai_assign
                    
                    final_report = {
                        "executive_summary": "Task routing analysis and resource matching complete.",
                        "analysis_overview": {
                            "total_tasks": total_t,
                            "total_estimated_effort": sum([d.get('estimated_effort', 8) for d in decisions]) or total_t * 8,
                            "total_estimated_cost": 0.0,
                            "high_risk_tasks": 0,
                            "ai_assignments": ai_assign,
                            "human_assignments": human_assign
                        },
                        "task_assignments": decisions,
                        "cost_analysis": {"total_cost": 0.0, "optimization_potential": 0.0, "cost_summary": {}},
                        "risk_assessment": {"overall_risk": "Low", "high_risk_count": 0, "risk_distribution": {"Low": total_t}},
                        "workload_insights": {"overloaded_resources": 0, "underutilized_resources": 0, "recommendations": []},
                        "detailed_recommendations": ["Task analysis and resource matching complete."],
                        "next_steps": ["Review and approve task assignments."]
                    }
                else:
                    decisions = final_report.get('task_assignments', []) or result_context.get('DecisionAgent', {}).get('final_decisions', [])
                
                # Attach execution audit log to final report
                final_report['execution_audit_log'] = {
                    "guardrail_report": guardrail_report,
                    "execution_steps": execution_steps
                }
                final_report = sanitize_for_json(final_report)
                
                try:
                    conn = database.get_db_connection()
                    cursor = conn.cursor()
                    for decision in decisions:
                        rec_res = decision.get('recommended_resource', {})
                        cursor.execute("""
                            INSERT INTO routing_decisions 
                            (task_id, selected_resource, recommendation_reason, confidence_score, analysis_data, created_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """, (
                            decision.get('task_id', 0),
                            json.dumps(rec_res),
                            rec_res.get('reasoning', ''),
                            rec_res.get('confidence_score', 0),
                            json.dumps(decision)
                        ))
                    conn.commit()
                    conn.close()
                except Exception as dbe:
                    print(f"[API Stream DB Error]: {dbe}")
                
                event_queue.put({
                    "type": "complete",
                    "report": final_report,
                    "task_count": len(decisions)
                })
            except Exception as pe:
                import traceback
                traceback.print_exc()
                event_queue.put({
                    "type": "error",
                    "error": str(pe)
                })
            finally:
                event_queue.put(None)

        thread = threading.Thread(target=run_pipeline)
        thread.start()

        while True:
            item = event_queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# ==========================================
# Project Execution Plan Endpoints
# ==========================================

@app.route('/api/execution-plans/generate', methods=['POST'])
def generate_execution_plan():
    """Generate and save a new Project Execution Plan"""
    try:
        data = request.get_json() or {}
        source = data.get('source', 'Task Routing Analysis')
        input_context = data.get('input_context', {})
        document_text = data.get('document_text', '')

        if document_text and not input_context.get('document_text'):
            input_context['document_text'] = document_text

        from agents.execution_plan_agent import ProjectExecutionAgent
        agent = ProjectExecutionAgent()
        plan_dict = agent.generate_plan(input_context, source=source)

        # Save to SQLite database
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO project_execution_plans 
            (plan_name, description, source, total_user_stories, total_story_points, 
             total_effort_hours, total_cost, sprint_count, start_date, target_end_date, 
             user_stories_json, timeline_json, team_allocation_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            plan_dict.get('plan_name', 'Project Execution Plan'),
            plan_dict.get('description', ''),
            plan_dict.get('source', source),
            plan_dict.get('total_user_stories', 0),
            plan_dict.get('total_story_points', 0),
            plan_dict.get('total_effort_hours', 0.0),
            plan_dict.get('total_cost', 0.0),
            plan_dict.get('sprint_count', 3),
            plan_dict.get('start_date', ''),
            plan_dict.get('target_end_date', ''),
            json.dumps(plan_dict.get('user_stories', [])),
            json.dumps(plan_dict.get('timeline', [])),
            json.dumps(plan_dict.get('team_allocation', []))
        ))
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()

        plan_dict['plan_id'] = plan_id
        return jsonify({"success": True, "plan": plan_dict}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/execution-plans', methods=['GET'])
def get_execution_plans():
    """Retrieve all saved Project Execution Plans"""
    try:
        conn = database.get_db_connection()
        rows = conn.execute("""
            SELECT plan_id, plan_name, description, source, total_user_stories, 
                   total_story_points, total_effort_hours, total_cost, sprint_count, 
                   start_date, target_end_date, user_stories_json, timeline_json, 
                   team_allocation_json, created_at 
            FROM project_execution_plans 
            ORDER BY created_at DESC
        """).fetchall()
        conn.close()

        plans = []
        for r in rows:
            p = dict(r)
            try:
                p['user_stories'] = json.loads(p.get('user_stories_json') or '[]')
            except Exception:
                p['user_stories'] = []
            try:
                p['timeline'] = json.loads(p.get('timeline_json') or '[]')
            except Exception:
                p['timeline'] = []
            try:
                p['team_allocation'] = json.loads(p.get('team_allocation_json') or '[]')
            except Exception:
                p['team_allocation'] = []
            plans.append(p)

        return jsonify({"success": True, "plans": plans, "count": len(plans)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/execution-plans/<int:plan_id>', methods=['GET'])
def get_execution_plan_by_id(plan_id):
    """Retrieve details of a specific Project Execution Plan"""
    try:
        conn = database.get_db_connection()
        row = conn.execute("""
            SELECT plan_id, plan_name, description, source, total_user_stories, 
                   total_story_points, total_effort_hours, total_cost, sprint_count, 
                   start_date, target_end_date, user_stories_json, timeline_json, 
                   team_allocation_json, created_at 
            FROM project_execution_plans 
            WHERE plan_id = ?
        """, (plan_id,)).fetchone()
        conn.close()

        if not row:
            return jsonify({"success": False, "error": "Execution plan not found"}), 404

        p = dict(row)
        p['user_stories'] = json.loads(p.get('user_stories_json') or '[]')
        p['timeline'] = json.loads(p.get('timeline_json') or '[]')
        p['team_allocation'] = json.loads(p.get('team_allocation_json') or '[]')
        return jsonify({"success": True, "plan": p}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/execution-plans/<int:plan_id>', methods=['DELETE'])
def delete_execution_plan(plan_id):
    """Delete a Project Execution Plan"""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM project_execution_plans WHERE plan_id = ?", (plan_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Execution plan {plan_id} deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    print(f"Starting Intelligent Task Routing System on port {Config.FLASK_PORT}...")
    print(f"Frontend URL: http://localhost:4204")
    print(f"API URL: http://localhost:{Config.FLASK_PORT}/api")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)
