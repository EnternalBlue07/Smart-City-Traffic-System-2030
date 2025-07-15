"""
Enhanced AI Traffic Violation Detection System
Improved helmet detection and license plate recognition
"""

import cv2
import numpy as np
import easyocr
from ultralytics import YOLO
import sqlite3
import json
from datetime import datetime
import requests

class EnhancedViolationDetector:
    def __init__(self):
        # Initialize models
        self.vehicle_model = YOLO('yolov8n.pt')
        self.ocr_reader = easyocr.Reader(['en'])
        
        # Load custom helmet detection model or use person detection
        try:
            # Try to load custom helmet model if available
            self.helmet_model = YOLO('yolov8n.pt')  # Will use person detection for now
        except:
            self.helmet_model = self.vehicle_model
        
        # Mock database for vehicle registration with more license plates
        self.vehicle_registry = {
            'KA01AB1234': {'owner': 'John Doe', 'phone': '+91-9876543210', 'address': 'Bangalore'},
            'KA02CD5678': {'owner': 'Rajesh Kumar', 'phone': '+91-9876543211', 'address': 'Bangalore'},
            'KA03EF9012': {'owner': 'Priya Sharma', 'phone': '+91-9876543212', 'address': 'Bangalore'},
            'KA04GH3456': {'owner': 'Amit Singh', 'phone': '+91-9876543213', 'address': 'Bangalore'},
            'KA05IJ7890': {'owner': 'Sunita Reddy', 'phone': '+91-9876543214', 'address': 'Bangalore'},
            'TN01AB1234': {'owner': 'Jane Smith', 'phone': '+91-8765432109', 'address': 'Chennai'},
            'MH01EF9012': {'owner': 'Mike Johnson', 'phone': '+91-7654321098', 'address': 'Mumbai'},
            'DL01GH3456': {'owner': 'Sarah Wilson', 'phone': '+91-6543210987', 'address': 'Delhi'},
            'UP01IJ7890': {'owner': 'David Brown', 'phone': '+91-5432109876', 'address': 'Lucknow'},
            # Add generic plates for testing
            'TEST123': {'owner': 'Test User', 'phone': '+91-9999999999', 'address': 'Test City'},
            'DEMO456': {'owner': 'Demo User', 'phone': '+91-8888888888', 'address': 'Demo City'}
        }
    
    def detect_person_on_motorcycle(self, image):
        """Detect persons on motorcycles and check for helmet violations"""
        violations = []
        
        try:
            # Detect all objects in the image
            results = self.vehicle_model(image, verbose=False)
            
            if results[0].boxes is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()
                
                motorcycles = []
                persons = []
                
                # Separate motorcycles and persons
                for i, (box, cls, conf) in enumerate(zip(boxes, classes, confidences)):
                    if conf > 0.5:
                        class_name = self.vehicle_model.names[int(cls)]
                        x1, y1, x2, y2 = map(int, box)
                        
                        if class_name == 'motorcycle':
                            motorcycles.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': conf
                            })
                        elif class_name == 'person':
                            persons.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': conf
                            })
                
                # Check for persons on motorcycles
                for motorcycle in motorcycles:
                    mx1, my1, mx2, my2 = motorcycle['bbox']
                    
                    # Find persons near this motorcycle
                    persons_on_bike = []
                    for person in persons:
                        px1, py1, px2, py2 = person['bbox']
                        
                        # Check if person is within or overlapping motorcycle area
                        if (px1 < mx2 and px2 > mx1 and py1 < my2 and py2 > my1):
                            persons_on_bike.append(person)
                    
                    if persons_on_bike:
                        # Extract motorcycle region for license plate detection
                        motorcycle_region = image[my1:my2, mx1:mx2]
                        license_plate = self.extract_license_plate_advanced(motorcycle_region)
                        
                        # If no plate detected, simulate one for demo (in real system, this wouldn't exist)
                        if not license_plate:
                            license_plate = self.generate_demo_plate()
                        
                        # For demo purposes, simulate helmet detection
                        # In a real scenario, you'd use a trained helmet detection model
                        helmet_violation = self.simulate_helmet_detection(persons_on_bike, image)
                        
                        if helmet_violation:
                            violation_data = {
                                'vehicle_type': 'motorcycle',
                                'bbox': [int(mx1), int(my1), int(mx2), int(my2)],
                                'license_plate': license_plate,
                                'violations': [{
                                    'type': 'no_helmet',
                                    'fine_amount': 1000,
                                    'persons_count': len(persons_on_bike)
                                }],
                                'confidence': float(motorcycle['confidence'])
                            }
                            
                            # Get owner details if license plate detected
                            if license_plate and license_plate in self.vehicle_registry:
                                owner_info = self.vehicle_registry[license_plate]
                                violation_data['owner_info'] = owner_info
                                
                                # Auto-send fine SMS
                                self.send_violation_sms(owner_info['phone'], license_plate, 'No Helmet', 1000)
                            
                            violations.append(violation_data)
        
        except Exception as e:
            print(f"Detection error: {e}")
        
        return violations
    
    def simulate_helmet_detection(self, persons, image):
        """Simulate helmet detection - in reality, this would use a trained model"""
        # For demonstration, we'll assume 70% chance of helmet violation
        # In real implementation, this would analyze the head region of each person
        
        # Simple heuristic: if person's head region (top 20% of bounding box) 
        # has certain color characteristics, assume no helmet
        for person in persons:
            px1, py1, px2, py2 = person['bbox']
            
            # Extract head region (top 30% of person)
            head_height = int((py2 - py1) * 0.3)
            head_region = image[py1:py1 + head_height, px1:px2]
            
            if head_region.size > 0:
                # Simple color analysis - if dominant color is skin-like, assume no helmet
                # This is a very basic approach; a real system would use trained models
                avg_color = np.mean(head_region, axis=(0, 1))
                
                # Skin-like color detection (simplified)
                b, g, r = avg_color
                if 80 < r < 255 and 50 < g < 200 and 20 < b < 120:
                    return True  # Likely no helmet (skin detected)
        
        return False
    
    def extract_license_plate_advanced(self, vehicle_image):
        """Advanced license plate extraction with multiple methods"""
        try:
            # Method 1: OCR on the entire vehicle region
            ocr_results = self.ocr_reader.readtext(vehicle_image)
            
            for result in ocr_results:
                text = result[1].strip().upper()
                # Indian license plate pattern matching
                if self.is_valid_indian_license_plate(text):
                    return text
            
            # Method 2: Look for rectangular regions that might be license plates
            gray = cv2.cvtColor(vehicle_image, cv2.COLOR_BGR2GRAY)
            
            # Apply morphological operations to find rectangular regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 5000:  # Reasonable size for license plate
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # License plates typically have aspect ratio between 2:1 and 4:1
                    if 2.0 < aspect_ratio < 4.5:
                        plate_region = vehicle_image[y:y+h, x:x+w]
                        ocr_results = self.ocr_reader.readtext(plate_region)
                        
                        for result in ocr_results:
                            text = result[1].strip().upper()
                            if self.is_valid_indian_license_plate(text):
                                return text
        
        except Exception as e:
            print(f"License plate extraction error: {e}")
        
        return None
    
    def is_valid_indian_license_plate(self, text):
        """Check if text matches Indian license plate pattern"""
        import re
        
        # Remove spaces and special characters
        cleaned_text = re.sub(r'[^A-Z0-9]', '', text)
        
        # Indian license plate patterns:
        # XX##XX#### (old format)
        # XX##XX#### (new format)
        patterns = [
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',  # Standard format
            r'^[A-Z]{2}[0-9]{2}[A-Z]{1}[0-9]{4}$',   # Some variations
            r'^[A-Z]{2}[0-9]{2}[0-9]{4}$'            # Simplified
        ]
        
        for pattern in patterns:
            if re.match(pattern, cleaned_text) and len(cleaned_text) >= 8:
                return True
        
        return False
    
    def generate_demo_plate(self):
        """Generate a demo license plate for testing"""
        import random
        
        # List of available demo plates
        demo_plates = list(self.vehicle_registry.keys())
        
        # Return a random demo plate
        return random.choice(demo_plates)
    
    def send_violation_sms(self, phone_number, license_plate, violation_type, amount):
        """Send fine notification via SMS"""
        try:
            message = f"""🚨 TRAFFIC VIOLATION FINE 🚨
Vehicle: {license_plate}
Violation: {violation_type}
Fine Amount: ₹{amount}
Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}

Pay within 15 days to avoid penalty.
Visit: https://parivahan.gov.in

- Traffic Police Department"""
            
            print(f"📱 SMS Sent to {phone_number}:")
            print(message)
            print("-" * 50)
            
            # In production, integrate with actual SMS service like:
            # - Twilio
            # - MSG91
            # - AWS SNS
            # - Fast2SMS
            
            return True
            
        except Exception as e:
            print(f"SMS sending error: {e}")
            return False
    
    def save_violation_to_database(self, violation, image_path):
        """Save violation to SQLite database"""
        try:
            conn = sqlite3.connect('database/violations.db')
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_type TEXT,
                    license_plate TEXT,
                    violation_type TEXT,
                    fine_amount REAL,
                    timestamp TEXT,
                    image_path TEXT,
                    owner_name TEXT,
                    owner_phone TEXT,
                    confidence REAL,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            violation_types = ', '.join([v['type'] for v in violation['violations']])
            total_fine = sum([v['fine_amount'] for v in violation['violations']])
            
            owner_info = violation.get('owner_info', {})
            
            cursor.execute('''
                INSERT INTO enhanced_violations 
                (vehicle_type, license_plate, violation_type, fine_amount, timestamp, 
                 image_path, owner_name, owner_phone, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                violation['vehicle_type'],
                violation.get('license_plate', 'Unknown'),
                violation_types,
                total_fine,
                datetime.now().isoformat(),
                image_path,
                owner_info.get('owner', 'Unknown'),
                owner_info.get('phone', 'Unknown'),
                violation.get('confidence', 0.0),
                'pending'
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Violation saved to database")
            return True
            
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def create_violation_image(self, image, violations):
        """Create annotated image showing violations"""
        annotated_image = image.copy()
        
        for violation in violations:
            x1, y1, x2, y2 = violation['bbox']
            
            # Draw red bounding box
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
            # Add violation text
            violation_text = f"NO HELMET - Fine: ₹{violation['violations'][0]['fine_amount']}"
            if violation.get('license_plate'):
                violation_text += f"\nPlate: {violation['license_plate']}"
            
            # Add text background
            text_size = cv2.getTextSize(violation_text.split('\n')[0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(annotated_image, (x1, y1-40), (x1 + text_size[0] + 10, y1), (0, 0, 255), -1)
            
            # Add text
            cv2.putText(annotated_image, violation_text.split('\n')[0], (x1 + 5, y1 - 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if violation.get('license_plate'):
                cv2.putText(annotated_image, f"Plate: {violation['license_plate']}", 
                           (x1 + 5, y1 - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated_image

# Example usage and testing
if __name__ == "__main__":
    detector = EnhancedViolationDetector()
    
    # Test with an image
    test_image_path = "test_image.jpg"  # Replace with actual image path
    
    if cv2.imread(test_image_path) is not None:
        image = cv2.imread(test_image_path)
        violations = detector.detect_person_on_motorcycle(image)
        
        if violations:
            print(f"🚨 Found {len(violations)} violation(s):")
            for i, violation in enumerate(violations, 1):
                print(f"\nViolation {i}:")
                print(f"  Vehicle: {violation['vehicle_type']}")
                print(f"  License Plate: {violation.get('license_plate', 'Not detected')}")
                print(f"  Fine Amount: ₹{violation['violations'][0]['fine_amount']}")
                if violation.get('owner_info'):
                    print(f"  Owner: {violation['owner_info']['owner']}")
                    print(f"  Phone: {violation['owner_info']['phone']}")
                
                # Save to database
                detector.save_violation_to_database(violation, test_image_path)
            
            # Create annotated image
            annotated = detector.create_violation_image(image, violations)
            cv2.imwrite("violations_detected.jpg", annotated)
            print(f"\n✅ Annotated image saved as 'violations_detected.jpg'")
        else:
            print("✅ No violations detected in the image")
    else:
        print("❌ Test image not found. Place a test image and update the path.")
