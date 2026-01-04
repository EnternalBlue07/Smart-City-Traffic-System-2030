"""
Phase 1 Integration Test
Tests database, auth, and basic functionality
"""

import sqlite3
from auth import hash_password, verify_password, create_user, get_user_by_username

def test_phase1():
    """Run Phase 1 integration tests"""
    print("="*60)
    print("Phase 1 Integration Tests")
    print("="*60)
    
    # Test 1: Database connectivity
    print("\n1. Testing database connectivity...")
    try:
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        
        # Check all new tables exist
        tables = [
            'users', 'sessions', 'intersections', 'traffic_signals',
            'appeals', 'wallet', 'wallet_transactions', 'audit_logs'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            if result:
                print(f"  ✓ Table '{table}' exists")
            else:
                print(f"  ✗ Table '{table}' missing!")
        
        conn.close()
        print("  ✓ Database connectivity test passed")
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
    
    # Test 2: Password hashing
    print("\n2. Testing password hashing...")
    try:
        password = "TestPassword@123"
        hashed = hash_password(password)
        
        if verify_password(password, hashed):
            print("  ✓ Password hashing and verification works")
        else:
            print("  ✗ Password verification failed")
    except Exception as e:
        print(f"  ✗ Password hashing test failed: {e}")
    
    # Test 3: User authentication
    print("\n3. Testing user authentication...")
    try:
        # Get demo user
        user = get_user_by_username('demo_operator1')
        
        if user:
            print(f"  ✓ Retrieved user: {user['username']}")
            print(f"    Role: {user['role']}")
            print(f"    Email: {user['email']}")
            
            # Test password verification
            if verify_password('Operator@123', user['password_hash']):
                print("  ✓ Demo operator password verification successful")
            else:
                print("  ✗ Demo operator password verification failed")
        else:
            print("  ✗ Could not retrieve demo user")
    except Exception as e:
        print(f"  ✗ User authentication test failed: {e}")
    
    # Test 4: Check demo data
    print("\n4. Testing demo data...")
    try:
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'demo_%'")
        user_count = cursor.fetchone()[0]
        print(f"  ✓ Demo users: {user_count}")
        
        # Count intersections
        cursor.execute("SELECT COUNT(*) FROM intersections")
        intersection_count = cursor.fetchone()[0]
        print(f"  ✓ Intersections: {intersection_count}")
        
        # Count signals
        cursor.execute("SELECT COUNT(*) FROM traffic_signals")
        signal_count = cursor.fetchone()[0]
        print(f"  ✓ Traffic signals: {signal_count}")
        
        # Count violations
        cursor.execute("SELECT COUNT(*) FROM violations WHERE operator_id IS NOT NULL")
        violation_count = cursor.fetchone()[0]
        print(f"  ✓ Violations with operator: {violation_count}")
        
        conn.close()
    except Exception as e:
        print(f"  ✗ Demo data test failed: {e}")
    
    # Test 5: Check new columns in existing tables
    print("\n5. Testing schema extensions...")
    try:
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        
        # Check violations table columns
        cursor.execute("PRAGMA table_info(violations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = ['operator_id', 'intersection_id', 'camera_id', 'is_challenged', 'wallet_payment']
        for col in new_columns:
            if col in columns:
                print(f"  ✓ Column 'violations.{col}' exists")
            else:
                print(f"  ✗ Column 'violations.{col}' missing!")
        
        conn.close()
    except Exception as e:
        print(f"  ✗ Schema extension test failed: {e}")
    
    print("\n" + "="*60)
    print("✓ Phase 1 Integration Tests Complete")
    print("="*60)

if __name__ == '__main__':
    test_phase1()
