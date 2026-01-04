"""
Flask-SocketIO Real-time Communication Module
Handles WebSocket connections and event broadcasting
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request
import json

# Initialize SocketIO
socketio = None

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    global socketio
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=False
    )
    
    register_handlers()
    print("✓ SocketIO initialized")
    return socketio

def register_handlers():
    """Register all WebSocket event handlers"""
    
    # ===== OPERATOR NAMESPACE =====
    
    @socketio.on('connect', namespace='/operator')
    def operator_connect():
        """Handle operator connection"""
        print(f"Operator connected: {request.sid}")
        emit('connection_status', {'status': 'connected', 'message': 'Welcome, Operator'})
        
        # Broadcast to other operators
        emit('operator_online', {
            'operator_id': request.sid,
            'timestamp': str(datetime.now())
        }, broadcast=True, include_self=False, namespace='/operator')
    
    @socketio.on('disconnect', namespace='/operator')
    def operator_disconnect():
        """Handle operator disconnection"""
        print(f"Operator disconnected: {request.sid}")
        emit('operator_offline', {
            'operator_id': request.sid,
            'timestamp': str(datetime.now())
        }, broadcast=True, namespace='/operator')
    
    @socketio.on('subscribe_intersection', namespace='/operator')
    def subscribe_intersection(data):
        """Subscribe to specific intersection updates"""
        intersection_id = data.get('intersection_id')
        if intersection_id:
            room = f"intersection_{intersection_id}"
            join_room(room)
            emit('subscribed', {
                'intersection_id': intersection_id,
                'message': f'Subscribed to intersection {intersection_id}'
            })
            print(f"Operator {request.sid} subscribed to {room}")
    
    @socketio.on('unsubscribe_intersection', namespace='/operator')
    def unsubscribe_intersection(data):
        """Unsubscribe from intersection updates"""
        intersection_id = data.get('intersection_id')
        if intersection_id:
            room = f"intersection_{intersection_id}"
            leave_room(room)
            emit('unsubscribed', {
                'intersection_id': intersection_id,
                'message': f'Unsubscribed from intersection {intersection_id}'
            })
            print(f"Operator {request.sid} unsubscribed from {room}")
    
    # ===== CITIZEN NAMESPACE =====
    
    @socketio.on('connect', namespace='/citizen')
    def citizen_connect():
        """Handle citizen connection"""
        print(f"Citizen connected: {request.sid}")
        emit('connection_status', {'status': 'connected', 'message': 'Welcome to Smart Traffic System'})
    
    @socketio.on('disconnect', namespace='/citizen')
    def citizen_disconnect():
        """Handle citizen disconnection"""
        print(f"Citizen disconnected: {request.sid}")
    
    @socketio.on('subscribe_violations', namespace='/citizen')
    def subscribe_violations(data):
        """Subscribe to personal violation updates"""
        user_id = data.get('user_id')
        if user_id:
            room = f"user_{user_id}"
            join_room(room)
            emit('subscribed', {
                'user_id': user_id,
                'message': 'Subscribed to violation updates'
            })
            print(f"Citizen {request.sid} subscribed to user_{user_id}")
    
    # ===== SIGNALS NAMESPACE =====
    
    @socketio.on('connect', namespace='/signals')
    def signals_connect():
        """Handle signals namespace connection"""
        print(f"Client connected to signals: {request.sid}")
        emit('connection_status', {'status': 'connected', 'message': 'Connected to traffic signals'})
    
    @socketio.on('disconnect', namespace='/signals')
    def signals_disconnect():
        """Handle signals namespace disconnection"""
        print(f"Client disconnected from signals: {request.sid}")
    
    # ===== CAMERA NAMESPACE =====
    
    @socketio.on('connect', namespace='/camera')
    def camera_connect():
        """Handle camera namespace connection"""
        print(f"Client connected to camera: {request.sid}")
        emit('connection_status', {'status': 'connected', 'message': 'Connected to camera feeds'})
    
    @socketio.on('disconnect', namespace='/camera')
    def camera_disconnect():
        """Handle camera namespace disconnection"""
        print(f"Client disconnected from camera: {request.sid}")
    
    @socketio.on('subscribe_camera', namespace='/camera')
    def subscribe_camera(data):
        """Subscribe to specific camera feed"""
        camera_id = data.get('camera_id')
        if camera_id:
            room = f"camera_{camera_id}"
            join_room(room)
            emit('subscribed', {
                'camera_id': camera_id,
                'message': f'Subscribed to camera {camera_id}'
            })
            print(f"Client {request.sid} subscribed to camera_{camera_id}")
    
    # ===== NOTIFICATIONS NAMESPACE =====
    
    @socketio.on('connect', namespace='/notifications')
    def notifications_connect():
        """Handle notifications namespace connection"""
        print(f"Client connected to notifications: {request.sid}")
        emit('connection_status', {'status': 'connected', 'message': 'Connected to notifications'})
    
    @socketio.on('disconnect', namespace='/notifications')
    def notifications_disconnect():
        """Handle notifications namespace disconnection"""
        print(f"Client disconnected from notifications: {request.sid}")

# ===== BROADCAST HELPER FUNCTIONS =====

from datetime import datetime

def broadcast_signal_update(intersection_id, direction, state, remaining_seconds=0):
    """Broadcast signal state update"""
    if socketio:
        socketio.emit('signal_state_update', {
            'intersection_id': intersection_id,
            'direction': direction,
            'state': state,
            'remaining_seconds': remaining_seconds,
            'timestamp': datetime.now().isoformat()
        }, namespace='/signals')
        
        # Also emit to specific intersection room
        socketio.emit('signal_update', {
            'direction': direction,
            'state': state,
            'remaining_seconds': remaining_seconds,
            'timestamp': datetime.now().isoformat()
        }, room=f"intersection_{intersection_id}", namespace='/operator')

def broadcast_network_state(intersections_data):
    """Broadcast full network state update"""
    if socketio:
        socketio.emit('network_state_update', {
            'all_intersections': intersections_data,
            'timestamp': datetime.now().isoformat()
        }, namespace='/signals')

def broadcast_override_applied(intersection_id, direction, action, user_id):
    """Broadcast signal override notification"""
    if socketio:
        socketio.emit('override_applied', {
            'intersection_id': intersection_id,
            'direction': direction,
            'action': action,
            'applied_by_user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }, namespace='/signals')

def broadcast_emergency_preempt(intersection_id, user_id):
    """Broadcast emergency preemption"""
    if socketio:
        socketio.emit('emergency_preempt', {
            'intersection_id': intersection_id,
            'activated_by_user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }, namespace='/signals')

def broadcast_camera_status(camera_id, is_online, last_frame_at=None):
    """Broadcast camera status update"""
    if socketio:
        socketio.emit('camera_status', {
            'camera_id': camera_id,
            'is_online': is_online,
            'last_frame_at': last_frame_at,
            'timestamp': datetime.now().isoformat()
        }, namespace='/camera')

def broadcast_privacy_toggle(enabled):
    """Broadcast privacy mode toggle"""
    if socketio:
        socketio.emit('privacy_toggle', {
            'enabled': enabled,
            'timestamp': datetime.now().isoformat()
        }, namespace='/camera')

def broadcast_snapshot_captured(camera_id, image_url):
    """Broadcast snapshot capture notification"""
    if socketio:
        socketio.emit('snapshot_captured', {
            'camera_id': camera_id,
            'image_url': image_url,
            'timestamp': datetime.now().isoformat()
        }, room=f"camera_{camera_id}", namespace='/camera')

def notify_violation_detected(violation_id, plate, confidence):
    """Notify system of new violation detection"""
    if socketio:
        socketio.emit('violation_detected', {
            'violation_id': violation_id,
            'plate': plate,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }, namespace='/notifications')

def notify_challan_paid(violation_id, user_id):
    """Notify system of challan payment"""
    if socketio:
        socketio.emit('challan_paid', {
            'violation_id': violation_id,
            'paid_by_user': user_id,
            'timestamp': datetime.now().isoformat()
        }, namespace='/notifications')

def notify_appeal_resolved(appeal_id, decision, user_id):
    """Notify user of appeal resolution"""
    if socketio:
        # Notify specific user
        socketio.emit('appeal_resolved', {
            'appeal_id': appeal_id,
            'decision': decision,
            'timestamp': datetime.now().isoformat()
        }, room=f"user_{user_id}", namespace='/citizen')
        
        # Also broadcast to notifications
        socketio.emit('appeal_resolved', {
            'appeal_id': appeal_id,
            'decision': decision,
            'notification_to_user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }, namespace='/notifications')

def notify_user(user_id, event_type, data):
    """Send direct notification to a specific user"""
    if socketio:
        socketio.emit(event_type, {
            **data,
            'timestamp': datetime.now().isoformat()
        }, room=f"user_{user_id}", namespace='/citizen')

def notify_operator(operator_id, event_type, data):
    """Send direct notification to a specific operator"""
    if socketio:
        socketio.emit(event_type, {
            **data,
            'timestamp': datetime.now().isoformat()
        }, room=operator_id, namespace='/operator')

def broadcast_system_alert(alert_type, message, severity='info'):
    """Broadcast system-wide alert"""
    if socketio:
        socketio.emit('system_alert', {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }, namespace='/notifications')
