"""
Authentication blueprint for JWT-based authentication
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import bcrypt
from database import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password required"}), 400
        
        # Get user from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
        # Create access token
        access_token = create_access_token(
            identity=username,
            additional_claims={"role": user['role']}
        )
        
        return jsonify({
            "success": True,
            "access_token": access_token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@auth_bp.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify():
    """
    Verify JWT token and return current user
    """
    try:
        current_user = get_jwt_identity()
        
        # Get user details from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE username = ?", (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user (admin only in production)
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password required"}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert user into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "id": user_id,
                    "username": username,
                    "role": role
                }
            }), 201
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": False, "error": "Username already exists"}), 409
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
