import multiprocessing

bind = "0.0.0.0:8000"
workers = int(__import__("os").getenv("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count() * 2 + 1)))
threads = int(__import__("os").getenv("GUNICORN_THREADS", "2"))
timeout = int(__import__("os").getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(__import__("os").getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
loglevel = __import__("os").getenv("LOG_LEVEL", "info")
preload_app = False
worker_tmp_dir = "/dev/shm"
max_requests = int(__import__("os").getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(__import__("os").getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))
