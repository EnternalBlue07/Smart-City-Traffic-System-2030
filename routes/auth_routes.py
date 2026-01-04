"""
Authentication Routes
Handles login, logout, registration, and session management endpoints
"""

from flask import Blueprint, request, jsonify, render_template, make_response, redirect, url_for
from auth import (
    create_session, destroy_session, validate_session, extend_session,
    verify_password, get_user_by_username, create_user,
    validate_password_strength, log_audit
)
import re

bp = Blueprint('auth_routes', __name__)

@bp.route('/login')
def login_page():
    """Render login page"""
    portal = request.args.get('portal', 'citizen')
    
    # If already authenticated, redirect to appropriate portal
    token = request.cookies.get('session_token')
    if token:
        session_data = validate_session(token)
        if session_data:
            user = session_data['user']
            if user['role'] == 'operator':
                return redirect('/operator/dashboard')
            else:
                return redirect('/citizen/dashboard')
    
    return render_template('login.html', portal=portal)

@bp.route('/auth/login', methods=['POST'])
def login():
    """Handle login request"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    username = data.get('username')
    password = data.get('password')
    portal = data.get('portal', 'citizen')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Get user from database
    user = get_user_by_username(username)
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Verify password
    if not verify_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if user is active
    if not user['is_active']:
        return jsonify({'error': 'Account is inactive'}), 401
    
    # Verify role matches portal
    if user['role'] != portal:
        return jsonify({'error': f'Invalid portal for this account. Please use the {user["role"]} portal.'}), 403
    
    # Create session
    token = create_session(user['id'], request)
    
    # Log audit
    log_audit(user['id'], 'login', 'session', None, None, None, request.remote_addr)
    
    # Determine redirect URL based on role
    if user['role'] == 'operator':
        redirect_url = '/operator/dashboard'
    else:
        redirect_url = '/citizen/dashboard'
    
    response = make_response(jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'email': user['email']
        },
        'redirect_url': redirect_url
    }))
    
    # Set httponly cookie
    response.set_cookie(
        'session_token',
        token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite='Lax',
        max_age=86400  # 24 hours
    )
    
    return response

@bp.route('/auth/logout', methods=['POST'])
def logout():
    """Handle logout request"""
    token = request.cookies.get('session_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if token:
        session_data = validate_session(token)
        if session_data:
            # Log audit
            log_audit(session_data['user']['id'], 'logout', 'session', None, None, None, request.remote_addr)
        
        destroy_session(token)
    
    response = make_response(jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }))
    
    # Clear cookie
    response.set_cookie('session_token', '', expires=0)
    
    return response

@bp.route('/auth/register', methods=['POST'])
def register():
    """Handle user registration (citizens only initially)"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    full_name = data.get('full_name')
    
    # Validate required fields
    if not all([username, email, password]):
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    # Validate username format (alphanumeric and underscore only)
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({'error': 'Username must be 3-20 characters, alphanumeric and underscore only'}), 400
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength
    is_strong, message = validate_password_strength(password)
    if not is_strong:
        return jsonify({'error': message}), 400
    
    # Validate phone if provided
    if phone and not re.match(r'^\+?[0-9]{10,15}$', phone):
        return jsonify({'error': 'Invalid phone number format'}), 400
    
    # Create user
    try:
        profile_data = {
            'full_name': full_name
        }
        
        user_id = create_user(
            username=username,
            password=password,
            email=email,
            role='citizen',
            phone=phone,
            profile_data=profile_data
        )
        
        # Log audit
        log_audit(user_id, 'register', 'user', user_id, None, None, request.remote_addr)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Registration successful. Please login.'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@bp.route('/auth/me')
def get_current_user():
    """Get current user information"""
    token = request.cookies.get('session_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    session_data = validate_session(token)
    
    if not session_data:
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    user = session_data['user']
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'phone': user['phone'],
        'profile_data': user['profile_data'],
        'is_active': user['is_active']
    })

@bp.route('/auth/refresh', methods=['POST'])
def refresh_session():
    """Refresh session expiry"""
    token = request.cookies.get('session_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    session_data = validate_session(token)
    
    if not session_data:
        return jsonify({'error': 'Invalid or expired session'}), 401
    
    # Extend session
    new_expires_at = extend_session(token)
    
    return jsonify({
        'success': True,
        'token': token,
        'expires_at': new_expires_at
    })
