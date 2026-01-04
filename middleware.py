"""
Middleware Module
Request/response pipeline, authentication checks, and security headers
"""

from flask import request, g, redirect, url_for, jsonify, render_template
from auth import validate_session
from functools import wraps

# Public routes that don't require authentication
PUBLIC_ROUTES = [
    '/login',
    '/auth/login',
    '/auth/register',
    '/health',
    '/static',
    '/_debug_toolbar'
]

def init_middleware(app):
    """Initialize middleware for the Flask app"""
    
    @app.before_request
    def check_authentication():
        """Validate session token before each request"""
        # Skip authentication for public routes
        if any(request.path.startswith(route) for route in PUBLIC_ROUTES):
            return None
        
        # Skip for static files
        if request.path.startswith('/static/'):
            return None
        
        # Get session token from cookies or headers
        token = request.cookies.get('session_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            # For API requests, return JSON error
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            # For page requests, redirect to login
            return redirect(url_for('auth_routes.login_page'))
        
        # Validate session
        session_data = validate_session(token)
        
        if not session_data:
            # Invalid or expired session
            if request.path.startswith('/api/') or request.is_json:
                return jsonify({'error': 'Session expired or invalid'}), 401
            return redirect(url_for('auth_routes.login_page'))
        
        # Store user and session in g for use in request handlers
        g.user = session_data['user']
        g.session = session_data['session']
        g.token = token
        
        return None
    
    @app.after_request
    def set_security_headers(response):
        """Set security headers on all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Don't cache authenticated pages
        if hasattr(g, 'user'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            }), 401
        
        return redirect(url_for('auth_routes.login_page', next=request.url))
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Insufficient permissions'
            }), 403
        
        return render_template('error.html', 
                             error_code=403,
                             error_title='Access Denied',
                             error_message='You do not have permission to access this resource.'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found'
            }), 404
        
        return render_template('error.html',
                             error_code=404,
                             error_title='Page Not Found',
                             error_message='The page you are looking for does not exist.'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 Internal Server Error"""
        # Log error (in production, use proper logging)
        print(f"Server error: {error}")
        
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }), 500
        
        return render_template('error.html',
                             error_code=500,
                             error_title='Server Error',
                             error_message='An unexpected error occurred. Please try again later.'), 500
    
    print("✓ Middleware initialized")

def require_auth(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user'):
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth_routes.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def optional_auth(f):
    """Decorator for routes that work with or without authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # User will be in g.user if authenticated, None otherwise
        return f(*args, **kwargs)
    return decorated_function
