"""
Authentication and Authorization Module
Handles password hashing, session management, and RBAC
"""

import bcrypt
import sqlite3
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g, redirect, url_for
import json

# Password Management

def hash_password(password):
    """Hash password using bcrypt with salt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def generate_secure_token():
    """Generate secure UUID4 token for sessions"""
    return str(uuid.uuid4())

def validate_password_strength(password):
    """Validate password meets minimum requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_number = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    if not has_number:
        return False, "Password must contain at least one number"
    if not has_special:
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

# Session Handling

def create_session(user_id, request_obj):
    """Create new session for user"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    token = generate_secure_token()
    ip_address = request_obj.remote_addr
    user_agent = request_obj.headers.get('User-Agent', '')
    expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
    
    cursor.execute('''
        INSERT INTO sessions (user_id, token, ip_address, user_agent, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, token, ip_address, user_agent, expires_at))
    
    conn.commit()
    conn.close()
    
    return token

def validate_session(token):
    """Validate session token and check expiry"""
    if not token:
        return None
    
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, u.id, u.username, u.email, u.role, u.phone, u.is_active, u.profile_data
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND s.is_active = 1
    ''', (token,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # Check expiry
    expires_at = datetime.fromisoformat(row[5])
    if datetime.now() > expires_at:
        destroy_session(token)
        return None
    
    # Check if user is active
    if not row[12]:
        return None
    
    # Return user and session data
    return {
        'session': {
            'id': row[0],
            'user_id': row[1],
            'token': row[2],
            'ip_address': row[3],
            'user_agent': row[4],
            'created_at': row[6],
            'expires_at': row[5]
        },
        'user': {
            'id': row[8],
            'username': row[9],
            'email': row[10],
            'role': row[11],
            'phone': row[12],
            'is_active': row[13],
            'profile_data': json.loads(row[14]) if row[14] else {}
        }
    }

def destroy_session(token):
    """Destroy session by token"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE sessions SET is_active = 0 WHERE token = ?', (token,))
    
    conn.commit()
    conn.close()

def get_current_user(request_obj):
    """Get current user from request (middleware helper)"""
    token = request_obj.cookies.get('session_token') or request_obj.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return None
    
    session_data = validate_session(token)
    return session_data['user'] if session_data else None

def extend_session(token):
    """Extend session expiry by 1 hour"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    new_expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    
    cursor.execute('''
        UPDATE sessions 
        SET expires_at = ? 
        WHERE token = ? AND is_active = 1
    ''', (new_expires_at, token))
    
    conn.commit()
    conn.close()
    
    return new_expires_at

# Role-Based Access Control

def require_role(*allowed_roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'user', None)
            
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if user['role'] not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_permission(user, resource_type, action):
    """Check if user has permission for specific resource action"""
    if not user:
        return False
    
    role = user.get('role')
    
    # Operator permissions
    if role == 'operator':
        operator_permissions = {
            'violation': ['read', 'update', 'delete'],
            'signal': ['read', 'update', 'override'],
            'intersection': ['read', 'update'],
            'appeal': ['read', 'approve', 'reject'],
            'fine': ['read', 'issue'],
            'user': ['read']
        }
        
        allowed_actions = operator_permissions.get(resource_type, [])
        return action in allowed_actions
    
    # Citizen permissions
    elif role == 'citizen':
        citizen_permissions = {
            'violation': ['read_own'],
            'appeal': ['read_own', 'create'],
            'fine': ['read_own', 'pay'],
            'wallet': ['read_own', 'credit']
        }
        
        allowed_actions = citizen_permissions.get(resource_type, [])
        return action in allowed_actions
    
    return False

# User Management Helpers

def get_user_by_username(username):
    """Get user by username"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, password_hash, email, role, phone, created_at, is_active, profile_data
        FROM users
        WHERE username = ?
    ''', (username,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        'id': row[0],
        'username': row[1],
        'password_hash': row[2],
        'email': row[3],
        'role': row[4],
        'phone': row[5],
        'created_at': row[6],
        'is_active': row[7],
        'profile_data': json.loads(row[8]) if row[8] else {}
    }

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, email, role, phone, created_at, is_active, profile_data
        FROM users
        WHERE id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        'id': row[0],
        'username': row[1],
        'email': row[2],
        'role': row[3],
        'phone': row[4],
        'created_at': row[5],
        'is_active': row[6],
        'profile_data': json.loads(row[7]) if row[7] else {}
    }

def create_user(username, password, email, role, phone=None, profile_data=None):
    """Create new user"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    profile_json = json.dumps(profile_data) if profile_data else None
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, role, phone, profile_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, email, role, phone, profile_json))
        
        user_id = cursor.lastrowid
        
        # Create wallet for citizen users
        if role == 'citizen':
            cursor.execute('''
                INSERT INTO wallet (user_id, balance, total_paid, total_credits)
                VALUES (?, 0.0, 0.0, 0.0)
            ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return user_id
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"User creation failed: {e}")

def log_audit(user_id, action, resource_type, resource_id, old_value=None, new_value=None, ip_address=None):
    """Log audit trail entry"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    old_value_json = json.dumps(old_value) if old_value else None
    new_value_json = json.dumps(new_value) if new_value else None
    
    cursor.execute('''
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, old_value, new_value, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, action, resource_type, resource_id, old_value_json, new_value_json, ip_address))
    
    conn.commit()
    conn.close()
