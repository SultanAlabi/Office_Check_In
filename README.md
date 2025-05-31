# Office Check-In System

A modern, responsive web application for managing employee check-ins, breaks, and attendance tracking. Built with Flask and featuring a beautiful dark/light mode interface.

![Check-In System](static/preview.png)

## Features

### User Management
- 🔐 Secure authentication system
- 👥 Role-based access control (Admin/Staff)
- 🔄 Password management with secure hashing
- 📝 User registration with email verification

### Check-In Features
- ⏰ Easy check-in/check-out functionality
- ⚡ Real-time status updates
- 🕒 Break time management (Short/Regular/Lunch breaks)
- 📍 Location tracking for check-ins
- 📱 Mobile-friendly interface

### Admin Features
- 📊 Comprehensive reporting system
- 👥 Staff management dashboard
- 📍 Location history tracking
- 📈 Attendance statistics
- 🔍 Advanced filtering and search

### UI/UX Features
- 🌓 Dark/Light mode support
- 📱 Responsive design for all devices
- ⚡ Interactive animations and transitions
- 🎨 Modern, clean interface
- 💫 Smooth micro-interactions

### Technical Features
- 🔒 Secure password hashing
- 💾 SQLite database with connection pooling
- 🌐 Network status monitoring
- 📶 Offline support capabilities
- 🔄 Auto-refresh functionality

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **CSS Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons
- **Security**: Werkzeug Security

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Check_In_System.git
cd Check_In_System
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

5. Access the application:
- Open your browser and navigate to `http://localhost:8080`
- Default admin credentials:
  * Email: admin@example.com
  * Password: Admin@123

## Configuration

The application can be configured through the following environment variables:

- `FLASK_ENV`: Set to 'development' or 'production'
- `SECRET_KEY`: Flask secret key for session management
- `DATABASE_PATH`: Path to SQLite database file
- `HOST`: Host address (default: 0.0.0.0)
- `PORT`: Port number (default: 8080)

## Usage

### Staff Members
1. Register a new account or log in with existing credentials
2. Use the check-in/check-out buttons to record attendance
3. Manage breaks through the dashboard
4. View personal attendance history and statistics

### Administrators
1. Log in with admin credentials
2. Access the admin dashboard to manage staff
3. View comprehensive reports and statistics
4. Monitor location history and attendance patterns

## Development

### Project Structure
```
Check_In_System/
├── app.py              # Main application file
├── templates/          # HTML templates
├── static/            # Static files (CSS, JS, images)
├── instance/         # Instance-specific files
└── requirements.txt  # Python dependencies
```

### Contributing
1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## Security

- Passwords are hashed using Werkzeug's security functions
- Session management with secure cookie handling
- CSRF protection enabled
- Input validation and sanitization
- Secure password reset functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask framework and its contributors
- Bootstrap team for the excellent UI framework
- All contributors and users of the system

## Support

For support, please open an issue in the GitHub repository or contact the development team.

---

Made with ❤️ by Alabi Abdulhameed Ayomikun

