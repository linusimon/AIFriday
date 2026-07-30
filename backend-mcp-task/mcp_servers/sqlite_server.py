"""
AIFriday Intelligent Task Routing - Standalone Generic SQLite Model Context Protocol (MCP) Server

An independent, reusable MCP server for executing SQLite database operations.
Provides generic tools for connecting, running SELECT queries, executing INSERT/UPDATE/DELETE
statements, running transaction batches, and inspecting schemas for ANY SQLite database.
"""

import os
import sys
import sqlite3
import json
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

# Path resolution for target SQLite database (configurable via environment variable)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(BASE_DIR, "task_routing.db"))

if not os.path.isabs(DEFAULT_DB_PATH):
    DEFAULT_DB_PATH = os.path.join(BASE_DIR, DEFAULT_DB_PATH)

# Ensure database directory exists
os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)

# Initialize FastMCP Server instance on port 5001
mcp = FastMCP("Generic-SQLite-MCP-Server", host="127.0.0.1", port=5001)

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Helper to open a connection to the specified or default SQLite database."""
    target_path = db_path if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ Generic FastMCP Tool Registrations ------------------

@mcp.tool()
def execute_query(sql: str, params: Optional[List[Any]] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generic MCP Tool: Executes a read-only SQL query (SELECT) against the SQLite database and returns rows.
    
    Args:
        sql: Parameterized SQL query string (e.g. "SELECT * FROM tasks WHERE status = ?")
        params: Optional list of query positional parameter values
        db_path: Optional custom path to SQLite database file
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or [])
        rows = [dict(r) for r in cursor.fetchall()]
        return rows
    finally:
        conn.close()

@mcp.tool()
def execute_statement(sql: str, params: Optional[List[Any]] = None, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generic MCP Tool: Executes a write/modification SQL statement (INSERT, UPDATE, DELETE, DDL) and commits transaction.
    
    Args:
        sql: Parameterized SQL statement string
        params: Optional list of statement parameter values
        db_path: Optional custom path to SQLite database file
    """
    conn = get_db_connection(db_path)
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
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        conn.close()

@mcp.tool()
def execute_batch(statements: List[Dict[str, Any]], db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generic MCP Tool: Executes a list of SQL statements within a single transaction block.
    
    Args:
        statements: List of dicts, each with 'sql' string and optional 'params' list.
        db_path: Optional custom path to SQLite database file.
    """
    conn = get_db_connection(db_path)
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
        return {
            "status": "success",
            "executed_count": executed_count
        }
    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "error": str(e),
            "executed_before_failure": executed_count
        }
    finally:
        conn.close()

@mcp.tool()
def list_tables(db_path: Optional[str] = None) -> List[str]:
    """
    Generic MCP Tool: Lists all user tables present in the target SQLite database.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row['name'] for row in cursor.fetchall()]
        return tables
    finally:
        conn.close()

@mcp.tool()
def describe_table(table_name: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generic MCP Tool: Returns schema column details for a given table in the database.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [dict(r) for r in cursor.fetchall()]
        return columns
    finally:
        conn.close()

if __name__ == "__main__":
    print("==================================================================")
    print("AIFriday Standalone Generic SQLite MCP Server starting...")
    print("• Transport: SSE (Server-Sent Events)")
    print("• Server Endpoint: http://127.0.0.1:5001/sse")
    print("• Target SQLite Database: ", DEFAULT_DB_PATH)
    print("==================================================================")
    mcp.run(transport="sse")
