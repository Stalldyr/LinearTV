import multiprocessing

# Serverinnstillinger
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Prosessnavngivning
proc_name = "tv_app"

# Timeouts
timeout = 120
keepalive = 5

# Sikkerhet
limit_request_line = 4096
limit_request_fields = 100

#reload = True
