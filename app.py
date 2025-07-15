"""
Advanced AI Traffic Violation Detection System
Web-based application with automatic fining system
"""

import os
import cv2
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import threading
import queue
import json
from pathlib import Path
import easyocr
import requests
from ultralytics import YOLO
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize OCR reader
ocr_reader = easyocr.Reader(['en'])

# Load AI models
vehicle_model = None
helmet_model = None
seatbelt_model = None
license_plate_model = None

# Database setup
def init_db():
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_type TEXT,
            license_plate TEXT,
            violation_type TEXT,
            timestamp TEXT,
            location TEXT,
            fine_amount REAL,
            status TEXT DEFAULT 'pending',
            image_path TEXT,
            phone_number TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            total_vehicles INTEGER,
            violations_count INTEGER,
            analysis_data TEXT,
            timestamp TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_id INTEGER,
            amount REAL,
            issued_date TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'unpaid',
            FOREIGN KEY (violation_id) REFERENCES violations (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Load AI models
def load_models():
    global vehicle_model, helmet_model, seatbelt_model, license_plate_model
    
    try:
        vehicle_model = YOLO('yolov8n.pt')  # Vehicle detection
        print("✓ Vehicle detection model loaded")
        
        # Copy models from parent directory if they exist
        parent_models = Path('../')
        if (parent_models / 'seat_belt_5.pt').exists():
            seatbelt_model = YOLO('../seat_belt_5.pt')
            print("✓ Seatbelt detection model loaded")
        
        if (parent_models / 'plat_license.pt').exists():
            license_plate_model = YOLO('../plat_license.pt')
            print("✓ License plate detection model loaded")
        
    except Exception as e:
        print(f"Error loading models: {e}")

def extract_license_plate(image):
    """Extract license plate text using OCR"""
    try:
        if license_plate_model:
            results = license_plate_model(image)
            if results[0].boxes is not None:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    plate_region = image[y1:y2, x1:x2]
                    
                    # Use OCR to extract text
                    ocr_results = ocr_reader.readtext(plate_region)
                    if ocr_results:
                        plate_text = ''.join([result[1] for result in ocr_results])
                        return plate_text.replace(' ', '').upper()
        return None
    except Exception as e:
        print(f"License plate extraction error: {e}")
        return None

# Import enhanced detection system
from enhanced_detection import EnhancedViolationDetector

# Initialize enhanced detector
enhanced_detector = EnhancedViolationDetector()

def process_camera_feed():
    """Process live camera feed for violations"""
    cap = cv2.VideoCapture(0)  # 0 for the default camera
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Perform detection on the captured frame
        violations = detect_violations(frame)
        
        # Annotate and display the frame
        annotated_frame = enhanced_detector.create_violation_image(frame, violations)
        cv2.imshow("Live Camera Feed", annotated_frame)

        # Exit loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def detect_violations(image):
    """Detect traffic violations in an image using enhanced system"""
    try:
        # Use enhanced detection system
        violations = enhanced_detector.detect_person_on_motorcycle(image)
        
        # Save each violation to database automatically
        for violation in violations:
            enhanced_detector.save_violation_to_database(violation, "uploaded_image")
        
        return violations
        
    except Exception as e:
        print(f"Enhanced violation detection error: {e}")
        return []

def send_fine_sms(phone_number, license_plate, violation_type, amount):
    """Send fine notification via SMS (using SMS API)"""
    try:
        # Using TextBelt API (free SMS service)
        # In production, use proper SMS service like Twilio, MSG91, etc.
        
        message = f"TRAFFIC VIOLATION FINE\n"
        message += f"Vehicle: {license_plate}\n"
        message += f"Violation: {violation_type}\n"
        message += f"Fine Amount: ₹{amount}\n"
        message += f"Pay within 15 days to avoid penalty\n"
        message += f"Visit: https://parivahan.gov.in"
        
        # Example using TextBelt (replace with actual Indian SMS service)
        response = requests.post('https://textbelt.com/text', {
            'phone': phone_number,
            'message': message,
            'key': 'your_api_key_here'  # Replace with actual API key
        })
        
        return response.json()
        
    except Exception as e:
        print(f"SMS sending error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process the file
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            return process_image(file_path)
        elif filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            return process_video(file_path)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

def process_image(file_path):
    """Process uploaded image for violations"""
    try:
        image = cv2.imread(file_path)
        violations = detect_violations(image)
        
        # Save violations to database
        violation_ids = []
        for violation in violations:
            violation_id = save_violation_to_db(violation, file_path)
            violation_ids.append(violation_id)
        
        # Take automatic screenshot
        screenshot_path = take_screenshot(image, violations)
        
        # Convert numpy types to native Python types for JSON serialization
        serializable_violations = json.loads(json.dumps(violations, cls=NumpyEncoder))
        
        return jsonify({
            'success': True,
            'violations': serializable_violations,
            'screenshot_path': screenshot_path,
            'violation_ids': violation_ids
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_video(file_path):
    """Process uploaded video for violations"""
    try:
        cap = cv2.VideoCapture(file_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        violations_summary = {
            'total_vehicles': 0,
            'violations': [],
            'frame_analysis': []
        }
        
        frame_count = 0
        processed_frames = 0
        
        while cap.isOpened() and processed_frames < 100:  # Process max 100 frames
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every 30th frame to speed up analysis
            if frame_count % 30 == 0:
                violations = detect_violations(frame)
                if violations:
                    violations_summary['violations'].extend(violations)
                    violations_summary['frame_analysis'].append({
                        'frame': frame_count,
                        'timestamp': frame_count / fps,
                        'violations': len(violations)
                    })
                    
                    # Save violations to database
                    for violation in violations:
                        save_violation_to_db(violation, file_path, frame_count / fps)
                
                processed_frames += 1
            
            frame_count += 1
        
        cap.release()
        
        # Save analysis results
        save_analysis_to_db(file_path, violations_summary)
        
        return jsonify({
            'success': True,
            'analysis': violations_summary,
            'total_frames': total_frames,
            'processed_frames': processed_frames
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_violation_to_db(violation, file_path, timestamp=None):
    """Save violation to database"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    violation_types = ', '.join([v['type'] for v in violation['violations']])
    total_fine = sum([v['fine_amount'] for v in violation['violations']])
    
    cursor.execute('''
        INSERT INTO violations 
        (vehicle_type, license_plate, violation_type, timestamp, fine_amount, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        violation['vehicle_type'],
        violation.get('license_plate', 'Unknown'),
        violation_types,
        timestamp or datetime.now().isoformat(),
        total_fine,
        file_path
    ))
    
    violation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return violation_id

def save_analysis_to_db(filename, analysis_data):
    """Save analysis results to database"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO analysis_results 
        (filename, total_vehicles, violations_count, analysis_data, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        filename,
        len(analysis_data['violations']),
        len(analysis_data['violations']),
        json.dumps(analysis_data),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def take_screenshot(image, violations):
    """Take automatic screenshot with violation highlights"""
    try:
        screenshot = image.copy()
        
        for violation in violations:
            x1, y1, x2, y2 = violation['bbox']
            
            # Draw bounding box
            cv2.rectangle(screenshot, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Add violation text
            violation_text = f"{violation['vehicle_type']} - {', '.join([v['type'] for v in violation['violations']])}"
            cv2.putText(screenshot, violation_text, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Save screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"screenshots/violation_{timestamp}.jpg"
        cv2.imwrite(screenshot_path, screenshot)
        
        return screenshot_path
        
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

@app.route('/violations')
def get_violations():
    """Get all violations from database"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM violations ORDER BY timestamp DESC')
    violations = cursor.fetchall()
    conn.close()
    
    return jsonify(violations)

@app.route('/issue_fine', methods=['POST'])
def issue_fine():
    """Issue fine for a violation"""
    data = request.json
    violation_id = data.get('violation_id')
    phone_number = data.get('phone_number')
    
    if not violation_id or not phone_number:
        return jsonify({'error': 'Missing required data'}), 400
    
    # Get violation details
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM violations WHERE id = ?', (violation_id,))
    violation = cursor.fetchone()
    
    if not violation:
        return jsonify({'error': 'Violation not found'}), 404
    
    # Update phone number
    cursor.execute('UPDATE violations SET phone_number = ? WHERE id = ?', 
                   (phone_number, violation_id))
    
    # Create fine record
    due_date = (datetime.now() + timedelta(days=15)).isoformat()
    cursor.execute('''
        INSERT INTO fines (violation_id, amount, issued_date, due_date, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (violation_id, violation[5], datetime.now().isoformat(), due_date, 'unpaid'))
    
    conn.commit()
    conn.close()
    
    # Send SMS notification
    sms_result = send_fine_sms(phone_number, violation[2], violation[3], violation[5])
    
    return jsonify({
        'success': True,
        'message': 'Fine issued successfully',
        'sms_sent': sms_result is not None
    })

@app.route('/dashboard')
def dashboard():
    """Dashboard with analytics"""
    return render_template('dashboard.html')

@app.route('/analytics')
def get_analytics():
    """Get analytics data"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    # Get violation statistics
    cursor.execute('''
        SELECT violation_type, COUNT(*) as count, SUM(fine_amount) as total_fines
        FROM violations 
        GROUP BY violation_type
    ''')
    violation_stats = cursor.fetchall()
    
    # Get daily violations
    cursor.execute('''
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM violations 
        WHERE timestamp >= datetime('now', '-30 days')
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''')
    daily_violations = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'violation_stats': violation_stats,
        'daily_violations': daily_violations
    })

if __name__ == '__main__':
    # Initialize database and load models
    init_db()
    load_models()
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('screenshots', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
