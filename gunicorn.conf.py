import os

# Worker configuration
workers = int(os.getenv('WEB_CONCURRENCY', 4))
worker_class = 'sync'
threads = int(os.getenv('PYTHON_MAX_THREADS', 1))

# Binding
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Timeout configuration
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Reload on code changes
reload = os.getenv('FLASK_ENV') == 'development'

# SSL configuration (if needed)
keyfile = None
certfile = None 