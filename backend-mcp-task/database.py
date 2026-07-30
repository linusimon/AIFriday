"""
Database models and initialization for Intelligent Task Routing System
Powered by Standalone Generic SQLite MCP Server Gateway
"""
import sqlite3
import bcrypt
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from config import Config
from mcp_sqlite_server import MCPSqliteClient

# Global MCP Client instance pointing to generic SQLite MCP Server
mcp_client = MCPSqliteClient(db_path=Config.DATABASE_PATH)

def execute_query(sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Execute a read SQL query (SELECT) via generic SQLite MCP client."""
    return mcp_client.execute_query(sql, params)

def execute_statement(sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Execute a write/update SQL statement (INSERT, UPDATE, DELETE, DDL) via generic SQLite MCP client."""
    return mcp_client.execute_statement(sql, params)

def execute_batch(statements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute a batch of SQL statements via generic SQLite MCP client."""
    return mcp_client.execute_batch(statements)

def get_db_connection():
    """Create and return a direct database connection for legacy callers"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables and sample data via generic MCP statement execution"""
    
    # 1. Create Users table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Create HumanResources table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS human_resources (
            resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT NOT NULL,
            experience INTEGER NOT NULL,
            availability TEXT NOT NULL,
            current_workload REAL NOT NULL DEFAULT 0,
            quality_score REAL NOT NULL DEFAULT 85,
            performance_score REAL NOT NULL DEFAULT 85,
            cost_per_hour REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Create AIAgents table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS ai_agents (
            agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            capabilities TEXT NOT NULL,
            specialization TEXT NOT NULL,
            availability TEXT NOT NULL,
            performance_score REAL NOT NULL DEFAULT 90,
            quality_score REAL NOT NULL DEFAULT 90,
            cost_per_hour REAL NOT NULL DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Create Projects table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            business_area TEXT NOT NULL,
            sla TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. Create Tasks table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            task_name TEXT NOT NULL,
            description TEXT NOT NULL,
            skills_required TEXT NOT NULL,
            complexity TEXT NOT NULL,
            estimated_effort REAL NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (project_id)
        )
    ''')
    
    # 6. Create HistoricalAssignments table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS historical_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            resource_id INTEGER,
            resource_type TEXT NOT NULL,
            completion_time REAL NOT NULL,
            quality_score REAL NOT NULL,
            outcome TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
    ''')
    
    # 7. Create SLARules table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS sla_rules (
            sla_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            target_duration REAL NOT NULL,
            priority TEXT NOT NULL,
            escalation_rule TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 8. Create CostModels table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS cost_models (
            cost_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_type TEXT NOT NULL,
            cost_per_hour REAL NOT NULL,
            cost_weight REAL NOT NULL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 9. Create ExpertAnalysis table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS expert_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            notes TEXT,
            expert_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 10. Create ProjectExecutionPlans table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS project_execution_plans (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_name TEXT NOT NULL,
            description TEXT,
            source TEXT DEFAULT 'Task Routing Analysis',
            total_user_stories INTEGER NOT NULL DEFAULT 0,
            total_story_points INTEGER NOT NULL DEFAULT 0,
            total_effort_hours REAL NOT NULL DEFAULT 0,
            total_cost REAL NOT NULL DEFAULT 0,
            sprint_count INTEGER NOT NULL DEFAULT 1,
            start_date TEXT,
            target_end_date TEXT,
            user_stories_json TEXT NOT NULL,
            timeline_json TEXT NOT NULL,
            team_allocation_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 11. Create RoutingDecisions table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS routing_decisions (
            decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            selected_resource TEXT NOT NULL,
            recommendation_reason TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            analysis_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id)
        )
    ''')
    
    # 12. Create ChatSessions table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id INTEGER,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (decision_id) REFERENCES routing_decisions (decision_id)
        )
    ''')
    
    # 13. Create ChatMessages table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    # 14. Create AuditLogs table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_id TEXT,
            action TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL
        )
    ''')

    # 15. Create GDPR audit trail table
    execute_statement('''
        CREATE TABLE IF NOT EXISTS gdpr_audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action_type TEXT,
            identifier_hash TEXT,
            status TEXT,
            details TEXT
        )
    ''')

    # Ensure admin user exists
    admin = execute_query("SELECT id FROM users WHERE username = 'admin'")
    if not admin:
        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        execute_statement(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ["admin", password_hash, "admin"]
        )
        print("[DATABASE] Created default admin user (username: admin, password: admin123)")

    # Ensure regular user exists
    regular_user = execute_query("SELECT id FROM users WHERE username = 'user'")
    if not regular_user:
        password_hash = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        execute_statement(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ["user", password_hash, "user"]
        )
        print("[DATABASE] Created default regular user (username: user, password: user123)")

    # Seed sample data if empty
    hr_rows = execute_query("SELECT COUNT(*) as count FROM human_resources")
    if not hr_rows or hr_rows[0]['count'] == 0:
        seed_sample_data()
        print("[DATABASE] Seeded sample data via generic MCP statements")

    print("[DATABASE] Database initialized successfully via generic SQLite MCP Server engine")

def seed_sample_data():
    """Seed the database with realistic sample data via generic MCP statement batching"""
    
    # HumanResources
    human_resources = [
        ("John Smith", "Senior Developer", "Python,Java,SQL,Machine Learning", 8, "Available", 45, 92, 90, 75),
        ("Sarah Johnson", "Full Stack Developer", "React,Node.js,MongoDB,AWS", 5, "Available", 60, 88, 87, 65),
        ("Michael Chen", "Data Scientist", "Python,TensorFlow,Statistics,SQL", 6, "Available", 30, 95, 93, 80),
        ("Emily Davis", "DevOps Engineer", "Docker,Kubernetes,CI/CD,AWS", 7, "Available", 70, 90, 89, 70),
        ("David Wilson", "Backend Developer", "Python,Flask,PostgreSQL,Redis", 4, "Available", 50, 85, 84, 60),
        ("Lisa Anderson", "Frontend Developer", "Angular,TypeScript,CSS,UX Design", 5, "Available", 40, 88, 86, 62),
        ("Robert Taylor", "ML Engineer", "PyTorch,NLP,Computer Vision,MLOps", 9, "Available", 80, 96, 94, 85),
        ("Jennifer Martinez", "QA Engineer", "Selenium,Pytest,Test Automation,CI/CD", 6, "Available", 35, 90, 88, 58),
        ("James Brown", "Solutions Architect", "System Design,Cloud Architecture,Security", 12, "Available", 75, 94, 92, 90),
        ("Patricia Garcia", "Business Analyst", "Requirements Analysis,Documentation,Agile", 7, "Available", 55, 87, 85, 65),
        ("Christopher Lee", "Database Administrator", "SQL,Oracle,Performance Tuning,Backup", 10, "Available", 60, 91, 89, 72),
        ("Mary Rodriguez", "UI/UX Designer", "Figma,User Research,Prototyping,Design Systems", 6, "Available", 45, 93, 91, 68),
        ("Daniel Martinez", "Security Engineer", "Penetration Testing,Compliance,Encryption", 8, "Busy", 85, 95, 93, 78),
        ("Jessica Thompson", "Project Manager", "Project Planning,Risk Management,Stakeholder Management", 11, "Available", 70, 89, 87, 75),
        ("Matthew White", "Cloud Architect", "AWS,Azure,Terraform,Microservices", 9, "Available", 65, 92, 90, 82),
        ("Ashley Harris", "Technical Writer", "Documentation,API Documentation,Technical Content", 5, "Available", 30, 86, 84, 55),
        ("Andrew Clark", "Site Reliability Engineer", "Monitoring,Incident Response,Performance Optimization", 7, "Available", 75, 90, 88, 73),
        ("Stephanie Lewis", "Data Engineer", "ETL,Data Pipelines,Spark,Airflow", 6, "Available", 50, 88, 86, 67),
        ("Joshua Walker", "Mobile Developer", "iOS,Swift,Android,Kotlin", 5, "Busy", 90, 87, 85, 63),
        ("Amanda Hall", "Scrum Master", "Agile,Scrum,Team Facilitation,Coaching", 8, "Available", 60, 89, 87, 70),
    ]
    
    for hr in human_resources:
        execute_statement('''
            INSERT INTO human_resources 
            (name, role, skills, experience, availability, current_workload, quality_score, performance_score, cost_per_hour)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', list(hr))
    
    # AIAgents
    ai_agents = [
        ("CodeGen AI", "Code Generation,Code Review,Refactoring", "Backend Development", "Available", 95, 92, 8),
        ("DataAnalyzer AI", "Data Analysis,Statistical Modeling,Visualization", "Data Science", "Available", 93, 90, 10),
        ("DocumentParser AI", "Document Processing,OCR,Text Extraction", "Document Analysis", "Available", 91, 89, 5),
        ("SecurityScanner AI", "Vulnerability Detection,Code Analysis,Security Audit", "Security", "Available", 94, 92, 12),
        ("TestGen AI", "Test Generation,Test Automation,Code Coverage", "Quality Assurance", "Available", 90, 88, 7),
        ("NLPAssistant AI", "Natural Language Processing,Sentiment Analysis,Text Classification", "NLP", "Available", 92, 90, 9),
        ("ImageProcessor AI", "Image Recognition,Object Detection,Image Enhancement", "Computer Vision", "Available", 91, 89, 11),
        ("ChatBot AI", "Conversational AI,Intent Recognition,Response Generation", "Customer Service", "Available", 89, 87, 6),
        ("CodeOptimizer AI", "Performance Optimization,Code Refactoring,Best Practices", "Code Quality", "Available", 93, 91, 8),
        ("DataCleaner AI", "Data Cleaning,Data Validation,Data Transformation", "Data Engineering", "Available", 90, 88, 7),
    ]
    
    for agent in ai_agents:
        execute_statement('''
            INSERT INTO ai_agents 
            (agent_name, capabilities, specialization, availability, performance_score, quality_score, cost_per_hour)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', list(agent))
    
    # Projects
    projects = [
        ("E-Commerce Platform Redesign", "High", "In Progress", "Retail", "7 days"),
        ("Customer Analytics Dashboard", "Medium", "Planning", "Analytics", "14 days"),
        ("Mobile Banking App", "Critical", "In Progress", "Finance", "3 days"),
        ("Supply Chain Optimization", "High", "Planning", "Operations", "10 days"),
        ("HR Management System", "Medium", "On Hold", "Human Resources", "21 days"),
    ]
    
    for proj in projects:
        execute_statement('''
            INSERT INTO projects (project_name, priority, status, business_area, sla)
            VALUES (?, ?, ?, ?, ?)
        ''', list(proj))
    
    # Tasks
    tasks = [
        (1, "Implement Payment Gateway Integration", "Integrate Stripe payment processing with existing checkout flow", "Python,REST APIs,Payment Systems", "High", 40, "Critical"),
        (1, "Design Product Catalog UI", "Create responsive product catalog with filtering and search", "React,CSS,UX Design", "Medium", 24, "High"),
        (1, "Database Performance Optimization", "Optimize queries and add indexes for faster page loads", "SQL,Performance Tuning,PostgreSQL", "High", 16, "High"),
        (2, "Build Real-time Analytics Pipeline", "Create ETL pipeline for customer behavior data", "Python,Spark,Kafka,Data Engineering", "High", 80, "Medium"),
        (2, "Develop Interactive Dashboards", "Create visualization dashboards using Power BI", "Power BI,Data Visualization,SQL", "Medium", 32, "Medium"),
        (3, "Implement Biometric Authentication", "Add fingerprint and face recognition login", "iOS,Android,Security,Biometrics", "Critical", 60, "Critical"),
        (3, "Build Transaction History Feature", "Display transaction history with filters and export", "Mobile Development,REST APIs,UI Design", "Medium", 24, "High"),
        (4, "Develop Demand Forecasting Model", "Build ML model to predict inventory needs", "Machine Learning,Python,TensorFlow,Statistics", "High", 100, "Medium"),
        (4, "Create Supplier Management Module", "Build interface for managing supplier relationships", "Full Stack Development,Database Design", "Medium", 48, "Medium"),
        (5, "Design Employee Self-Service Portal", "Create portal for leave requests and document access", "Angular,REST APIs,Authentication", "Low", 56, "Low"),
    ]
    
    for task in tasks:
        execute_statement('''
            INSERT INTO tasks 
            (project_id, task_name, description, skills_required, complexity, estimated_effort, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', list(task))
    
    # HistoricalAssignments
    historical_assignments = [
        (1, 1, "Human", 38, 94, "Success"),
        (2, 12, "Human", 22, 91, "Success"),
        (3, 11, "Human", 14, 96, "Success"),
        (4, 3, "Human", 85, 89, "Success"),
        (5, 2, "AI", 28, 88, "Success"),
        (1, 5, "Human", 42, 92, "Success"),
        (2, 15, "Human", 20, 90, "Success"),
        (3, 19, "Human", 62, 85, "Delayed"),
        (4, 18, "Human", 78, 91, "Success"),
        (5, 6, "Human", 54, 87, "Success"),
    ]
    
    for ha in historical_assignments:
        execute_statement('''
            INSERT INTO historical_assignments 
            (task_id, resource_id, resource_type, completion_time, quality_score, outcome)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', list(ha))
    
    # SLARules
    sla_rules = [
        ("Critical", 72, "Critical", "Immediate escalation to senior management"),
        ("High", 168, "High", "Escalate to team lead after 24 hours"),
        ("Medium", 336, "Medium", "Escalate to project manager after 3 days"),
        ("Low", 720, "Low", "Review in weekly planning meeting"),
    ]
    
    for rule in sla_rules:
        execute_statement('''
            INSERT INTO sla_rules (category, target_duration, priority, escalation_rule)
            VALUES (?, ?, ?, ?)
        ''', list(rule))
    
    # CostModels
    cost_models = [
        ("Senior Developer", 80, 1.2),
        ("Mid-level Developer", 60, 1.0),
        ("Junior Developer", 40, 0.8),
        ("AI Agent", 8, 0.5),
        ("Specialist", 90, 1.3),
    ]
    
    for cm in cost_models:
        execute_statement('''
            INSERT INTO cost_models (resource_type, cost_per_hour, cost_weight)
            VALUES (?, ?, ?)
        ''', list(cm))
    
    # ExpertAnalysis
    expert_analysis = [
        ("Backend Development", "For high-complexity backend tasks, prioritize developers with 5+ years experience and proven track record in similar technologies. Consider AI agents for boilerplate code generation.", "Assign senior developers for critical path items", "Tech Lead - Alex Kumar"),
        ("Frontend Development", "Modern frontend frameworks like React and Angular require dedicated specialists. Avoid mixing backend and frontend assignments for better quality.", "UI/UX alignment is critical", "Frontend Architect - Maria Santos"),
        ("Machine Learning", "ML projects require data scientists with strong statistical background. Start with data exploration phase before model development.", "Ensure data quality first", "ML Lead - Dr. James Watson"),
        ("Security", "Security-critical tasks must be assigned to certified security professionals. Always perform code review and penetration testing.", "Never compromise on security", "CISO - Sarah Miller"),
        ("Data Engineering", "Large-scale data pipelines require experience with distributed systems. Consider cloud-native solutions for scalability.", "Plan for data governance", "Data Architect - Raj Patel"),
        ("Mobile Development", "iOS and Android require platform-specific expertise. Cross-platform frameworks may reduce quality for complex apps.", "Native development for critical apps", "Mobile Lead - Chen Wei"),
        ("DevOps", "Infrastructure automation is critical. Prioritize engineers with CI/CD and cloud expertise.", "Automation over manual processes", "DevOps Manager - Tom Anderson"),
    ]
    
    for ea in expert_analysis:
        execute_statement('''
            INSERT INTO expert_analysis (category, recommendation, notes, expert_name)
            VALUES (?, ?, ?, ?)
        ''', list(ea))

if __name__ == "__main__":
    init_database()
