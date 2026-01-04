"""
Traffic Prediction & Optimization Module
Phase 3: ML-based signal timing and congestion detection
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import json

class TrafficPredictor:
    """Predict traffic patterns and optimize signal timings"""
    
    def __init__(self):
        self.db_path = 'database/violations.db'
        self.prediction_window = 60  # minutes
        self.min_data_points = 10
        
    def get_db(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_historical_violations(self, intersection_id, hours=24):
        """Get historical violation data for an intersection"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%H', timestamp) as hour,
                strftime('%w', timestamp) as day_of_week,
                COUNT(*) as count
            FROM violations
            WHERE intersection_id = ?
            AND timestamp >= datetime('now', '-' || ? || ' hours')
            GROUP BY hour, day_of_week
            ORDER BY hour
        ''', (intersection_id, hours))
        
        data = cursor.fetchall()
        conn.close()
        
        return data
    
    def predict_traffic_density(self, intersection_id):
        """Predict traffic density for next hour based on historical patterns"""
        historical_data = self.get_historical_violations(intersection_id, hours=168)  # 7 days
        
        if len(historical_data) < self.min_data_points:
            return {
                'density': 'medium',
                'confidence': 0.5,
                'recommended_cycle': 60,
                'prediction': 'insufficient_data'
            }
        
        # Get current hour and day
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()
        
        # Find similar time periods
        similar_periods = [
            count for hour, day, count in historical_data
            if int(hour) == current_hour and int(day) == current_day
        ]
        
        if not similar_periods:
            # Fallback to same hour regardless of day
            similar_periods = [
                count for hour, day, count in historical_data
                if int(hour) == current_hour
            ]
        
        if not similar_periods:
            avg_violations = 5
        else:
            avg_violations = np.mean(similar_periods)
        
        # Classify density
        if avg_violations < 3:
            density = 'low'
            recommended_cycle = 45  # Shorter cycles for light traffic
            confidence = 0.7
        elif avg_violations < 7:
            density = 'medium'
            recommended_cycle = 60  # Standard cycle
            confidence = 0.8
        elif avg_violations < 15:
            density = 'high'
            recommended_cycle = 75  # Longer cycles for heavy traffic
            confidence = 0.85
        else:
            density = 'very_high'
            recommended_cycle = 90  # Maximum cycle for congestion
            confidence = 0.9
        
        return {
            'density': density,
            'confidence': confidence,
            'recommended_cycle': recommended_cycle,
            'avg_violations': float(avg_violations),
            'prediction': 'success',
            'similar_samples': len(similar_periods)
        }
    
    def detect_congestion(self, intersection_id, threshold_minutes=15):
        """Detect if intersection is experiencing congestion"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get recent violations (last 15 minutes)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM violations
            WHERE intersection_id = ?
            AND timestamp >= datetime('now', '-' || ? || ' minutes')
        ''', (intersection_id, threshold_minutes))
        
        recent_count = cursor.fetchone()[0]
        
        # Get average for same time period
        cursor.execute('''
            SELECT AVG(violation_count) FROM (
                SELECT COUNT(*) as violation_count
                FROM violations
                WHERE intersection_id = ?
                AND timestamp >= datetime('now', '-7 days')
                AND timestamp < datetime('now', '-1 day')
                GROUP BY strftime('%Y-%m-%d %H', timestamp)
            )
        ''', (intersection_id,))
        
        avg_result = cursor.fetchone()[0]
        avg_count = avg_result if avg_result else 5
        
        conn.close()
        
        # Detect congestion if current is 2x average
        is_congested = recent_count > (avg_count * 2)
        severity = 'none'
        
        if is_congested:
            ratio = recent_count / max(avg_count, 1)
            if ratio >= 3:
                severity = 'severe'
            elif ratio >= 2.5:
                severity = 'high'
            else:
                severity = 'moderate'
        
        return {
            'is_congested': is_congested,
            'severity': severity,
            'recent_violations': recent_count,
            'average_violations': float(avg_count),
            'ratio': float(recent_count / max(avg_count, 1)),
            'threshold_exceeded': is_congested
        }
    
    def optimize_signal_timing(self, intersection_id):
        """Generate optimized signal timing based on traffic patterns"""
        prediction = self.predict_traffic_density(intersection_id)
        congestion = self.detect_congestion(intersection_id)
        
        # Base timings
        green_time = prediction['recommended_cycle']
        amber_time = 5
        
        # Adjust for congestion
        if congestion['is_congested']:
            if congestion['severity'] == 'severe':
                green_time += 20
            elif congestion['severity'] == 'high':
                green_time += 15
            else:
                green_time += 10
        
        # Calculate NS/EW split (60/40 default)
        ns_green = int(green_time * 0.6)
        ew_green = int(green_time * 0.4)
        
        return {
            'total_cycle_time': green_time + amber_time,
            'ns_green_time': ns_green,
            'ns_amber_time': amber_time,
            'ew_green_time': ew_green,
            'ew_amber_time': amber_time,
            'prediction': prediction,
            'congestion': congestion,
            'optimization_applied': True
        }
    
    def get_network_health(self):
        """Get overall network health and performance metrics"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get all intersections
        cursor.execute('SELECT id, name, status FROM intersections')
        intersections = cursor.fetchall()
        
        network_metrics = {
            'total_intersections': len(intersections),
            'active_intersections': 0,
            'congested_intersections': 0,
            'optimized_intersections': 0,
            'intersections': []
        }
        
        for intersection_id, name, status in intersections:
            if status == 'active':
                network_metrics['active_intersections'] += 1
            
            congestion = self.detect_congestion(intersection_id)
            prediction = self.predict_traffic_density(intersection_id)
            
            if congestion['is_congested']:
                network_metrics['congested_intersections'] += 1
            
            intersection_health = {
                'id': intersection_id,
                'name': name,
                'status': status,
                'density': prediction['density'],
                'is_congested': congestion['is_congested'],
                'congestion_severity': congestion['severity'],
                'confidence': prediction['confidence']
            }
            
            network_metrics['intersections'].append(intersection_health)
        
        # Calculate network efficiency score (0-100)
        if network_metrics['total_intersections'] > 0:
            congestion_penalty = (network_metrics['congested_intersections'] / 
                                network_metrics['total_intersections']) * 30
            active_bonus = (network_metrics['active_intersections'] / 
                          network_metrics['total_intersections']) * 100
            
            network_metrics['efficiency_score'] = max(0, min(100, active_bonus - congestion_penalty))
        else:
            network_metrics['efficiency_score'] = 0
        
        conn.close()
        
        return network_metrics
    
    def suggest_emergency_routing(self, intersection_id):
        """Suggest alternative routing for emergency vehicles"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get intersection details
        cursor.execute('SELECT name, location FROM intersections WHERE id = ?', (intersection_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        name, location = result
        
        # Get nearby intersections (simple distance-based)
        cursor.execute('''
            SELECT id, name, location, status
            FROM intersections
            WHERE id != ?
        ''', (intersection_id,))
        
        nearby = cursor.fetchall()
        conn.close()
        
        # Calculate congestion for alternatives
        alternatives = []
        for alt_id, alt_name, alt_location, alt_status in nearby:
            if alt_status == 'active':
                congestion = self.detect_congestion(alt_id)
                alternatives.append({
                    'id': alt_id,
                    'name': alt_name,
                    'is_congested': congestion['is_congested'],
                    'severity': congestion['severity'],
                    'recommended': not congestion['is_congested']
                })
        
        # Sort by least congested
        alternatives.sort(key=lambda x: (x['is_congested'], x['severity']))
        
        return {
            'current_intersection': {
                'id': intersection_id,
                'name': name
            },
            'alternatives': alternatives[:3],  # Top 3 alternatives
            'recommendation': 'Use alternative routes' if alternatives else 'No alternatives available'
        }
    
    def analyze_violation_patterns(self, days=7):
        """Analyze violation patterns across the network"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get violations by hour
        cursor.execute('''
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as count,
                AVG(fine_amount) as avg_fine
            FROM violations
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY hour
            ORDER BY hour
        ''', (days,))
        
        hourly_patterns = [
            {
                'hour': int(row[0]),
                'violations': row[1],
                'avg_fine': float(row[2]) if row[2] else 0
            }
            for row in cursor.fetchall()
        ]
        
        # Get violations by type
        cursor.execute('''
            SELECT 
                violation_type,
                COUNT(*) as count,
                AVG(fine_amount) as avg_fine
            FROM violations
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY violation_type
            ORDER BY count DESC
        ''', (days,))
        
        type_patterns = [
            {
                'type': row[0],
                'count': row[1],
                'avg_fine': float(row[2]) if row[2] else 0
            }
            for row in cursor.fetchall()
        ]
        
        # Identify peak hours
        if hourly_patterns:
            peak_violations = max(hourly_patterns, key=lambda x: x['violations'])
            low_violations = min(hourly_patterns, key=lambda x: x['violations'])
        else:
            peak_violations = {'hour': 12, 'violations': 0}
            low_violations = {'hour': 3, 'violations': 0}
        
        conn.close()
        
        return {
            'hourly_patterns': hourly_patterns,
            'type_patterns': type_patterns,
            'peak_hour': peak_violations['hour'],
            'peak_violations': peak_violations['violations'],
            'low_hour': low_violations['hour'],
            'analysis_period_days': days
        }
    
    def generate_optimization_report(self, intersection_id):
        """Generate comprehensive optimization report for an intersection"""
        optimization = self.optimize_signal_timing(intersection_id)
        
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Get current signal timings
        cursor.execute('''
            SELECT direction, current_state, total_cycle_time, predictive_mode
            FROM traffic_signals
            WHERE intersection_id = ?
        ''', (intersection_id,))
        
        current_signals = [
            {
                'direction': row[0],
                'current_state': row[1],
                'current_cycle_time': row[2],
                'predictive_mode': bool(row[3])
            }
            for row in cursor.fetchall()
        ]
        
        # Get intersection name
        cursor.execute('SELECT name FROM intersections WHERE id = ?', (intersection_id,))
        intersection_name = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate potential improvements
        current_avg_cycle = np.mean([s['current_cycle_time'] for s in current_signals]) if current_signals else 60
        optimized_cycle = optimization['total_cycle_time']
        improvement_pct = ((current_avg_cycle - optimized_cycle) / current_avg_cycle) * 100 if current_avg_cycle > 0 else 0
        
        return {
            'intersection_id': intersection_id,
            'intersection_name': intersection_name,
            'timestamp': datetime.now().isoformat(),
            'current_signals': current_signals,
            'optimization': optimization,
            'improvements': {
                'cycle_time_change': optimized_cycle - current_avg_cycle,
                'improvement_percentage': improvement_pct,
                'estimated_wait_time_reduction': abs(improvement_pct) * 0.3,  # Rough estimate
                'recommended': improvement_pct > 5 or optimization['congestion']['is_congested']
            },
            'recommendations': self._generate_recommendations(optimization)
        }
    
    def _generate_recommendations(self, optimization):
        """Generate actionable recommendations based on optimization data"""
        recommendations = []
        
        congestion = optimization['congestion']
        prediction = optimization['prediction']
        
        if congestion['is_congested']:
            recommendations.append({
                'priority': 'high',
                'action': 'Increase green time',
                'reason': f'Congestion detected ({congestion["severity"]} severity)',
                'impact': 'Reduce wait times by 20-30%'
            })
        
        if prediction['density'] == 'very_high':
            recommendations.append({
                'priority': 'high',
                'action': 'Enable adaptive timing',
                'reason': 'Very high traffic density predicted',
                'impact': 'Optimize flow for peak traffic'
            })
        
        if prediction['density'] == 'low':
            recommendations.append({
                'priority': 'medium',
                'action': 'Reduce cycle times',
                'reason': 'Low traffic density - shorter cycles more efficient',
                'impact': 'Reduce unnecessary wait times'
            })
        
        if prediction['confidence'] < 0.6:
            recommendations.append({
                'priority': 'low',
                'action': 'Collect more data',
                'reason': 'Low prediction confidence',
                'impact': 'Improve future predictions'
            })
        
        return recommendations


# Singleton instance
predictor = TrafficPredictor()
