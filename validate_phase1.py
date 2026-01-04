"""
Phase 1 Validation Script
Validates that all Phase 1 components are properly configured
"""

def validate_phase1():
    """Validate Phase 1 implementation"""
    print("="*60)
    print("Phase 1 Validation")
    print("="*60)
    
    errors = []
    warnings = []
    
    # Check 1: Module imports
    print("\n1. Checking module imports...")
    try:
        import auth
        print("  ✓ auth.py imported successfully")
    except Exception as e:
        errors.append(f"auth.py import failed: {e}")
        print(f"  ✗ auth.py import failed: {e}")
    
    try:
        import realtime
        print("  ✓ realtime.py imported successfully")
    except Exception as e:
        errors.append(f"realtime.py import failed: {e}")
        print(f"  ✗ realtime.py import failed: {e}")
    
    try:
        import middleware
        print("  ✓ middleware.py imported successfully")
    except Exception as e:
        errors.append(f"middleware.py import failed: {e}")
        print(f"  ✗ middleware.py import failed: {e}")
    
    try:
        from routes import auth_routes, operator_routes, citizen_routes
        print("  ✓ All route modules imported successfully")
    except Exception as e:
        errors.append(f"Route modules import failed: {e}")
        print(f"  ✗ Route modules import failed: {e}")
    
    # Check 2: Database schema
    print("\n2. Checking database schema...")
    try:
        import sqlite3
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        
        required_tables = [
            'users', 'sessions', 'intersections', 'traffic_signals',
            'appeals', 'wallet', 'wallet_transactions', 'audit_logs',
            'violations', 'fines', 'analysis_results'
        ]
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"  ✓ Table '{table}' exists")
            else:
                errors.append(f"Table '{table}' missing")
                print(f"  ✗ Table '{table}' missing")
        
        conn.close()
    except Exception as e:
        errors.append(f"Database check failed: {e}")
        print(f"  ✗ Database check failed: {e}")
    
    # Check 3: Static files
    print("\n3. Checking static files...")
    import os
    
    static_files = [
        'static/css/theme.css',
        'static/js/theme-utils.js'
    ]
    
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} exists")
        else:
            errors.append(f"Static file missing: {file_path}")
            print(f"  ✗ {file_path} missing")
    
    # Check 4: Templates
    print("\n4. Checking templates...")
    
    template_files = [
        'templates/login.html',
        'templates/error.html',
        'templates/index.html',
        'templates/dashboard.html'
    ]
    
    for file_path in template_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} exists")
        else:
            if file_path in ['templates/index.html', 'templates/dashboard.html']:
                warnings.append(f"Existing template: {file_path}")
                print(f"  ⚠ {file_path} (existing)")
            else:
                errors.append(f"Template missing: {file_path}")
                print(f"  ✗ {file_path} missing")
    
    # Check 5: Configuration files
    print("\n5. Checking configuration files...")
    
    config_files = [
        '.env.example',
        'requirements.txt',
        'PHASE1_README.md'
    ]
    
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} exists")
        else:
            warnings.append(f"Config file missing: {file_path}")
            print(f"  ⚠ {file_path} missing")
    
    # Check 6: Demo data
    print("\n6. Checking demo data...")
    try:
        import sqlite3
        conn = sqlite3.connect('database/violations.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'demo_%'")
        user_count = cursor.fetchone()[0]
        
        if user_count >= 8:
            print(f"  ✓ Demo users present: {user_count}")
        else:
            warnings.append(f"Insufficient demo users: {user_count} (expected 8)")
            print(f"  ⚠ Demo users: {user_count} (expected 8)")
        
        cursor.execute("SELECT COUNT(*) FROM intersections")
        intersection_count = cursor.fetchone()[0]
        
        if intersection_count >= 4:
            print(f"  ✓ Intersections present: {intersection_count}")
        else:
            warnings.append(f"Insufficient intersections: {intersection_count} (expected 4)")
            print(f"  ⚠ Intersections: {intersection_count} (expected 4)")
        
        conn.close()
    except Exception as e:
        warnings.append(f"Demo data check failed: {e}")
        print(f"  ⚠ Demo data check failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    if not errors and not warnings:
        print("✓ All checks passed! Phase 1 is ready.")
    else:
        if errors:
            print(f"\n✗ ERRORS ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
        
        if warnings:
            print(f"\n⚠ WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"  - {warning}")
    
    print("="*60)
    
    return len(errors) == 0

if __name__ == '__main__':
    success = validate_phase1()
    exit(0 if success else 1)
