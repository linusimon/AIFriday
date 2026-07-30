import os
import sqlite3
import json
import httpx
from typing import List, Dict, Any, Optional

class MCPSqliteClient:
    """
    Client Interface & Service Gateway for the Standalone Generic SQLite MCP Server.
    Communicates with the standalone MCP server running on http://127.0.0.1:5001
    or executes through the generic SQLite execution layer for multi-agent workers.
    """

    def __init__(self, standalone_url: str = "http://127.0.0.1:5001", db_path: str = None):
        self.standalone_url = standalone_url.rstrip('/')
        if not db_path:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            default_db = os.environ.get("SQLITE_DB_PATH", os.path.join(base_dir, "task_routing.db"))
            if not os.path.exists(default_db):
                db_dir = os.path.join(base_dir, "data")
                os.makedirs(db_dir, exist_ok=True)
                self.db_path = os.path.join(db_dir, "task_routing.db")
            else:
                self.db_path = default_db
        else:
            self.db_path = db_path

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

    # ---------------- Generic SQLite Operations ----------------

    def execute_query(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Executes a SELECT query via the SQLite MCP server execution layer."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or [])
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def execute_statement(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Executes an INSERT, UPDATE, DELETE, or DDL statement via the SQLite MCP server execution layer."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or [])
            conn.commit()
            return {
                "status": "success",
                "rows_affected": cursor.rowcount,
                "last_row_id": cursor.lastrowid
            }
        except Exception as e:
            conn.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()

    def execute_batch(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executes a list of SQL statements in a single transaction block."""
        conn = self._get_connection()
        cursor = conn.cursor()
        executed_count = 0
        try:
            for stmt in statements:
                sql = stmt.get('sql')
                params = stmt.get('params', [])
                if sql:
                    cursor.execute(sql, params)
                    executed_count += 1
            conn.commit()
            return {"status": "success", "executed_count": executed_count}
        except Exception as e:
            conn.rollback()
            return {"status": "error", "error": str(e), "executed_before_failure": executed_count}
        finally:
            conn.close()

    def list_tables(self) -> List[str]:
        """Lists user tables in the SQLite database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row['name'] for row in cursor.fetchall()]
        finally:
            conn.close()

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Describes schema columns for a given table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    # ---------------- Application Domain Helpers ----------------

    def query_tasks(self, query_str: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Queries tasks table from SQLite database using generic execute_query."""
        if query_str:
            return self.execute_query(
                "SELECT * FROM tasks WHERE task_name LIKE ? OR description LIKE ? OR skills_required LIKE ? LIMIT ?",
                [f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", limit]
            )
        return self.execute_query("SELECT * FROM tasks ORDER BY task_id DESC LIMIT ?", [limit])

    def query_resources(self, query_str: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Queries human resources and AI agents from database using generic execute_query."""
        results = []
        if query_str:
            human = self.execute_query(
                "SELECT *, 'human' as resource_kind FROM human_resources WHERE name LIKE ? OR skills LIKE ? OR role LIKE ? LIMIT ?",
                [f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", limit]
            )
            results.extend(human)
            ai = self.execute_query(
                "SELECT *, 'ai_agent' as resource_kind FROM ai_agents WHERE agent_name LIKE ? OR capabilities LIKE ? OR specialization LIKE ? LIMIT ?",
                [f"%{query_str}%", f"%{query_str}%", f"%{query_str}%", limit]
            )
            results.extend(ai)
        else:
            human = self.execute_query("SELECT *, 'human' as resource_kind FROM human_resources LIMIT ?", [limit])
            results.extend(human)
            ai = self.execute_query("SELECT *, 'ai_agent' as resource_kind FROM ai_agents LIMIT ?", [limit])
            results.extend(ai)
        return results

    def search_knowledge_base(self, pattern: str = "") -> List[Dict[str, Any]]:
        """Searches knowledge base and document chunks using generic execute_query."""
        return self.execute_query(
            "SELECT * FROM knowledge_base WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?",
            [f"%{pattern}%", f"%{pattern}%", f"%{pattern}%"]
        )

    def record_audit_entry(self, action_type: str, details: str, status: str = "COMPLETED") -> bool:
        """Logs a GDPR compliance action using generic execute_statement."""
        res = self.execute_statement(
            "INSERT INTO gdpr_audit_trail (timestamp, action_type, identifier_hash, status, details) VALUES (datetime('now'), ?, 'LOGGED', ?, ?)",
            [action_type, status, details]
        )
        return res.get("status") == "success"

    def get_gdpr_audit_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent GDPR audit trail records using generic execute_query."""
        return self.execute_query("SELECT * FROM gdpr_audit_trail ORDER BY id DESC LIMIT ?", [limit])

# Aliases for backwards compatibility
MCPSqliteServer = MCPSqliteClient
