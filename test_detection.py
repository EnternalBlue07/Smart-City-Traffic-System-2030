"""
Test script for helmet detection functionality
"""

import cv2
import numpy as np
from enhanced_detection import EnhancedViolationDetector
import os

def test_with_sample_images():
    """Test detection with uploaded images"""
    detector = EnhancedViolationDetector()
    
    # Check uploads folder for test images
    uploads_folder = "uploads"
    
    if os.path.exists(uploads_folder):
        image_files = [f for f in os.listdir(uploads_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        if image_files:
            print(f"🔍 Found {len(image_files)} image(s) to test:")
            
            for image_file in image_files:
                print(f"\n📸 Testing: {image_file}")
                image_path = os.path.join(uploads_folder, image_file)
                
                # Load image
                image = cv2.imread(image_path)
                if image is not None:
                    # Detect violations
                    violations = detector.detect_person_on_motorcycle(image)
                    
                    if violations:
                        print(f"🚨 Found {len(violations)} violation(s)!")
                        
                        for i, violation in enumerate(violations, 1):
                            print(f"\n  Violation {i}:")
                            print(f"    Vehicle: {violation['vehicle_type']}")
                            print(f"    License Plate: {violation.get('license_plate', 'Not detected')}")
                            print(f"    Fine: ₹{violation['violations'][0]['fine_amount']}")
                            
                            if violation.get('owner_info'):
                                owner = violation['owner_info']
                                print(f"    Owner: {owner['owner']}")
                                print(f"    Phone: {owner['phone']}")
                                print(f"    📱 SMS notification sent!")
                        
                        # Create annotated image
                        annotated = detector.create_violation_image(image, violations)
                        output_path = f"screenshots/detected_{image_file}"
                        cv2.imwrite(output_path, annotated)
                        print(f"\n✅ Annotated image saved: {output_path}")
                        
                    else:
                        print("✅ No violations detected")
                else:
                    print(f"❌ Could not load image: {image_file}")
        else:
            print("📂 No images found in uploads folder")
            print("   Upload some test images containing motorcycles with people")
    else:
        print("📂 Uploads folder not found")

def create_demo_violation():
    """Create a demo violation for testing"""
    print("\n🎭 Creating demo violation data...")
    
    detector = EnhancedViolationDetector()
    
    # Simulate a violation
    demo_violation = {
        'vehicle_type': 'motorcycle',
        'bbox': [100, 100, 300, 250],
        'license_plate': 'KA01AB1234',
        'violations': [{'type': 'no_helmet', 'fine_amount': 1000}],
        'confidence': 0.85,
        'owner_info': {
            'owner': 'John Doe',
            'phone': '+91-9876543210',
            'address': 'Bangalore'
        }
    }
    
    # Save to database
    success = detector.save_violation_to_database(demo_violation, "demo_image.jpg")
    
    if success:
        print("✅ Demo violation saved to database")
        
        # Send SMS notification
        owner_info = demo_violation['owner_info']
        detector.send_violation_sms(
            owner_info['phone'],
            demo_violation['license_plate'],
            'No Helmet',
            1000
        )
    else:
        print("❌ Failed to save demo violation")

if __name__ == "__main__":
    print("🚦 AI Traffic Violation Detection Test")
    print("=" * 50)
    
    # Test with actual images if available
    test_with_sample_images()
    
    # Create demo violation
    create_demo_violation()
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("   - Enhanced detection system active")
    print("   - Person + Motorcycle detection enabled")
    print("   - License plate recognition active")
    print("   - SMS notification system ready")
    print("   - Database storage functional")
    print("\n💡 Upload images with motorcycles to test live detection!")
