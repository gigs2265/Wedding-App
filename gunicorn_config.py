# Gunicorn configuration for better concurrent upload handling
import multiprocessing
import os

# Bind to the PORT environment variable (Render provides this)
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Use gevent async workers for better concurrency
worker_class = 'gevent'

# Number of worker processes
# Free tier has limited CPU, so keep this modest
workers = 2

# Each worker can handle multiple concurrent connections with gevent
worker_connections = 50

# Timeout for uploads (important for large files)
timeout = 300  # 5 minutes for large video uploads

# Preload app for better memory usage
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
