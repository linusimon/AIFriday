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

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.utils import secure_filename
from config import Config
import database
from rag_service import RAGService

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
        
        if not session_id:
            return jsonify({"success": False, "error": "No session_id provided"}), 400
            
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
            
        history = chat_sessions[session_id]
        history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build LLM context from DB state
        system_context = build_chat_context()
        
        # Retrieve relevant policies from RAG
        rag_context = ""
        try:
            rag_results = rag_service.search_knowledge(message, top_k=3)
            if rag_results:
                rag_context = "\n--- RELEVANT POLICIES (RAG) ---\n" + \
                              "\n".join([f"- [{res['category']}] {res['content']}" for res in rag_results])
        except Exception as e:
            print("RAG search failed in chat:", e)
            
        system_prompt = f"""You are a helpful project routing assistant for the Intelligent Task Routing System.
Using the current state context and corporate policies below, answer the user's questions about resources, assignments, task complexities, risks, or costs.

{system_context}
{rag_context}

Be concise, helpful, and reference resources or tasks by name where appropriate. If asked about policies, refer to the uploaded RAG documents."""

        from agents import Agent
        dummy_agent = Agent("ChatAssistantAgent", "Handles chat requests")
        llm_response = dummy_agent.call_llm(system_prompt, message, temperature=0.5)
        
        history.append({
            "role": "assistant",
            "content": llm_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "response": llm_response,
            "tool_calls": []
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
        from agents.orchestrator import AgentOrchestrator
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
        
        # Execute orchestration
        initial_context = {
            'document_text': document_text,
            'document_path': document_path
        }
        
        print("[API] Executing agent orchestration...")
        result_context = orchestrator.execute_custom_flow(
            initial_context,
            sequential_agents,
            parallel_agents,
            final_agents
        )
        
        print("[API] Agent orchestration complete")
        
        # Extract final report
        summary_result = result_context.get('SummaryAgent', {})
        final_report = summary_result.get('final_report', {})
        
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

if __name__ == '__main__':
    print(f"Starting Intelligent Task Routing System on port {Config.FLASK_PORT}...")
    print(f"Frontend URL: http://localhost:4204")
    print(f"API URL: http://localhost:{Config.FLASK_PORT}/api")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)
