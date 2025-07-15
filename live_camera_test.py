#!/usr/bin/env python3
"""
Live Camera Traffic Violation Detection Test Script
This script runs the live camera detection independently for testing purposes.
"""

import cv2
import sys
import os
from datetime import datetime
import threading
import time

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_detection import EnhancedViolationDetector
    from app import init_db, load_models
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project directory")
    sys.exit(1)

class LiveCameraDetector:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.detector = EnhancedViolationDetector()
        self.is_running = False
        self.frame_count = 0
        self.violation_count = 0
        
        # Initialize database
        print("Initializing database...")
        init_db()
        
        print("Loading AI models...")
        load_models()
        
        print("✅ Live Camera Detection System Ready!")
        print("Press 'q' to quit, 's' to save screenshot, 'r' to reset counters")
        print("-" * 60)
    
    def detect_violations_in_frame(self, frame):
        """Detect violations in a single frame"""
        try:
            violations = self.detector.detect_person_on_motorcycle(frame)
            
            # Save violations to database
            for violation in violations:
                self.detector.save_violation_to_database(violation, f"live_camera_frame_{self.frame_count}")
                self.violation_count += 1
                
                # Print violation details
                print(f"🚨 VIOLATION DETECTED (Frame {self.frame_count}):")
                print(f"   Vehicle: {violation['vehicle_type']}")
                print(f"   License Plate: {violation.get('license_plate', 'Not detected')}")
                print(f"   Violation Type: {violation['violations'][0]['type']}")
                print(f"   Fine Amount: ₹{violation['violations'][0]['fine_amount']}")
                if violation.get('owner_info'):
                    print(f"   Owner: {violation['owner_info']['owner']}")
                    print(f"   Phone: {violation['owner_info']['phone']}")
                print("-" * 40)
            
            return violations
            
        except Exception as e:
            print(f"Error detecting violations: {e}")
            return []
    
    def add_overlay_info(self, frame, violations):
        """Add information overlay to the frame"""
        height, width = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Add header info
        cv2.rectangle(overlay, (0, 0), (width, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Add text information
        cv2.putText(frame, "LIVE TRAFFIC VIOLATION DETECTION", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {self.frame_count} | Violations: {self.violation_count}", 
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add status indicator
        status_color = (0, 255, 0) if len(violations) == 0 else (0, 0, 255)
        status_text = "MONITORING" if len(violations) == 0 else "VIOLATION DETECTED!"
        cv2.putText(frame, status_text, (width - 200, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        return frame
    
    def start_detection(self):
        """Start the live camera detection"""
        print(f"Starting camera {self.camera_index}...")
        cap = cv2.VideoCapture(self.camera_index)
        
        if not cap.isOpened():
            print(f"❌ Error: Could not open camera {self.camera_index}")
            print("Available cameras to try:")
            for i in range(5):
                test_cap = cv2.VideoCapture(i)
                if test_cap.isOpened():
                    print(f"  Camera {i}: Available")
                    test_cap.release()
                else:
                    print(f"  Camera {i}: Not available")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Camera opened successfully!")
        print("📹 Live detection started...")
        
        self.is_running = True
        
        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to read frame from camera")
                    break
                
                self.frame_count += 1
                
                # Detect violations (process every 30th frame for performance)
                violations = []
                if self.frame_count % 30 == 0:
                    violations = self.detect_violations_in_frame(frame)
                
                # Create annotated frame
                if violations:
                    annotated_frame = self.detector.create_violation_image(frame, violations)
                else:
                    annotated_frame = frame.copy()
                
                # Add overlay information
                display_frame = self.add_overlay_info(annotated_frame, violations)
                
                # Display the frame
                cv2.imshow('Live Traffic Violation Detection', display_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("🛑 Stopping detection...")
                    self.is_running = False
                elif key == ord('s'):
                    # Save screenshot
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot_path = f"screenshots/live_camera_{timestamp}.jpg"
                    cv2.imwrite(screenshot_path, display_frame)
                    print(f"📸 Screenshot saved: {screenshot_path}")
                elif key == ord('r'):
                    # Reset counters
                    self.frame_count = 0
                    self.violation_count = 0
                    print("🔄 Counters reset")
                
        except KeyboardInterrupt:
            print("\n🛑 Detection stopped by user")
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("✅ Camera released and windows closed")
            print(f"📊 Session Summary:")
            print(f"   Total Frames Processed: {self.frame_count}")
            print(f"   Total Violations Detected: {self.violation_count}")

def main():
    print("🚀 Live Camera Traffic Violation Detection System")
    print("=" * 60)
    
    # Create necessary directories
    os.makedirs('screenshots', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    # Get camera index from user
    camera_index = 0
    if len(sys.argv) > 1:
        try:
            camera_index = int(sys.argv[1])
        except ValueError:
            print("Invalid camera index. Using default camera (0)")
    
    # Initialize and start detection
    detector = LiveCameraDetector(camera_index)
    detector.start_detection()

if __name__ == "__main__":
    main()
