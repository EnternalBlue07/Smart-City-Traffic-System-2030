"""
Operator Routes
Phase 2: Operator Dashboard & Network Visualization
"""

from flask import Blueprint, jsonify, render_template, g, request
from auth import require_role, log_audit
import sqlite3
from datetime import datetime, timedelta
import json

bp = Blueprint('operator_routes', __name__)

def get_db():
    """Get database connection"""
    return sqlite3.connect('database/violations.db')

@bp.route('/dashboard')
@require_role('operator')
def dashboard():
    """Operator dashboard - main control interface"""
    return render_template('operator_dashboard.html', user=g.user)

@bp.route('/api/overview')
@require_role('operator')
def get_overview():
    """Get system overview statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Active intersections
    cursor.execute('SELECT COUNT(*) FROM intersections WHERE status = "active"')
    active_intersections = cursor.fetchone()[0]
    
    # Total intersections
    cursor.execute('SELECT COUNT(*) FROM intersections')
    total_intersections = cursor.fetchone()[0]
    
    # Violations today
    cursor.execute('''
        SELECT COUNT(*) FROM violations 
        WHERE DATE(timestamp) = DATE('now')
    ''')
    violations_today = cursor.fetchone()[0]
    
    # Pending appeals
    cursor.execute('SELECT COUNT(*) FROM appeals WHERE status = "pending"')
    pending_appeals = cursor.fetchone()[0]
    
    # Active signals (green)
    cursor.execute('SELECT COUNT(*) FROM traffic_signals WHERE current_state = "green"')
    active_signals = cursor.fetchone()[0]
    
    # Recent violations (last 10)
    cursor.execute('''
        SELECT v.id, v.vehicle_type, v.license_plate, v.violation_type, 
               v.timestamp, v.location, v.camera_id, i.name as intersection_name
        FROM violations v
        LEFT JOIN intersections i ON v.intersection_id = i.id
        ORDER BY v.timestamp DESC
        LIMIT 10
    ''')
    recent_violations = [
        {
            'id': row[0],
            'vehicle_type': row[1],
            'license_plate': row[2],
            'violation_type': row[3],
            'timestamp': row[4],
            'location': row[5],
            'camera_id': row[6],
            'intersection_name': row[7]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'active_intersections': active_intersections,
        'total_intersections': total_intersections,
        'violations_today': violations_today,
        'pending_appeals': pending_appeals,
        'active_signals': active_signals,
        'recent_violations': recent_violations,
        'timestamp': datetime.now().isoformat()
    })

@bp.route('/api/intersections')
@require_role('operator')
def list_intersections():
    """List all intersections with their current status"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT i.id, i.name, i.location, i.mode, i.status, i.ns_cycle, i.ew_cycle,
               i.created_at, i.updated_at,
               (SELECT COUNT(*) FROM violations WHERE intersection_id = i.id) as violation_count
        FROM intersections i
        ORDER BY i.name
    ''')
    
    intersections = [
        {
            'id': row[0],
            'name': row[1],
            'location': row[2],
            'lat': float(row[2].split(',')[0]) if row[2] else None,
            'lon': float(row[2].split(',')[1]) if row[2] else None,
            'mode': row[3],
            'status': row[4],
            'ns_cycle': row[5],
            'ew_cycle': row[6],
            'created_at': row[7],
            'updated_at': row[8],
            'violation_count': row[9]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'intersections': intersections,
        'count': len(intersections)
    })

@bp.route('/api/intersections/<int:intersection_id>')
@require_role('operator')
def get_intersection_details(intersection_id):
    """Get detailed information about a specific intersection"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get intersection details
    cursor.execute('''
        SELECT id, name, location, mode, status, ns_cycle, ew_cycle, created_at, updated_at
        FROM intersections
        WHERE id = ?
    ''', (intersection_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Intersection not found'}), 404
    
    intersection = {
        'id': row[0],
        'name': row[1],
        'location': row[2],
        'mode': row[3],
        'status': row[4],
        'ns_cycle': row[5],
        'ew_cycle': row[6],
        'created_at': row[7],
        'updated_at': row[8]
    }
    
    # Get traffic signals
    cursor.execute('''
        SELECT id, direction, current_state, remaining_seconds, total_cycle_time,
               last_override_by, last_override_at, predictive_mode
        FROM traffic_signals
        WHERE intersection_id = ?
    ''', (intersection_id,))
    
    signals = [
        {
            'id': row[0],
            'direction': row[1],
            'current_state': row[2],
            'remaining_seconds': row[3],
            'total_cycle_time': row[4],
            'last_override_by': row[5],
            'last_override_at': row[6],
            'predictive_mode': bool(row[7])
        }
        for row in cursor.fetchall()
    ]
    
    # Get recent violations
    cursor.execute('''
        SELECT id, vehicle_type, license_plate, violation_type, timestamp, camera_id
        FROM violations
        WHERE intersection_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    ''', (intersection_id,))
    
    violations = [
        {
            'id': row[0],
            'vehicle_type': row[1],
            'license_plate': row[2],
            'violation_type': row[3],
            'timestamp': row[4],
            'camera_id': row[5]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'intersection': intersection,
        'signals': signals,
        'recent_violations': violations
    })

@bp.route('/api/signals')
@require_role('operator')
def get_all_signals():
    """Get all traffic signals across the network"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ts.id, ts.intersection_id, i.name, ts.direction, ts.current_state,
               ts.remaining_seconds, ts.total_cycle_time, ts.predictive_mode
        FROM traffic_signals ts
        JOIN intersections i ON ts.intersection_id = i.id
        ORDER BY i.name, ts.direction
    ''')
    
    signals = [
        {
            'id': row[0],
            'intersection_id': row[1],
            'intersection_name': row[2],
            'direction': row[3],
            'current_state': row[4],
            'remaining_seconds': row[5],
            'total_cycle_time': row[6],
            'predictive_mode': bool(row[7])
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'signals': signals,
        'count': len(signals)
    })

@bp.route('/api/signals/<int:signal_id>/override', methods=['POST'])
@require_role('operator')
def override_signal(signal_id):
    """Override signal state manually"""
    data = request.get_json()
    new_state = data.get('state')  # 'green', 'red', 'amber'
    duration = data.get('duration', 60)  # seconds
    
    if new_state not in ['green', 'red', 'amber']:
        return jsonify({'error': 'Invalid state'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get signal details
    cursor.execute('''
        SELECT ts.intersection_id, ts.direction, i.name
        FROM traffic_signals ts
        JOIN intersections i ON ts.intersection_id = i.id
        WHERE ts.id = ?
    ''', (signal_id,))
    
    signal_info = cursor.fetchone()
    if not signal_info:
        conn.close()
        return jsonify({'error': 'Signal not found'}), 404
    
    intersection_id, direction, intersection_name = signal_info
    
    # Update signal state
    cursor.execute('''
        UPDATE traffic_signals
        SET current_state = ?,
            remaining_seconds = ?,
            last_override_by = ?,
            last_override_at = ?
        WHERE id = ?
    ''', (new_state, duration, g.user['id'], datetime.now().isoformat(), signal_id))
    
    # Log audit trail
    log_audit(
        user_id=g.user['id'],
        action='override_signal',
        resource_type='signal',
        resource_id=signal_id,
        old_value=None,
        new_value={'state': new_state, 'duration': duration},
        ip_address=request.remote_addr
    )
    
    conn.commit()
    conn.close()
    
    # Broadcast via SocketIO
    try:
        from realtime import broadcast_override_applied
        broadcast_override_applied(intersection_id, direction, new_state, g.user['id'])
    except Exception as e:
        print(f"SocketIO broadcast error: {e}")
    
    return jsonify({
        'success': True,
        'message': f'Signal overridden to {new_state} for {duration} seconds',
        'intersection': intersection_name,
        'direction': direction
    })

@bp.route('/api/signals/<int:signal_id>/auto', methods=['POST'])
@require_role('operator')
def set_signal_auto(signal_id):
    """Return signal to automatic mode"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Reset override
    cursor.execute('''
        UPDATE traffic_signals
        SET last_override_by = NULL,
            last_override_at = NULL
        WHERE id = ?
    ''', (signal_id,))
    
    # Log audit trail
    log_audit(
        user_id=g.user['id'],
        action='reset_signal_auto',
        resource_type='signal',
        resource_id=signal_id,
        old_value=None,
        new_value={'mode': 'auto'},
        ip_address=request.remote_addr
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Signal returned to automatic mode'
    })

@bp.route('/api/intersections/<int:intersection_id>/mode', methods=['POST'])
@require_role('operator')
def set_intersection_mode(intersection_id):
    """Set intersection mode (auto/manual)"""
    data = request.get_json()
    mode = data.get('mode')
    
    if mode not in ['auto', 'manual']:
        return jsonify({'error': 'Invalid mode'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE intersections
        SET mode = ?,
            updated_at = ?
        WHERE id = ?
    ''', (mode, datetime.now().isoformat(), intersection_id))
    
    # Log audit trail
    log_audit(
        user_id=g.user['id'],
        action='set_intersection_mode',
        resource_type='intersection',
        resource_id=intersection_id,
        old_value=None,
        new_value={'mode': mode},
        ip_address=request.remote_addr
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Intersection mode set to {mode}'
    })

@bp.route('/api/intersections/<int:intersection_id>/emergency', methods=['POST'])
@require_role('operator')
def emergency_preempt(intersection_id):
    """Emergency preemption - clear all signals for emergency vehicle"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get intersection name
    cursor.execute('SELECT name FROM intersections WHERE id = ?', (intersection_id,))
    intersection = cursor.fetchone()
    
    if not intersection:
        conn.close()
        return jsonify({'error': 'Intersection not found'}), 404
    
    # Set all signals to red
    cursor.execute('''
        UPDATE traffic_signals
        SET current_state = 'red',
            remaining_seconds = 120,
            last_override_by = ?,
            last_override_at = ?
        WHERE intersection_id = ?
    ''', (g.user['id'], datetime.now().isoformat(), intersection_id))
    
    # Log audit trail
    log_audit(
        user_id=g.user['id'],
        action='emergency_preempt',
        resource_type='intersection',
        resource_id=intersection_id,
        old_value=None,
        new_value={'action': 'emergency_preempt'},
        ip_address=request.remote_addr
    )
    
    conn.commit()
    conn.close()
    
    # Broadcast via SocketIO
    try:
        from realtime import broadcast_emergency_preempt
        broadcast_emergency_preempt(intersection_id, g.user['id'])
    except Exception as e:
        print(f"SocketIO broadcast error: {e}")
    
    return jsonify({
        'success': True,
        'message': f'Emergency preemption activated at {intersection[0]}'
    })

@bp.route('/api/violations/recent')
@require_role('operator')
def get_recent_violations():
    """Get recent violations for live feed"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.id, v.vehicle_type, v.license_plate, v.violation_type,
               v.timestamp, v.location, v.camera_id, v.fine_amount,
               i.name as intersection_name, v.status
        FROM violations v
        LEFT JOIN intersections i ON v.intersection_id = i.id
        ORDER BY v.timestamp DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    violations = [
        {
            'id': row[0],
            'vehicle_type': row[1],
            'license_plate': row[2],
            'violation_type': row[3],
            'timestamp': row[4],
            'location': row[5],
            'camera_id': row[6],
            'fine_amount': row[7],
            'intersection_name': row[8],
            'status': row[9]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'violations': violations,
        'count': len(violations)
    })

@bp.route('/api/analytics/hourly')
@require_role('operator')
def get_hourly_analytics():
    """Get hourly violation statistics for charts"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Last 24 hours
    cursor.execute('''
        SELECT 
            strftime('%H:00', timestamp) as hour,
            COUNT(*) as count
        FROM violations
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour
        ORDER BY hour
    ''')
    
    hourly_data = [
        {'hour': row[0], 'count': row[1]}
        for row in cursor.fetchall()
    ]
    
    # By violation type
    cursor.execute('''
        SELECT violation_type, COUNT(*) as count
        FROM violations
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY violation_type
        ORDER BY count DESC
    ''')
    
    by_type = [
        {'type': row[0], 'count': row[1]}
        for row in cursor.fetchall()
    ]
    
    # By intersection
    cursor.execute('''
        SELECT i.name, COUNT(*) as count
        FROM violations v
        JOIN intersections i ON v.intersection_id = i.id
        WHERE v.timestamp >= datetime('now', '-24 hours')
        GROUP BY i.name
        ORDER BY count DESC
    ''')
    
    by_intersection = [
        {'intersection': row[0], 'count': row[1]}
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'hourly': hourly_data,
        'by_type': by_type,
        'by_intersection': by_intersection
    })

@bp.route('/api/system/status')
@require_role('operator')
def get_system_status():
    """Get overall system health status"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Count intersections by status
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM intersections
        GROUP BY status
    ''')
    intersection_status = dict(cursor.fetchall())
    
    # Count signals by state
    cursor.execute('''
        SELECT current_state, COUNT(*) as count
        FROM traffic_signals
        GROUP BY current_state
    ''')
    signal_status = dict(cursor.fetchall())
    
    # Recent system activity
    cursor.execute('''
        SELECT action, COUNT(*) as count
        FROM audit_logs
        WHERE timestamp >= datetime('now', '-1 hour')
        GROUP BY action
    ''')
    recent_activity = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        'intersection_status': intersection_status,
        'signal_status': signal_status,
        'recent_activity': recent_activity,
        'timestamp': datetime.now().isoformat()
    })

# ===== PHASE 3: PREDICTIVE TRAFFIC MANAGEMENT =====

@bp.route('/api/prediction/density/<int:intersection_id>')
@require_role('operator')
def predict_density(intersection_id):
    """Predict traffic density for an intersection"""
    from traffic_prediction import predictor
    
    try:
        prediction = predictor.predict_traffic_density(intersection_id)
        return jsonify({
            'success': True,
            'intersection_id': intersection_id,
            'prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/congestion/<int:intersection_id>')
@require_role('operator')
def detect_congestion_status(intersection_id):
    """Detect congestion at an intersection"""
    from traffic_prediction import predictor
    
    try:
        congestion = predictor.detect_congestion(intersection_id)
        return jsonify({
            'success': True,
            'intersection_id': intersection_id,
            'congestion': congestion,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/optimize/<int:intersection_id>')
@require_role('operator')
def get_optimization(intersection_id):
    """Get optimized signal timing for an intersection"""
    from traffic_prediction import predictor
    
    try:
        optimization = predictor.optimize_signal_timing(intersection_id)
        return jsonify({
            'success': True,
            'intersection_id': intersection_id,
            'optimization': optimization,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/optimize/<int:intersection_id>/apply', methods=['POST'])
@require_role('operator')
def apply_optimization(intersection_id):
    """Apply optimized signal timing"""
    from traffic_prediction import predictor
    
    try:
        optimization = predictor.optimize_signal_timing(intersection_id)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update signal timings
        cursor.execute('''
            UPDATE traffic_signals
            SET total_cycle_time = ?,
                predictive_mode = 1
            WHERE intersection_id = ? AND direction = 'NS'
        ''', (optimization['ns_green_time'] + optimization['ns_amber_time'], intersection_id))
        
        cursor.execute('''
            UPDATE traffic_signals
            SET total_cycle_time = ?,
                predictive_mode = 1
            WHERE intersection_id = ? AND direction = 'EW'
        ''', (optimization['ew_green_time'] + optimization['ew_amber_time'], intersection_id))
        
        # Log audit
        log_audit(
            user_id=g.user['id'],
            action='apply_predictive_optimization',
            resource_type='intersection',
            resource_id=intersection_id,
            old_value=None,
            new_value=optimization,
            ip_address=request.remote_addr
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Predictive optimization applied',
            'optimization': optimization
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/network-health')
@require_role('operator')
def get_network_health():
    """Get overall network health metrics"""
    from traffic_prediction import predictor
    
    try:
        health = predictor.get_network_health()
        return jsonify({
            'success': True,
            'network_health': health,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/emergency-routing/<int:intersection_id>')
@require_role('operator')
def get_emergency_routing(intersection_id):
    """Get emergency routing suggestions"""
    from traffic_prediction import predictor
    
    try:
        routing = predictor.suggest_emergency_routing(intersection_id)
        
        if not routing:
            return jsonify({'error': 'Intersection not found'}), 404
        
        return jsonify({
            'success': True,
            'routing': routing,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/patterns')
@require_role('operator')
def get_violation_patterns():
    """Analyze violation patterns"""
    from traffic_prediction import predictor
    
    days = request.args.get('days', 7, type=int)
    
    try:
        patterns = predictor.analyze_violation_patterns(days)
        return jsonify({
            'success': True,
            'patterns': patterns,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/report/<int:intersection_id>')
@require_role('operator')
def get_optimization_report(intersection_id):
    """Generate comprehensive optimization report"""
    from traffic_prediction import predictor
    
    try:
        report = predictor.generate_optimization_report(intersection_id)
        return jsonify({
            'success': True,
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/prediction/auto-optimize', methods=['POST'])
@require_role('operator')
def auto_optimize_network():
    """Automatically optimize all congested intersections"""
    from traffic_prediction import predictor
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all active intersections
        cursor.execute('SELECT id, name FROM intersections WHERE status = "active"')
        intersections = cursor.fetchall()
        
        optimized = []
        skipped = []
        
        for intersection_id, name in intersections:
            congestion = predictor.detect_congestion(intersection_id)
            
            if congestion['is_congested']:
                optimization = predictor.optimize_signal_timing(intersection_id)
                
                # Apply optimization
                cursor.execute('''
                    UPDATE traffic_signals
                    SET total_cycle_time = ?,
                        predictive_mode = 1
                    WHERE intersection_id = ?
                ''', (optimization['total_cycle_time'], intersection_id))
                
                optimized.append({
                    'id': intersection_id,
                    'name': name,
                    'severity': congestion['severity']
                })
            else:
                skipped.append({
                    'id': intersection_id,
                    'name': name,
                    'reason': 'not_congested'
                })
        
        # Log audit
        log_audit(
            user_id=g.user['id'],
            action='auto_optimize_network',
            resource_type='network',
            resource_id=None,
            old_value=None,
            new_value={'optimized_count': len(optimized)},
            ip_address=request.remote_addr
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'optimized': optimized,
            'skipped': skipped,
            'total_optimized': len(optimized),
            'message': f'Optimized {len(optimized)} congested intersections'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
