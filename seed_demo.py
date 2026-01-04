"""
Demo Data Seeding Script
Populates database with demo users, intersections, signals, violations, and transactions
"""

import sqlite3
from datetime import datetime, timedelta
import json
from auth import hash_password

def seed_demo_data():
    """Seed database with demo data"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    print("Starting demo data seeding...")
    
    # Clear existing demo data (optional - comment out to preserve data)
    # cursor.execute('DELETE FROM users WHERE username LIKE "demo_%"')
    
    # 1. Create demo operator users
    operators = [
        {
            'username': 'demo_operator1',
            'password': 'Operator@123',
            'email': 'operator1@traffic.gov.in',
            'phone': '+919876543210',
            'full_name': 'Rajesh Kumar'
        },
        {
            'username': 'demo_operator2',
            'password': 'Operator@456',
            'email': 'operator2@traffic.gov.in',
            'phone': '+919876543211',
            'full_name': 'Priya Sharma'
        },
        {
            'username': 'demo_operator3',
            'password': 'Operator@789',
            'email': 'operator3@traffic.gov.in',
            'phone': '+919876543212',
            'full_name': 'Anil Patel'
        }
    ]
    
    operator_ids = []
    for op in operators:
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, role, phone, profile_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                op['username'],
                hash_password(op['password']),
                op['email'],
                'operator',
                op['phone'],
                json.dumps({'full_name': op['full_name']})
            ))
            operator_ids.append(cursor.lastrowid)
            print(f"✓ Created operator: {op['username']} (password: {op['password']})")
        except sqlite3.IntegrityError:
            print(f"  - Operator {op['username']} already exists")
            cursor.execute('SELECT id FROM users WHERE username = ?', (op['username'],))
            operator_ids.append(cursor.fetchone()[0])
    
    # 2. Create demo citizen users
    citizens = [
        {
            'username': 'demo_citizen1',
            'password': 'Citizen@123',
            'email': 'citizen1@example.com',
            'phone': '+919123456780',
            'full_name': 'Amit Verma'
        },
        {
            'username': 'demo_citizen2',
            'password': 'Citizen@456',
            'email': 'citizen2@example.com',
            'phone': '+919123456781',
            'full_name': 'Sneha Reddy'
        },
        {
            'username': 'demo_citizen3',
            'password': 'Citizen@789',
            'email': 'citizen3@example.com',
            'phone': '+919123456782',
            'full_name': 'Vikram Singh'
        },
        {
            'username': 'demo_citizen4',
            'password': 'Citizen@101',
            'email': 'citizen4@example.com',
            'phone': '+919123456783',
            'full_name': 'Kavya Iyer'
        },
        {
            'username': 'demo_citizen5',
            'password': 'Citizen@202',
            'email': 'citizen5@example.com',
            'phone': '+919123456784',
            'full_name': 'Rohan Desai'
        }
    ]
    
    citizen_ids = []
    for citizen in citizens:
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, role, phone, profile_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                citizen['username'],
                hash_password(citizen['password']),
                citizen['email'],
                'citizen',
                citizen['phone'],
                json.dumps({'full_name': citizen['full_name']})
            ))
            user_id = cursor.lastrowid
            citizen_ids.append(user_id)
            
            # Create wallet for citizen
            cursor.execute('''
                INSERT INTO wallet (user_id, balance, total_paid, total_credits)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 1000.0, 0.0, 1000.0))
            
            print(f"✓ Created citizen: {citizen['username']} (password: {citizen['password']})")
        except sqlite3.IntegrityError:
            print(f"  - Citizen {citizen['username']} already exists")
            cursor.execute('SELECT id FROM users WHERE username = ?', (citizen['username'],))
            citizen_ids.append(cursor.fetchone()[0])
    
    # 3. Create demo intersections (Indian road names)
    intersections = [
        {
            'name': 'MG Road - Brigade Road Circle',
            'location': '12.9716,77.5946',
            'mode': 'auto',
            'status': 'active'
        },
        {
            'name': 'Infantry Road - Dairy Circle',
            'location': '12.9351,77.6245',
            'mode': 'auto',
            'status': 'active'
        },
        {
            'name': 'St. Mark\'s Road - Richmond Circle',
            'location': '12.9698,77.5993',
            'mode': 'manual',
            'status': 'warning'
        },
        {
            'name': 'Cunningham Road - Ulsoor Circle',
            'location': '12.9824,77.6209',
            'mode': 'auto',
            'status': 'active'
        }
    ]
    
    intersection_ids = []
    for intersection in intersections:
        cursor.execute('''
            INSERT INTO intersections (name, location, mode, status, ns_cycle, ew_cycle)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            intersection['name'],
            intersection['location'],
            intersection['mode'],
            intersection['status'],
            'green',
            'red'
        ))
        intersection_ids.append(cursor.lastrowid)
        print(f"✓ Created intersection: {intersection['name']}")
    
    # 4. Create traffic signals for each intersection
    for intersection_id in intersection_ids:
        # NS signal
        cursor.execute('''
            INSERT INTO traffic_signals 
            (intersection_id, direction, current_state, remaining_seconds, total_cycle_time, predictive_mode)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (intersection_id, 'NS', 'green', 45, 60, 0))
        
        # EW signal
        cursor.execute('''
            INSERT INTO traffic_signals 
            (intersection_id, direction, current_state, remaining_seconds, total_cycle_time, predictive_mode)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (intersection_id, 'EW', 'red', 15, 60, 0))
        
        print(f"  ✓ Created signals for intersection ID {intersection_id}")
    
    # 5. Create demo violations
    violation_types = [
        ('No Helmet', 1000),
        ('Red Light Violation', 1500),
        ('Wrong Side Driving', 2000),
        ('Over Speeding', 1200),
        ('No Seat Belt', 800)
    ]
    
    demo_plates = ['KA01AB1234', 'KA02CD5678', 'KA03EF9012', 'KA04GH3456', 'KA05IJ7890']
    
    violation_ids = []
    for i, citizen_id in enumerate(citizen_ids):
        vtype, fine_amount = violation_types[i % len(violation_types)]
        plate = demo_plates[i % len(demo_plates)]
        
        timestamp = (datetime.now() - timedelta(days=i*2)).isoformat()
        
        cursor.execute('''
            INSERT INTO violations 
            (vehicle_type, license_plate, violation_type, timestamp, location, 
             fine_amount, status, operator_id, intersection_id, camera_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Motorcycle' if i % 2 == 0 else 'Car',
            plate,
            vtype,
            timestamp,
            intersections[i % len(intersections)]['name'],
            fine_amount,
            'pending',
            operator_ids[i % len(operator_ids)],
            intersection_ids[i % len(intersection_ids)],
            f'CAM{(i % 4) + 1}'
        ))
        violation_ids.append(cursor.lastrowid)
        print(f"✓ Created violation: {vtype} - {plate}")
    
    # 6. Create demo fines
    for i, violation_id in enumerate(violation_ids):
        due_date = (datetime.now() + timedelta(days=15)).isoformat()
        cursor.execute('''
            SELECT fine_amount FROM violations WHERE id = ?
        ''', (violation_id,))
        amount = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO fines (violation_id, amount, issued_date, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            violation_id,
            amount,
            datetime.now().isoformat(),
            due_date,
            'unpaid' if i % 3 != 0 else 'paid'
        ))
        print(f"✓ Created fine for violation ID {violation_id}")
    
    # 7. Create demo appeals
    for i in range(2):
        cursor.execute('''
            INSERT INTO appeals (violation_id, user_id, status, reason)
            VALUES (?, ?, ?, ?)
        ''', (
            violation_ids[i],
            citizen_ids[i],
            'pending' if i == 0 else 'approved',
            'The violation was not committed by me. I have proof of my location at that time.'
        ))
        print(f"✓ Created appeal for violation ID {violation_ids[i]}")
    
    # 8. Create demo wallet transactions
    for i, citizen_id in enumerate(citizen_ids):
        cursor.execute('SELECT id FROM wallet WHERE user_id = ?', (citizen_id,))
        wallet_result = cursor.fetchone()
        
        if wallet_result:
            wallet_id = wallet_result[0]
            
            # Initial credit
            cursor.execute('''
                INSERT INTO wallet_transactions 
                (wallet_id, type, amount, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                wallet_id,
                'credit',
                1000.0,
                'Initial wallet credit',
                datetime.now().isoformat()
            ))
            
            print(f"✓ Created wallet transaction for citizen ID {citizen_id}")
    
    # 9. Create demo audit logs
    for i, operator_id in enumerate(operator_ids):
        cursor.execute('''
            INSERT INTO audit_logs 
            (user_id, action, resource_type, resource_id, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            operator_id,
            'view_violation',
            'violation',
            violation_ids[i] if i < len(violation_ids) else 1,
            '192.168.1.' + str(100 + i),
            datetime.now().isoformat()
        ))
    
    print("✓ Created audit logs")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✓ Demo data seeding completed successfully!")
    print("="*60)
    print("\nDEMO CREDENTIALS:")
    print("\nOperators:")
    for op in operators:
        print(f"  Username: {op['username']} | Password: {op['password']}")
    print("\nCitizens:")
    for citizen in citizens:
        print(f"  Username: {citizen['username']} | Password: {citizen['password']}")
    print("\n" + "="*60)

if __name__ == '__main__':
    seed_demo_data()
