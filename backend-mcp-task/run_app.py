"""
AIFriday Task Routing - Unified Application Launcher
Launches the Standalone FastMCP SQLite Server process on port 5001,
and Flask backend server on port 5004.
"""

import os
import sys
import time
import subprocess
import threading

def start_mcp_server():
    """Starts the standalone FastMCP SQLite Server process on port 5001."""
    python_exe = sys.executable
    mcp_script = os.path.join(os.path.dirname(__file__), "mcp_servers", "sqlite_server.py")
    subprocess.Popen([python_exe, mcp_script])

def main():
    # Ensure working directory is backend-mcp-task root
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)

    print("==================================================================")
    print("[AIFriday] Starting Intelligent Task Routing Platform...")
    print("==================================================================")
    print("• Standalone MCP SQLite Server: http://127.0.0.1:5001/sse")
    print("• Backend API Server:          http://localhost:5004/api")
    print("==================================================================")

    # Prevent duplicate subprocess spawns during Flask debug hot-reloads
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # 1. Start Standalone MCP Server Process once
        threading.Thread(target=start_mcp_server, daemon=True).start()
        time.sleep(1.0)

    # 2. Import and run Flask app on port 5004
    from app import app
    app.run(host="0.0.0.0", port=5004, debug=True)

if __name__ == "__main__":
    main()
