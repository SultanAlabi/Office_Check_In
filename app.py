import os
import sqlite3
from datetime import datetime, timedelta
import traceback
from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    session, 
    send_file, 
    jsonify, 
    make_response,
    g,
    send_from_directory
)
import io
from io import BytesIO
import base64
from threading import Thread
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure random secret key

# Enable debug mode for development
app.debug = True

# Custom SQLite adapters and converters for Python 3.12 compatibility
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(val):
    try:
        return datetime.fromisoformat(val.decode())
    except (AttributeError, ValueError):
        return None

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# Configuration
class Config:
    # Database setup
    DATABASE_PATH = 'check_in_system.db'
    
    # File upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True only if using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Check-in configuration
    LATE_THRESHOLD = 9  # 9 AM
    WORK_HOURS = 8  # 8 hours per day
    BREAK_TYPES = {
        'short': 15,    # 15 minutes
        'regular': 30,  # 30 minutes
        'lunch': 60     # 1 hour
    }

# Apply configuration
app.config.from_object(Config)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_client_info():
    """Get basic client information with error handling"""
    try:
        user_agent = request.headers.get('User-Agent', '').lower()
        return {
            'ip_address': request.remote_addr,
            'browser': request.headers.get('User-Agent', 'Unknown'),
            'is_mobile': any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
        }
    except Exception as e:
        print(f"Error getting client info: {str(e)}")
        return {
            'ip_address': 'Unknown',
            'browser': 'Unknown',
            'is_mobile': False
        }

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        
        # Create staff table with indexes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_email ON staff(email)')
        
        # Create check_in_logs table with indexes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS check_in_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            date TEXT NOT NULL,
            is_late BOOLEAN DEFAULT FALSE,
            late_reason TEXT,
            total_break_time INTEGER DEFAULT 0,
            FOREIGN KEY (staff_id) REFERENCES staff (id)
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_check_in_logs_staff_date ON check_in_logs(staff_id, date)')
        
        # Create break_logs table with indexes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS break_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_in_log_id INTEGER NOT NULL,
            break_start TIMESTAMP NOT NULL,
            break_end TIMESTAMP,
            break_type TEXT NOT NULL,
            FOREIGN KEY (check_in_log_id) REFERENCES check_in_logs (id)
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_break_logs_check_in ON break_logs(check_in_log_id)')
        
        # Create simplified location_logs table with indexes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS location_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_in_log_id INTEGER NOT NULL,
            ip_address TEXT NOT NULL,
            browser TEXT,
            is_mobile BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (check_in_log_id) REFERENCES check_in_logs (id)
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_location_logs_check_in ON location_logs(check_in_log_id)')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except sqlite3.Error as e:
        print(f"Database initialization error: {str(e)}")
        raise

def get_db():
    """Get database connection with connection pooling"""
    if not hasattr(g, 'sqlite_db'):
        try:
            g.sqlite_db = sqlite3.connect(
                app.config['DATABASE_PATH'],
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            g.sqlite_db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Database connection error: {str(e)}")
            raise
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of request"""
    if hasattr(g, 'sqlite_db'):
        try:
            g.sqlite_db.close()
        except Exception as e:
            print(f"Error closing database: {str(e)}")

def cache_control(*directives):
    """Add Cache-Control header with given directives."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                response = make_response(view(*args, **kwargs))
                response.headers['Cache-Control'] = ', '.join(directives)
                return response
            except Exception as e:
                print(f"Cache control error: {str(e)}")
                return view(*args, **kwargs)
        return wrapped
    return decorator

@app.after_request
def add_cache_headers(response):
    """Add cache headers to static assets"""
    try:
        if request.path.startswith('/static'):
            response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    except Exception as e:
        print(f"Error adding cache headers: {str(e)}")
        return response

# Serve static files with caching
@app.route('/static/<path:filename>')
@cache_control('public', 'max-age=3600')
def serve_static(filename):
    """Serve static files with proper MIME types and caching"""
    try:
        return send_file(f'static/{filename}')
    except Exception as e:
        print(f"Error serving static file: {str(e)}")
        return '', 404

# Routes
@app.route('/')
def index():
    """Home page route"""
    if 'user_id' in session:
        # Detect device type
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
        
        # Redirect based on device type
        if is_mobile:
            return redirect(url_for('mobile_check_in'))
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route with error handling"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, role, password FROM staff WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_role'] = user['role']
                flash('Login successful!', 'success')
                
                # Detect device type and redirect
                user_agent = request.headers.get('User-Agent', '').lower()
                is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
                
                if is_mobile:
                    return redirect(url_for('mobile_check_in'))
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))
                
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            return redirect(url_for('login'))
        finally:
            if 'conn' in locals():
                conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route with session cleanup"""
    try:
        session.clear()
        flash('You have been logged out successfully', 'success')
    except Exception as e:
        flash(f'Error during logout: {str(e)}', 'error')
    
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Dashboard route"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_name = session['user_name']
    user_role = session['user_role']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user has checked in today
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT id, check_in_time, check_out_time, is_late, total_break_time FROM check_in_logs WHERE staff_id = ? AND date = ?', 
                  (user_id, today))
    log = cursor.fetchone()
    
    # Get attendance statistics
    # Last 5 days attendance
    cursor.execute('''
        SELECT 
            date,
            check_in_time,
            check_out_time,
            is_late,
            total_break_time
        FROM check_in_logs 
        WHERE staff_id = ? 
        ORDER BY date DESC 
        LIMIT 5
    ''', (user_id,))
    recent_logs = cursor.fetchall()
    
    # Calculate statistics
    total_days = len(recent_logs)
    on_time_days = sum(1 for log in recent_logs if not log[3])  # not late
    late_days = sum(1 for log in recent_logs if log[3])  # late
    avg_break_time = sum(log[4] or 0 for log in recent_logs) / total_days if total_days > 0 else 0
    
    # Get current break status
    active_break = None
    if log:
        cursor.execute('''
            SELECT break_start, break_type 
            FROM break_logs 
            WHERE check_in_log_id = ? AND break_end IS NULL
        ''', (log[0],))
        active_break = cursor.fetchone()
    
    # Get all staff for admin view
    staff_list = []
    late_check_ins = []
    if user_role == 'admin':
        cursor.execute('SELECT id, name, email, role FROM staff')
        staff_list = cursor.fetchall()
        
        # Get today's late check-ins for admin
        cursor.execute('''
            SELECT s.name, l.check_in_time 
            FROM check_in_logs l 
            JOIN staff s ON l.staff_id = s.id 
            WHERE l.date = ? AND l.is_late = 1
            ORDER BY l.check_in_time DESC
        ''', (today,))
        late_check_ins = cursor.fetchall()
    
    conn.close()
    
    # Calculate attendance percentages
    attendance_stats = {
        'on_time_percentage': (on_time_days / total_days * 100) if total_days > 0 else 0,
        'late_percentage': (late_days / total_days * 100) if total_days > 0 else 0,
        'avg_break_time': round(avg_break_time, 1),
        'total_days': total_days,
        'on_time_days': on_time_days,
        'late_days': late_days
    }
    
    return render_template('dashboard.html', 
                         user_name=user_name, 
                         user_role=user_role,
                         log=log,
                         today=today,
                         staff_list=staff_list,
                         is_late=log[3] if log else False,
                         late_check_ins=late_check_ins,
                         active_break=active_break,
                         attendance_stats=attendance_stats,
                         recent_logs=recent_logs)

@app.route('/check_in', methods=['POST'])
def check_in():
    """Check in route with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    staff_id_to_check_in = request.form.get('staff_id', session['user_id'])
    if session['user_role'] != 'admin':
        staff_id_to_check_in = session['user_id']
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    nine_am_today = now.replace(hour=9, minute=0, second=0, microsecond=0)
    is_late = now > nine_am_today
    late_reason = None
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check for existing check-in
        cursor.execute('''
            SELECT id FROM check_in_logs 
            WHERE staff_id = ? AND date = ?
        ''', (staff_id_to_check_in, today_str))
        existing_log = cursor.fetchone()
        
        if existing_log:
            flash('You\'ve already checked in today! 👍', 'info')
            return redirect(url_for('dashboard'))
        
        # Handle late check-in
        client_info = get_client_info()
        is_mobile = client_info['is_mobile']
        
        if is_late and is_mobile:
            late_reason = request.form.get('late_reason')
            if not late_reason:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'need_reason': True})
                return render_template('late_reason.html')
        
        # Insert check-in log
        cursor.execute('''
            INSERT INTO check_in_logs (staff_id, check_in_time, date, is_late, late_reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (staff_id_to_check_in, now, today_str, is_late, late_reason))
        check_in_log_id = cursor.lastrowid
        
        # Insert location log
        cursor.execute('''
            INSERT INTO location_logs (check_in_log_id, ip_address, browser, is_mobile)
            VALUES (?, ?, ?, ?)
        ''', (
            check_in_log_id,
            client_info['ip_address'],
            client_info['browser'],
            client_info['is_mobile']
        ))
        
        # Get staff info for message
        cursor.execute('SELECT name, email FROM staff WHERE id = ?', (staff_id_to_check_in,))
        staff_info = cursor.fetchone()
        staff_name = staff_info['name']
        
        conn.commit()
        
        if is_late:
            if is_mobile:
                flash(f'Better late than never! Thanks for providing a reason. You checked in at {now.strftime("%H:%M")} ⏰', 'warning')
            else:
                flash(f'Late check-in recorded at {now.strftime("%H:%M")} ⏰', 'warning')
        else:
            flash(f'Great start to the day! You\'re right on time! 🌟', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('mobile_check_in' if is_mobile else 'dashboard'))

@app.route('/submit_late_reason', methods=['POST'])
def submit_late_reason():
    """Submit late check-in reason with error handling (mobile only)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if request is from mobile
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
    
    if not is_mobile:
        flash('Late reason submission is only available on mobile devices', 'warning')
        return redirect(url_for('dashboard'))
    
    staff_id = session['user_id']
    late_reason = request.form.get('late_reason')
    today_str = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check for existing check-in
        cursor.execute('''
            SELECT id FROM check_in_logs 
            WHERE staff_id = ? AND date = ?
        ''', (staff_id, today_str))
        existing_log = cursor.fetchone()
        
        if existing_log:
            flash('You\'ve already checked in today!', 'info')
            return redirect(url_for('mobile_check_in'))
        
        # Insert check-in log with late reason
        cursor.execute('''
            INSERT INTO check_in_logs (
                staff_id, check_in_time, date, is_late, late_reason
            ) VALUES (?, ?, ?, ?, ?)
        ''', (staff_id, now, today_str, True, late_reason))
        check_in_log_id = cursor.lastrowid
        
        # Insert location log
        client_info = get_client_info()
        cursor.execute('''
            INSERT INTO location_logs (
                check_in_log_id, ip_address, browser, is_mobile
            ) VALUES (?, ?, ?, ?)
        ''', (
            check_in_log_id,
            client_info['ip_address'],
            client_info['browser'],
            client_info['is_mobile']
        ))
        
        conn.commit()
        flash('Check-in completed with late reason recorded. Thank you for the explanation! 👍', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('mobile_check_in'))

@app.route('/check_out', methods=['POST'])
def check_out():
    """Check out route with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    staff_id_to_check_out = request.form.get('staff_id', session['user_id'])
    if session['user_role'] != 'admin':
        staff_id_to_check_out = session['user_id']
    
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get check-in record
        cursor.execute('''
            SELECT id, check_out_time 
            FROM check_in_logs 
            WHERE staff_id = ? AND date = ?
        ''', (staff_id_to_check_out, today))
        log = cursor.fetchone()
        
        if not log:
            flash('Don\'t forget to check in first! 😊', 'info')
        elif log['check_out_time'] is not None:
            flash('You\'ve already checked out. See you tomorrow! 👋', 'info')
        else:
            # End any active breaks
            cursor.execute('''
                UPDATE break_logs 
                SET break_end = ? 
                WHERE check_in_log_id = ? AND break_end IS NULL
            ''', (now, log['id']))
            
            # Update check-out time
            cursor.execute('''
                UPDATE check_in_logs 
                SET check_out_time = ? 
                WHERE id = ?
            ''', (now, log['id']))
            
            conn.commit()
            flash('Great job today! Have a wonderful evening! 🌟', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new staff route with error handling"""
    is_admin = 'user_id' in session and session['user_role'] == 'admin'
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Only admins can create other admin accounts
        role = request.form['role'] if is_admin else 'staff'
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO staff (name, email, password, role, created_at) 
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (name, email, hashed_password, role))
            conn.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
        finally:
            if 'conn' in locals():
                conn.close()
        
        if is_admin:
            return redirect(url_for('dashboard'))
        return redirect(url_for('register'))
    
    return render_template('register.html', is_admin=is_admin)

@app.route('/reports')
def reports():
    """View reports route with error handling (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get date filter from query params
        date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get all logs for the selected date with break information
        cursor.execute('''
            SELECT 
                l.id,
                s.name,
                l.check_in_time,
                l.check_out_time,
                s.id as staff_id,
                (
                    SELECT COUNT(*)
                    FROM break_logs b
                    WHERE b.check_in_log_id = l.id
                    AND b.break_end IS NULL
                ) > 0 as is_on_break,
                (
                    SELECT break_start
                    FROM break_logs b
                    WHERE b.check_in_log_id = l.id
                    AND b.break_end IS NULL
                    LIMIT 1
                ) as break_start,
                (
                    SELECT break_type
                    FROM break_logs b
                    WHERE b.check_in_log_id = l.id
                    AND b.break_end IS NULL
                    LIMIT 1
                ) as break_type,
                l.is_late,
                l.late_reason,
                l.total_break_time
            FROM check_in_logs l 
            JOIN staff s ON l.staff_id = s.id 
            WHERE l.date = ?
            ORDER BY l.check_in_time
        ''', (date_filter,))
        
        logs = cursor.fetchall()
        
        # Calculate durations for each log
        durations = []
        for log in logs:
            check_in = log['check_in_time']
            check_out = log['check_out_time']
            if check_in and check_out:
                try:
                    check_in_dt = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S.%f') if '.' in check_in else datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
                    check_out_dt = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S.%f') if '.' in check_out else datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')
                    duration = check_out_dt - check_in_dt
                    durations.append(str(duration))
                except (ValueError, TypeError):
                    durations.append('N/A')
            else:
                durations.append('N/A')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        logs = []
        durations = []
    finally:
        if 'conn' in locals():
            conn.close()
    
    return render_template('reports.html', 
                         logs=logs, 
                         selected_date=date_filter, 
                         durations=durations)

@app.route('/delete_log/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    """Delete a check-in log with error handling (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the date of the log to redirect back to the correct report page
        cursor.execute('SELECT date FROM check_in_logs WHERE id = ?', (log_id,))
        log_date = cursor.fetchone()
        
        if log_date:
            # Delete related records first
            cursor.execute('DELETE FROM location_logs WHERE check_in_log_id = ?', (log_id,))
            cursor.execute('DELETE FROM break_logs WHERE check_in_log_id = ?', (log_id,))
            
            # Delete the log
            cursor.execute('DELETE FROM check_in_logs WHERE id = ?', (log_id,))
            conn.commit()
            
            # Reset the sequence for the check_in_logs table
            reset_table_sequence('check_in_logs')
            
            flash('Check-in log deleted successfully', 'success')
            date_to_redirect = log_date['date']
        else:
            flash('Log not found', 'error')
            date_to_redirect = datetime.now().strftime('%Y-%m-%d')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        date_to_redirect = datetime.now().strftime('%Y-%m-%d')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('reports', date=date_to_redirect))

def reset_table_sequence(table_name):
    """Reset the SQLite autoincrement sequence for a table with error handling"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the maximum ID from the table
        cursor.execute(f"SELECT MAX(id) as max_id FROM {table_name}")
        result = cursor.fetchone()
        max_id = result['max_id'] if result else 0
        
        # Reset the sequence
        cursor.execute(
            "UPDATE sqlite_sequence SET seq = ? WHERE name = ?",
            (max_id or 0, table_name)
        )
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Error resetting sequence for {table_name}: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/delete_staff/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    """Delete a staff member with error handling (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    # Prevent deleting yourself
    if staff_id == session['user_id']:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all check-in logs for this staff member
        cursor.execute('SELECT id FROM check_in_logs WHERE staff_id = ?', (staff_id,))
        log_ids = [row['id'] for row in cursor.fetchall()]
        
        # Delete related records first
        for log_id in log_ids:
            cursor.execute('DELETE FROM location_logs WHERE check_in_log_id = ?', (log_id,))
            cursor.execute('DELETE FROM break_logs WHERE check_in_log_id = ?', (log_id,))
        
        # Delete check-in logs
        cursor.execute('DELETE FROM check_in_logs WHERE staff_id = ?', (staff_id,))
        
        # Finally, delete the staff member
        cursor.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
        
        conn.commit()
        
        # Reset sequences
        reset_table_sequence('staff')
        reset_table_sequence('check_in_logs')
        reset_table_sequence('break_logs')
        reset_table_sequence('location_logs')
        
        flash('Staff member and all associated records deleted successfully', 'success')
        
    except sqlite3.Error as e:
        flash(f'Error deleting staff member: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    return redirect(url_for('dashboard'))

def create_admin_if_not_exists():
    """Create a default admin user if none exists"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM staff WHERE role = "admin"')
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Use a simple default password: Admin@123
            default_password = 'Admin@123'
            hashed_password = generate_password_hash(default_password, method='pbkdf2:sha256')
            
            cursor.execute('''
                INSERT INTO staff (name, email, password, role, created_at) 
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', ('Admin User', 'admin@example.com', hashed_password, 'admin'))
            conn.commit()
            
            print('\n' + '='*50)
            print('ADMIN USER CREATED!')
            print('='*50)
            print('Email: admin@example.com')
            print('Default Password: Admin@123')
            print('IMPORTANT: Please change this password after logging in!')
            print('='*50 + '\n')
        
        conn.close()
    except sqlite3.Error as e:
        print(f'Error creating admin user: {str(e)}')
        raise

@app.route('/export_report')
def export_report():
    """Export report to CSV with error handling (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    selected_date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        return redirect(url_for('reports'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                s.name,
                l.check_in_time,
                l.check_out_time,
                l.date,
                l.is_late,
                l.late_reason,
                l.total_break_time
            FROM check_in_logs l
            JOIN staff s ON l.staff_id = s.id
            WHERE l.date = ?
            ORDER BY l.check_in_time
        ''', (selected_date_str,))
        
        logs = cursor.fetchall()
        
        if not logs:
            flash(f'No data to export for {selected_date_str}.', 'info')
            return redirect(url_for('reports', date=selected_date_str))
        
        # Create CSV in memory
        output = io.StringIO()
        output.write('Staff Name,Check-In Time,Check-Out Time,Duration,Status,Late,Break Time (min),Date\n')
        
        for log in logs:
            # Safely parse check-in time
            try:
                check_in_time = datetime.strptime(log['check_in_time'], '%Y-%m-%d %H:%M:%S.%f') if log['check_in_time'] and '.' in log['check_in_time'] else \
                               datetime.strptime(log['check_in_time'], '%Y-%m-%d %H:%M:%S') if log['check_in_time'] else None
            except (ValueError, TypeError):
                check_in_time = None
            
            # Safely parse check-out time
            try:
                check_out_time = datetime.strptime(log['check_out_time'], '%Y-%m-%d %H:%M:%S.%f') if log['check_out_time'] and '.' in log['check_out_time'] else \
                                datetime.strptime(log['check_out_time'], '%Y-%m-%d %H:%M:%S') if log['check_out_time'] else None
            except (ValueError, TypeError):
                check_out_time = None
            
            # Calculate duration and status
            duration_str = "N/A"
            status_str = "In Progress"
            
            if check_in_time and check_out_time:
                duration = check_out_time - check_in_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{int(hours)}h {int(minutes)}m"
                status_str = "Completed"
            elif check_in_time:
                status_str = "Checked In"
            
            # Format times for CSV
            check_in_str = check_in_time.strftime("%H:%M:%S") if check_in_time else "N/A"
            check_out_str = check_out_time.strftime("%H:%M:%S") if check_out_time else "N/A"
            
            # Write row to CSV
            output.write(f'{log["name"]},{check_in_str},{check_out_str},{duration_str},'
                       f'{status_str},{"Yes" if log["is_late"] else "No"},'
                       f'{log["total_break_time"] or 0},{log["date"]}\n')
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'check_in_report_{selected_date_str}.csv'
        )
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('reports', date=selected_date_str))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/mobile_check_in')
def mobile_check_in():
    """Mobile-friendly check-in page with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_name = session['user_name']
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get today's check-in status
        cursor.execute('''
            SELECT 
                l.id,
                l.staff_id,
                l.check_in_time,
                l.check_out_time,
                l.is_late,
                l.late_reason,
                l.total_break_time
            FROM check_in_logs l 
            WHERE l.staff_id = ? AND l.date = ?
        ''', (user_id, today))
        log = cursor.fetchone()
        
        # Get current break status if checked in
        active_break = None
        if log:
            cursor.execute('''
                SELECT 
                    break_start,
                    break_type,
                    ROUND((strftime('%s', 'now') - strftime('%s', break_start)) / 60.0) as duration
                FROM break_logs 
                WHERE check_in_log_id = ? AND break_end IS NULL
            ''', (log['id'],))
            active_break = cursor.fetchone()
        
    except sqlite3.Error as e:
        logger.error(f'Database error: {str(e)}')
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if 'conn' in locals():
            conn.close()
    
    return render_template('mobile_check_in.html',
                         user_name=user_name,
                         log=log,
                         today=today,
                         active_break=active_break)

@app.route('/start_break', methods=['POST'])
def start_break():
    """Start a break with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    staff_id = session['user_id']
    break_type = request.form.get('break_type', 'regular')
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get today's check-in log
        cursor.execute('''
            SELECT id FROM check_in_logs 
            WHERE staff_id = ? AND date = ?
        ''', (staff_id, today))
        check_in_log = cursor.fetchone()
        
        if not check_in_log:
            flash('You need to check in first! 😊', 'warning')
            return redirect(url_for('dashboard'))
        
        # Check for active break
        cursor.execute('''
            SELECT id FROM break_logs 
            WHERE check_in_log_id = ? AND break_end IS NULL
        ''', (check_in_log['id'],))
        active_break = cursor.fetchone()
        
        if active_break:
            flash('You already have an active break! ⏸️', 'warning')
        else:
            cursor.execute('''
                INSERT INTO break_logs (check_in_log_id, break_start, break_type)
                VALUES (?, ?, ?)
            ''', (check_in_log['id'], now, break_type))
            conn.commit()
            flash('Break started! Take your time 🌟', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    # Detect device type
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
    
    return redirect(url_for('mobile_check_in' if is_mobile else 'dashboard'))

@app.route('/end_break', methods=['POST'])
def end_break():
    """End break with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    staff_id = session['user_id']
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get check-in record
        cursor.execute('''
            SELECT id FROM check_in_logs 
            WHERE staff_id = ? AND date = ?
        ''', (staff_id, today))
        check_in_log = cursor.fetchone()
        
        if check_in_log:
            # Find active break
            cursor.execute('''
                SELECT id, break_start, break_type FROM break_logs 
                WHERE check_in_log_id = ? AND break_end IS NULL
            ''', (check_in_log['id'],))
            active_break = cursor.fetchone()
            
            if active_break:
                # Calculate break duration - break_start is now a datetime object
                break_start = active_break['break_start']
                break_duration = int((now - break_start).total_seconds() / 60)
                
                # Update break log
                cursor.execute('''
                    UPDATE break_logs 
                    SET break_end = ? 
                    WHERE id = ?
                ''', (now, active_break['id']))
                
                # Update total break time
                cursor.execute('''
                    UPDATE check_in_logs 
                    SET total_break_time = total_break_time + ?
                    WHERE id = ?
                ''', (break_duration, check_in_log['id']))
                
                conn.commit()
                
                # Get break type for message
                break_type = active_break['break_type'].capitalize()
                flash(f'{break_type} break ended! Duration: {break_duration} minutes ⏰', 'success')
            else:
                flash('No active break found! 🤔', 'warning')
        else:
            flash('No check-in record found for today! 📝', 'warning')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    except Exception as e:
        logger.error(f"Error ending break: {str(e)}")
        flash('An error occurred while ending the break', 'error')
    finally:
        if 'conn' in locals():
            conn.close()
    
    # Detect device type
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
    
    return redirect(url_for('mobile_check_in' if is_mobile else 'dashboard'))

@app.route('/location_history')
def location_history():
    """View location history with error handling (admin only)"""
    if 'user_id' not in session or session['user_role'] != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get date filter from query params
        date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get all location logs for the selected date with simplified structure
        cursor.execute('''
            SELECT 
                s.name,
                l.check_in_time,
                loc.ip_address,
                loc.browser,
                loc.is_mobile,
                loc.created_at
            FROM location_logs loc
            JOIN check_in_logs l ON loc.check_in_log_id = l.id
            JOIN staff s ON l.staff_id = s.id
            WHERE l.date = ?
            ORDER BY l.check_in_time DESC
        ''', (date_filter,))
        
        location_logs = cursor.fetchall()
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        location_logs = []
    finally:
        if 'conn' in locals():
            conn.close()
    
    return render_template('location_history.html', 
                         logs=location_logs, 
                         selected_date=date_filter)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    """Change password route with error handling"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Verify current password
            cursor.execute('SELECT password FROM staff WHERE id = ?', (session['user_id'],))
            current_hash = cursor.fetchone()['password']
            
            if not check_password_hash(current_hash, current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('change_password'))
            
            # Update password
            new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            cursor.execute('''
                UPDATE staff 
                SET password = ? 
                WHERE id = ?
            ''', (new_hash, session['user_id']))
            
            conn.commit()
            flash('Password updated successfully! 🔐', 'success')
            return redirect(url_for('dashboard'))
        
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'danger')
        finally:
            if 'conn' in locals():
                conn.close()
    
    return render_template('change_password.html')

@app.route('/favicon.ico')
def favicon():
    try:
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.html',
            mimetype='text/html'
        )
    except Exception as e:
        print(f"Error serving favicon: {str(e)}")
        return '', 204  # Return empty response if favicon not found

# Ensure templates directory is properly set
app.template_folder = os.path.join(app.root_path, 'templates')

# Error handlers with proper template paths and logging
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 Error: {error}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {error}")
    # Log the full traceback
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled Exception: {error}")
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database and create admin user
    try:
        with app.app_context():
            init_db()
            create_admin_if_not_exists()
    except Exception as e:
        print(f"Startup error: {str(e)}")
        exit(1)
    
    # Run the app with default Flask development server
    app.run(host='0.0.0.0', port=8080, debug=True)