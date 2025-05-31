import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key in production

# Database setup
DATABASE_PATH = 'check_in_system.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create staff table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    
    # Create check_in_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_in_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER NOT NULL,
        check_in_time TIMESTAMP,
        check_out_time TIMESTAMP,
        date TEXT NOT NULL,
        FOREIGN KEY (staff_id) REFERENCES staff (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    """Home page route"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, role, password FROM staff WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[3] == password:  # In production, use proper password hashing
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[2]
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Dashboard route"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_name = session['user_name']
    user_role = session['user_role']
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if user has checked in today
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT id, check_in_time, check_out_time FROM check_in_logs WHERE staff_id = ? AND date = ?', 
                  (user_id, today))
    log = cursor.fetchone()
    
    # Get all staff for admin view
    staff_list = []
    if user_role == 'admin':
        cursor.execute('SELECT id, name, email, role FROM staff')
        staff_list = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                          user_name=user_name, 
                          user_role=user_role,
                          log=log,
                          today=today,
                          staff_list=staff_list)

@app.route('/check_in', methods=['POST'])
def check_in():
    """Check in route"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if already checked in today
    cursor.execute('SELECT id FROM check_in_logs WHERE staff_id = ? AND date = ?', (user_id, today))
    existing_log = cursor.fetchone()
    
    if existing_log:
        flash('You have already checked in today')
    else:
        cursor.execute('INSERT INTO check_in_logs (staff_id, check_in_time, date) VALUES (?, ?, ?)',
                      (user_id, now, today))
        conn.commit()
        flash('Check-in successful!')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/check_out', methods=['POST'])
def check_out():
    """Check out route"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Find today's log
    cursor.execute('SELECT id, check_out_time FROM check_in_logs WHERE staff_id = ? AND date = ?', 
                  (user_id, today))
    log = cursor.fetchone()
    
    if not log:
        flash('You need to check in first')
    elif log[1] is not None:
        flash('You have already checked out today')
    else:
        cursor.execute('UPDATE check_in_logs SET check_out_time = ? WHERE id = ?', (now, log[0]))
        conn.commit()
        flash('Check-out successful!')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new staff route (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']  # In production, hash this password
        role = request.form['role']
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO staff (name, email, password, role) VALUES (?, ?, ?, ?)',
                          (name, email, password, role))
            conn.commit()
            flash('Staff registered successfully!')
        except sqlite3.IntegrityError:
            flash('Email already exists')
        finally:
            conn.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/reports')
def reports():
    """View reports route (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get date filter from query params
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get all logs for the selected date
    cursor.execute('''
    SELECT l.id, s.name, l.check_in_time, l.check_out_time, s.id 
    FROM check_in_logs l 
    JOIN staff s ON l.staff_id = s.id 
    WHERE l.date = ?
    ORDER BY l.check_in_time
    ''', (date_filter,))
    
    logs = cursor.fetchall()
    conn.close()
    
    # Calculate durations for each log
    durations = []
    for log in logs:
        check_in = log[2]
        check_out = log[3]
        if check_in and check_out:
            try:
                check_in_dt = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S.%f') if '.' in check_in else datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
                check_out_dt = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S.%f') if '.' in check_out else datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')
                duration = check_out_dt - check_in_dt
                durations.append(str(duration))
            except Exception:
                durations.append('N/A')
        else:
            durations.append('N/A')
    return render_template('reports.html', logs=logs, selected_date=date_filter, durations=durations)

@app.route('/delete_log/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    """Delete a check-in log (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get the date of the log to redirect back to the correct report page
    cursor.execute('SELECT date FROM check_in_logs WHERE id = ?', (log_id,))
    log_date = cursor.fetchone()
    
    if log_date:
        # Delete the log
        cursor.execute('DELETE FROM check_in_logs WHERE id = ?', (log_id,))
        conn.commit()
        
        # Reset the sequence for the check_in_logs table
        reset_table_sequence('check_in_logs')
        
        flash('Check-in log deleted successfully')
        date_to_redirect = log_date[0]
    else:
        flash('Log not found')
        date_to_redirect = datetime.now().strftime('%Y-%m-%d')
    
    conn.close()
    return redirect(url_for('reports', date=date_to_redirect))

def reset_table_sequence(table_name):
    """Reset the SQLite autoincrement sequence for a table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get the maximum ID from the table
        cursor.execute(f"SELECT MAX(id) FROM {table_name}")
        max_id = cursor.fetchone()[0]
        
        # If there are no records, set sequence to 0, otherwise to the max ID
        reset_to = 0 if max_id is None else max_id
        
        # Reset the sequence
        cursor.execute(f"UPDATE sqlite_sequence SET seq = ? WHERE name = ?", (reset_to, table_name))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error resetting sequence for {table_name}: {str(e)}")
    finally:
        conn.close()

@app.route('/delete_staff/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    """Delete a staff member (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    # Prevent deleting yourself
    if staff_id == session['user_id']:
        flash('You cannot delete your own account')
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First delete all check-in logs for this staff member
        cursor.execute('DELETE FROM check_in_logs WHERE staff_id = ?', (staff_id,))
        
        # Then delete the staff member
        cursor.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
        
        conn.commit()
        
        # Reset the sequence for the staff table
        reset_table_sequence('staff')
        
        flash('Staff member and all associated logs deleted successfully')
    except sqlite3.Error as e:
        flash(f'Error deleting staff member: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

# Create a basic admin user if none exists
def create_admin_if_not_exists():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM staff WHERE role = "admin"')
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        cursor.execute('INSERT INTO staff (name, email, password, role) VALUES (?, ?, ?, ?)',
                      ('Admin User', 'admin@example.com', 'admin123', 'admin'))
        conn.commit()
        print('Admin user created with email: admin@example.com and password: admin123')
    
    conn.close()

if __name__ == '__main__':
    # Make sure the templates and static folders exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Initialize database
    init_db()
    create_admin_if_not_exists()
    
    # Run the app
    app.run(debug=True)