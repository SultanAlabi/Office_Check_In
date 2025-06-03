# Check-In System

A modern web-based check-in system built with Flask for managing employee attendance, breaks, and work hours.

## Features

- 🔐 Secure user authentication and role-based access control
- ⏰ Daily check-in/check-out tracking
- ⏸️ Break management (short breaks, regular breaks, lunch breaks)
- 📱 Mobile-friendly interface
- 📊 Attendance reports and analytics
- 📍 Location tracking for check-ins
- 👥 Admin dashboard for user management
- 📄 CSV export functionality for reports

## Prerequisites

- Python 3.8 or higher
- SQLite3
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Check_In_System.git
cd Check_In_System
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The server will start at `http://localhost:8080`

## Default Admin Account

After first run, use these credentials to log in:
- Email: admin@example.com
- Password: Admin@123

**Important**: Change the admin password immediately after first login!

## Features in Detail

### For Employees
- Daily check-in and check-out
- Break management (start/end breaks)
- View personal attendance history
- Mobile-friendly interface
- Password management

### For Administrators
- User management (add/remove staff)
- View attendance reports
- Export reports to CSV
- Monitor late check-ins
- Track check-in locations
- System-wide analytics

## Security Features

- Password hashing using pbkdf2:sha256
- Session management
- CSRF protection
- Secure cookie handling
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Alabi Abdulhameed Ayomikun

## Support

For support, email [your-email@example.com] or open an issue in the GitHub repository.

