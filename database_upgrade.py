"""
Database Schema Upgrade Script
Adds new tables and extends existing ones for Phase 1
"""

import sqlite3
from datetime import datetime

def upgrade_database():
    """Upgrade database schema with new tables and columns"""
    conn = sqlite3.connect('database/violations.db')
    cursor = conn.cursor()
    
    print("Starting database upgrade...")
    
    # 1. Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('operator', 'citizen')),
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            profile_data TEXT
        )
    ''')
    print("✓ Created users table")
    
    # 2. Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("✓ Created sessions table")
    
    # 3. Create intersections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intersections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            mode TEXT DEFAULT 'auto' CHECK(mode IN ('auto', 'manual')),
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'warning', 'offline')),
            ns_cycle TEXT,
            ew_cycle TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created intersections table")
    
    # 4. Create traffic_signals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intersection_id INTEGER NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('NS', 'EW')),
            current_state TEXT DEFAULT 'red' CHECK(current_state IN ('green', 'red', 'amber')),
            remaining_seconds INTEGER DEFAULT 0,
            total_cycle_time INTEGER DEFAULT 60,
            last_override_by INTEGER,
            last_override_at TEXT,
            predictive_mode INTEGER DEFAULT 0,
            FOREIGN KEY (intersection_id) REFERENCES intersections (id),
            FOREIGN KEY (last_override_by) REFERENCES users (id)
        )
    ''')
    print("✓ Created traffic_signals table")
    
    # 5. Create appeals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appeals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            reason TEXT NOT NULL,
            operator_comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            FOREIGN KEY (violation_id) REFERENCES violations (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("✓ Created appeals table")
    
    # 6. Create wallet table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            balance REAL DEFAULT 0.0,
            total_paid REAL DEFAULT 0.0,
            total_credits REAL DEFAULT 0.0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("✓ Created wallet table")
    
    # 7. Create wallet_transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('credit', 'debit')),
            amount REAL NOT NULL,
            description TEXT,
            violation_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallet (id),
            FOREIGN KEY (violation_id) REFERENCES violations (id)
        )
    ''')
    print("✓ Created wallet_transactions table")
    
    # 8. Create audit_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    print("✓ Created audit_logs table")
    
    # 9. Add new columns to violations table
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN operator_id INTEGER')
        print("✓ Added operator_id to violations")
    except sqlite3.OperationalError:
        print("  - operator_id already exists")
    
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN intersection_id INTEGER')
        print("✓ Added intersection_id to violations")
    except sqlite3.OperationalError:
        print("  - intersection_id already exists")
    
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN camera_id TEXT')
        print("✓ Added camera_id to violations")
    except sqlite3.OperationalError:
        print("  - camera_id already exists")
    
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN challenge_reason TEXT')
        print("✓ Added challenge_reason to violations")
    except sqlite3.OperationalError:
        print("  - challenge_reason already exists")
    
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN is_challenged INTEGER DEFAULT 0')
        print("✓ Added is_challenged to violations")
    except sqlite3.OperationalError:
        print("  - is_challenged already exists")
    
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN paid_at TEXT')
        print("✓ Added paid_at to violations")
    except sqlite3.OperationalError:
        print("  - paid_at already exists")
    
    try:
        cursor.execute('ALTER TABLE violations ADD COLUMN wallet_payment INTEGER DEFAULT 0')
        print("✓ Added wallet_payment to violations")
    except sqlite3.OperationalError:
        print("  - wallet_payment already exists")
    
    # 10. Add new columns to fines table
    try:
        cursor.execute('ALTER TABLE fines ADD COLUMN qr_code_path TEXT')
        print("✓ Added qr_code_path to fines")
    except sqlite3.OperationalError:
        print("  - qr_code_path already exists")
    
    try:
        cursor.execute('ALTER TABLE fines ADD COLUMN challan_pdf_path TEXT')
        print("✓ Added challan_pdf_path to fines")
    except sqlite3.OperationalError:
        print("  - challan_pdf_path already exists")
    
    try:
        cursor.execute('ALTER TABLE fines ADD COLUMN appeal_id INTEGER')
        print("✓ Added appeal_id to fines")
    except sqlite3.OperationalError:
        print("  - appeal_id already exists")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Database upgrade completed successfully!")

if __name__ == '__main__':
    upgrade_database()
