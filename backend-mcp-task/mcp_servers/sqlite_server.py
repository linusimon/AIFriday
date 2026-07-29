"""
AIFriday Intelligent Task Routing - Standalone Model Context Protocol (MCP) SQLite Server
Provides tools for local SQL queries against task routing, resources, policy management,
knowledge base, and GDPR audit trails.
"""

import os
import sys
import sqlite3
import json
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP

# Path resolution for SQLite database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "task_routing.db")
if not os.path.exists(DB_PATH):
    DATA_DIR = os.path.join(BASE_DIR, "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    DB_PATH = os.path.join(DATA_DIR, "task_routing.db")

# Initialize FastMCP Server instance on port 5001
mcp = FastMCP("TaskRouting-MCP-Server", host="127.0.0.1", port=5001)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and ensures database schema exists."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gdpr_audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action_type TEXT,
            identifier_hash TEXT,
            status TEXT,
            details TEXT
        )
    ''')

    # Seed initial audit trail if empty
    cursor.execute("SELECT COUNT(*) FROM gdpr_audit_trail")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO gdpr_audit_trail (timestamp, action_type, identifier_hash, status, details)
            VALUES (datetime('now'), 'GDPR_SYSTEM_INIT', 'SYSTEM', 'ACTIVE', 'AIFriday MCP SQLite Server Initialized with Local Privacy Guardrail.')
        ''')
        conn.commit()

    conn.close()

# ------------------ FastMCP Tool Registrations ------------------

@mcp.tool()
def query_tasks(query_str: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """MCP Tool: Queries tasks table from task_routing.db SQLite database."""
    conn = get_connection()
    cursor = conn.cursor()
    if query_str:
        cursor.execute(
            "SELECT * FROM tasks WHERE task_name LIKE ? OR description LIKE ? OR skills_required LIKE ? LIMIT ?",
            (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", limit)
        )
    else:
        cursor.execute("SELECT * FROM tasks ORDER BY task_id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@mcp.tool()
def query_resources(query_str: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """MCP Tool: Queries human resources and AI agents from task_routing.db."""
    conn = get_connection()
    cursor = conn.cursor()
    results = []
    if query_str:
        cursor.execute("SELECT *, 'human' as resource_kind FROM human_resources WHERE name LIKE ? OR skills LIKE ? OR role LIKE ? LIMIT ?",
                       (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", limit))
        results.extend([dict(r) for r in cursor.fetchall()])
        
        cursor.execute("SELECT *, 'ai_agent' as resource_kind FROM ai_agents WHERE agent_name LIKE ? OR capabilities LIKE ? OR specialization LIKE ? LIMIT ?",
                       (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", limit))
        results.extend([dict(r) for r in cursor.fetchall()])
    else:
        cursor.execute("SELECT *, 'human' as resource_kind FROM human_resources LIMIT ?", (limit,))
        results.extend([dict(r) for r in cursor.fetchall()])
        cursor.execute("SELECT *, 'ai_agent' as resource_kind FROM ai_agents LIMIT ?", (limit,))
        results.extend([dict(r) for r in cursor.fetchall()])
    conn.close()
    return results

@mcp.tool()
def search_knowledge_base(pattern: str = "") -> List[Dict[str, Any]]:
    """MCP Tool: Searches knowledge base and document chunks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM knowledge_base 
        WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
    ''', (f"%{pattern}%", f"%{pattern}%", f"%{pattern}%"))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@mcp.tool()
def fetch_policy_playbook(policy_category: str) -> Dict[str, Any]:
    """MCP Tool: Retrieves governance policies and SLA playbooks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policies WHERE policy_type LIKE ? OR title LIKE ?",
                   (f"%{policy_category}%", f"%{policy_category}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

@mcp.tool()
def record_audit_entry(action_type: str, details: str, status: str = "COMPLETED") -> bool:
    """MCP Tool: Logs a GDPR or system governance action in the audit trail."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gdpr_audit_trail (timestamp, action_type, identifier_hash, status, details)
        VALUES (datetime('now'), ?, 'LOGGED', ?, ?)
    ''', (action_type, status, details))
    conn.commit()
    conn.close()
    return True

@mcp.tool()
def purge_data_subject(identifier: str) -> Dict[str, int]:
    """MCP Tool: Performs in-place anonymization for GDPR Right to Erasure (Art. 17)."""
    conn = get_connection()
    cursor = conn.cursor()
    anonymized_tag = "[GDPR_ANONYMIZED]"
    
    cursor.execute('''
        UPDATE tasks SET description = ? WHERE description LIKE ? OR assigned_to LIKE ?
    ''', (anonymized_tag, f"%{identifier}%", f"%{identifier}%"))
    task_count = cursor.rowcount

    cursor.execute('''
        UPDATE human_resources SET email = ? WHERE email LIKE ? OR name LIKE ?
    ''', (anonymized_tag, f"%{identifier}%", f"%{identifier}%"))
    hr_count = cursor.rowcount

    conn.commit()
    conn.close()
    return {"tasks_updated": task_count, "human_resources_updated": hr_count}

@mcp.tool()
def get_gdpr_audit_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """MCP Tool: Retrieves recent GDPR audit trail records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gdpr_audit_trail ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("==================================================================")
    print("AIFriday Standalone MCP SQLite Server starting...")
    print("• Transport: SSE (Server-Sent Events)")
    print("• Server Endpoint: http://127.0.0.1:5001/sse")
    print("• SQLite Database: ", DB_PATH)
    print("==================================================================")
    mcp.run(transport="sse")
