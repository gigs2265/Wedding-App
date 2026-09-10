# Gunicorn configuration for better concurrent upload handling
import multiprocessing
import os

# Bind to the PORT environment variable (Render provides this)
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Use threaded workers for better concurrency (compatible with all Python versions)
worker_class = 'gthread'

# Number of worker processes
# Free tier has limited CPU, so keep this modest
workers = 2

# Each worker can handle multiple concurrent connections with threads
threads = 4  # 2 workers × 4 threads = 8 concurrent uploads

# Timeout for uploads (important for large files)
timeout = 300  # 5 minutes for large video uploads

# Keep-alive to handle multiple requests per connection
keepalive = 5

# Preload app for better memory usage
preload_app = True

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
