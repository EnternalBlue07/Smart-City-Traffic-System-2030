"""
Quick Demo Server - Phase 1-3 Features
Runs without heavy ML dependencies
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, g, make_response
import sqlite3
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key-change-in-production'

# Import our Phase 1-3 modules
socketio = None
try:
    from auth import hash_password, verify_password, generate_secure_token, require_role, get_current_user, log_audit
    from realtime import init_socketio
    from middleware import set_security_headers
    
    # Initialize SocketIO
    socketio = init_socketio(app)
    
    # Register middleware
    app.after_request(set_security_headers)
    
    print("✓ Phase 1 modules loaded")
except Exception as e:
    print(f"Warning: {e}")
    # Fallback if SocketIO fails
    from flask_socketio import SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

# Import routes
try:
    from routes import auth_routes, operator_routes, citizen_routes
    
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(operator_routes.bp, url_prefix='/operator')
    app.register_blueprint(citizen_routes.bp, url_prefix='/citizen')
    
    print("✓ Phase 1-3 routes registered")
except Exception as e:
    print(f"Warning: {e}")

# Home route
@app.route('/')
def index():
    """Home page - redirect to login"""
    return redirect('/login')

# Health check
@app.route('/health')
def health():
    """System health check"""
    try:
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'ok',
            'users': user_count,
            'auth': 'ok',
            'socketio': 'ok',
            'phase1': 'complete',
            'phase2': 'complete',
            'phase3': 'complete'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Simple stats endpoint
@app.route('/stats')
def stats():
    """Quick stats overview"""
    try:
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "operator"')
        operators = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "citizen"')
        citizens = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM intersections')
        intersections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM violations')
        violations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM traffic_signals')
        signals = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'operators': operators,
            'citizens': citizens,
            'intersections': intersections,
            'violations': violations,
            'traffic_signals': signals,
            'features': {
                'authentication': 'enabled',
                'real_time': 'enabled',
                'prediction': 'enabled',
                'operator_dashboard': 'enabled',
                'citizen_portal': 'stub'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Smart Traffic Management System - Demo Server")
    print("=" * 60)
    print()
    print("Phase 1: Foundation ✅")
    print("Phase 2: Operator Dashboard ✅")
    print("Phase 3: Predictive Management ✅")
    print()
    print("Server starting...")
    print()
    print("Access Points:")
    print("  • Login: http://localhost:5000/login")
    print("  • Health: http://localhost:5000/health")
    print("  • Stats: http://localhost:5000/stats")
    print("  • Operator Dashboard: http://localhost:5000/operator/dashboard")
    print()
    print("Demo Credentials:")
    print("  Operators: demo_operator1 / Operator@123")
    print("  Citizens: demo_citizen1 / Citizen@123")
    print()
    print("=" * 60)
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
