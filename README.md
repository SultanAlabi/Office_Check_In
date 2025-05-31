# Check-In System

A modern Flask-based Check-In System designed for efficient employee attendance tracking and management.

## Features

- User Authentication (Admin/Staff roles)
- QR Code-based Check-In
- Break Time Management
- Late Check-In Handling
- Mobile-Friendly Interface
- Attendance Reports & Export
- Location Tracking
- Real-time Status Updates

## Tech Stack

- Python 3.11+
- Flask
- SQLite
- Jinja2 Templates
- HTML/CSS/JavaScript
- Gunicorn (Production Server)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/Check_In_System.git
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
- Development: http://localhost:5000
- Default Admin Credentials:
  - Email: admin@example.com
  - Password: Admin@123

## Deployment

This application is configured for deployment on Render.com. See `render.yaml` for deployment configuration.

## Security

- Password Hashing
- Session Management
- CSRF Protection
- Secure Cookie Configuration
- Input Validation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
