import sqlite3
import os
from datetime import datetime

def test_database():
    print("Testing Database...")
    try:
        conn = sqlite3.connect('check_in_system.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables found:", [table[0] for table in tables])
        
        # Check admin user
        cursor.execute("SELECT * FROM staff WHERE role='admin';")
        admin = cursor.fetchone()
        print("Admin user exists:", bool(admin))
        
        # Check table structures
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table[0]});")
            columns = cursor.fetchall()
            print(f"\n{table[0]} columns:", [col[1] for col in columns])
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"Records in {table[0]}: {count}")
        
        conn.close()
        print("\nDatabase test completed successfully!")
        return True
    except Exception as e:
        print(f"Database test failed: {str(e)}")
        return False

def test_file_structure():
    print("\nTesting File Structure...")
    required_files = [
        'app.py',
        'templates/base.html',
        'templates/login.html',
        'templates/dashboard.html',
        'templates/404.html',
        'templates/500.html',
        'static/uploads'
    ]
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        print(f"{file_path}: {'✓' if exists else '✗'}")
    
    return all(os.path.exists(f) for f in required_files)

if __name__ == '__main__':
    print("=== Check-In System Feature Test ===\n")
    
    db_ok = test_database()
    files_ok = test_file_structure()
    
    print("\n=== Test Summary ===")
    print(f"Database Status: {'✓' if db_ok else '✗'}")
    print(f"File Structure: {'✓' if files_ok else '✗'}")
    
    if db_ok and files_ok:
        print("\nAll basic checks passed! The application structure appears to be correct.")
        print("\nNext steps for manual testing:")
        print("1. Login with admin credentials (admin@example.com / Admin@123)")
        print("2. Test check-in/check-out functionality")
        print("3. Test break management")
        print("4. Test reports generation")
        print("5. Test user management")
    else:
        print("\nSome checks failed. Please review the output above for details.") 