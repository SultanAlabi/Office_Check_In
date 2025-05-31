# Office Check-In System

A modern, secure, and mobile-friendly attendance tracking system built with Flask for managing staff arrivals and departures in an office environment.

## Features

### Core Features
- Secure user authentication with password hashing
- Automatic device type detection and redirection
- QR code-based check-in
- Break time management with multiple break types
- Real-time attendance reporting and analytics

### Mobile Features
- Responsive mobile interface
- Quick break controls (15min, 30min, 1hour)
- Late check-in reason submission
- Offline support with automatic sync
- Touch-optimized UI elements

### Admin Features
- Real-time attendance dashboard
- Dynamic attendance statistics
- Advanced filtering and search
- CSV report export
- Staff management tools
- Break time monitoring
- Simplified location history tracking
- User-friendly device type indicators

### Security Features
- Password hashing using Werkzeug
- Secure session management
- CSRF protection
- Protected admin routes
- Simple default admin credentials

## Project Structure
```
check-in-system/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS)
│   ├── css/          # CSS stylesheets
│   ├── js/           # JavaScript files
│   └── sw.js         # Service Worker for offline support
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── login.html    # Login page
│   ├── reports.html  # Reports dashboard
│   └── mobile_check_in.html  # Mobile interface
└── check_in_system.db # SQLite database
```

## Requirements

- Python 3.6 or higher
- Flask
- SQLite3 (included with Python)
- Modern web browser with JavaScript enabled
- Internet connection (offline mode available for basic functions)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Initial Setup

### Default Admin Account
The system creates a default admin account on first run:
- Email: admin@example.com
- Password: Admin@123

**IMPORTANT**: Change this password immediately after first login!

### Starting the Application
```bash
python app.py
```
The server will start on http://127.0.0.1:5000

## Usage

### Staff Members
1. Register using the registration form
2. Log in with email and password
3. System automatically detects device type:
   - Desktop users see the full dashboard
   - Mobile users get the mobile-optimized interface
4. Check in/out using the dashboard
5. Manage breaks with quick controls
6. Submit late check-in reasons when needed

### Administrators
1. Access admin dashboard using default credentials
2. View real-time attendance statistics
3. Generate and export reports
4. Monitor staff locations and devices:
   - Track check-in locations
   - See device types (mobile/desktop)
   - View browser information
   - Monitor IP addresses
5. Manage staff members
6. View break durations
7. Access location history with improved filtering

## Recent Updates

### Location History Improvements
- Improved table layout and responsiveness
- Better device type indicators with icons
- Enhanced IP address display
- Truncated browser information for clarity
- Added "No data found" messages
- Improved date selection interface

### Security Updates
- Simplified admin password system
- Enhanced password change prompts
- Improved session management
- Better error handling
- Secure default credentials

### Technical Improvements
- Enhanced offline functionality
- Improved service worker caching
- Better mobile device detection
- Optimized database queries
- Enhanced error handling
- Improved form validation

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (Chrome for Android, Safari for iOS)

## Security Notes

1. Change the default admin password after first login
2. All passwords are securely hashed
3. Session management is handled securely
4. Database queries are protected against SQL injection
5. CSRF protection is enabled

## Support

For support or questions, please open an issue in the repository or contact the system administrator.

## License

MIT License - Feel free to use this project for your organization.
