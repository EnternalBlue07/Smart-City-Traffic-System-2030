"""
Citizen Routes
Handles citizen portal endpoints (to be filled in Phase 5)
"""

from flask import Blueprint, jsonify, render_template, g
from auth import require_role

bp = Blueprint('citizen_routes', __name__)

@bp.route('/dashboard')
@require_role('citizen')
def dashboard():
    """Citizen dashboard (stub for Phase 5)"""
    return jsonify({
        'message': 'Citizen dashboard - Coming in Phase 5',
        'user': g.user
    })

@bp.route('/violations')
@require_role('citizen')
def my_violations():
    """List user's violations (stub for Phase 5)"""
    return jsonify({
        'message': 'My violations - Coming in Phase 5',
        'user': g.user
    })

@bp.route('/wallet')
@require_role('citizen')
def wallet():
    """User wallet interface (stub for Phase 5)"""
    return jsonify({
        'message': 'Wallet - Coming in Phase 5',
        'user': g.user
    })
