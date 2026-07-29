import os
import sqlite3
import json
import httpx
from typing import List, Dict, Any

class MCPSqliteServer:
    """
    Client Interface & Service Wrapper for the Standalone AIFriday MCP Server.
    Connects to the standalone MCP server running on http://127.0.0.1:5001
    and provides local SQLite query fallbacks for multi-agent orchestrator workers.
    """

    def __init__(self, standalone_url: str = "http://127.0.0.1:5001", db_path: str = None):
        self.standalone_url = standalone_url.rstrip('/')
        if not db_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            default_db = os.path.join(base_dir, "task_routing.db")
            if os.path.exists(default_db):
                self.db_path = default_db
            else:
                db_dir = os.path.join(base_dir, "data")
                os.makedirs(db_dir, exist_ok=True)
                self.db_path = os.path.join(db_dir, "task_routing.db")
        else:
            self.db_path = db_path

        self._init_db()

    def is_standalone_online(self) -> bool:
        """Checks if the standalone MCP server process is active on port 5001."""
        try:
            with httpx.Client(timeout=1.0) as client:
                req = client.build_request("GET", f"{self.standalone_url}/sse")
                resp = client.send(req, stream=True)
                return resp.status_code == 200
        except Exception:
            return False

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Ensures local SQLite audit trail table exists."""
        conn = self._get_connection()
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
        conn.commit()
        conn.close()

    def query_tasks(self, query_str: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Queries tasks table from task_routing.db SQLite database."""
        conn = self._get_connection()
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

    def query_resources(self, query_str: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Queries human resources and AI agents from task_routing.db."""
        conn = self._get_connection()
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

    def search_knowledge_base(self, pattern: str = "") -> List[Dict[str, Any]]:
        """Searches knowledge base and document chunks."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM knowledge_base 
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
        ''', (f"%{pattern}%", f"%{pattern}%", f"%{pattern}%"))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def record_audit_entry(self, action_type: str, details: str, status: str = "COMPLETED") -> bool:
        """Logs a GDPR compliance action in the audit trail."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO gdpr_audit_trail (timestamp, action_type, identifier_hash, status, details)
            VALUES (datetime('now'), ?, 'LOGGED', ?, ?)
        ''', (action_type, status, details))
        conn.commit()
        conn.close()
        return True

    def get_gdpr_audit_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent GDPR audit trail records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gdpr_audit_trail ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

# Alias for backwards compatibility
MCPSqliteClient = MCPSqliteServer
