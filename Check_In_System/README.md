# Office Check-In System

A simple web-based application for tracking staff arrivals and departures in an office environment. This system allows staff to check in and out, while administrators can manage staff and view reports.

## Features

- User authentication (login/logout)
- Staff check-in and check-out tracking
- Admin dashboard for staff management
- Reports generation by date
- Responsive design for desktop and mobile devices

## Requirements

- Python 3.6 or higher
- Flask
- SQLite3 (included with Python)

## Installation

1. Clone or download this repository to your local machine
2. Navigate to the project directory
3. Install the required dependencies:

```bash
pip install flask
```

## Usage

1. Start the application:

```bash
python app.py
```

2. Open a web browser and navigate to `http://127.0.0.1:5000`
3. Log in with the default admin credentials:
   - Email: admin@example.com
   - Password: admin123

## System Roles

### Staff
- Can check in and out
- Can view their own check-in/out history

### Administrator
- Can register new staff members
- Can view reports of all staff check-ins and check-outs
- Can manage staff accounts

## Database Structure

The application uses SQLite for data storage with the following tables:

- `staff`: Stores staff information (id, name, email, password, role)
- `check_in_logs`: Records check-in and check-out times (id, staff_id, check_in_time, check_out_time, date)

## Security Notes

This is a demonstration application and has several security limitations:

- Passwords are stored in plain text (in a production environment, use proper password hashing)
- No CSRF protection is implemented
- No input validation beyond basic form requirements

For production use, these security issues should be addressed.

## Customization

You can customize the application by:

- Modifying the templates in the `templates` directory
- Updating the CSS in `static/css/style.css`
- Adding additional functionality to `app.py`

## License

This project is available for personal and commercial use.