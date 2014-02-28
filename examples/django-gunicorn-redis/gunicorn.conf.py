import multiprocessing
import os
os.environ["GEVENT_RESOLVER"] = "ares" #Resolves some nasty bugs with native socket creation in imports (for example a mobile detection lib reading cache from Redis)

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 10000
worker_class = "socketio.sgunicorn.GeventSocketIOWorker"
preload_app = True

raw_env=[
         "SOCKET_MANAGER_CLASS=socketio.contrib.redis.socket_manager.RedisSocketManager",
         "SOCKET_MANAGER_REDIS_HOST=0.0.0.0",
         "SOCKET_MANAGER_REDIS_PORT=6379",
         "SOCKET_MANAGER_REDIS_DB=0"
         ]
    

loglevel = "debug"


# this ensures forked processes are patched with psycogreen
def post_fork(server, worker):
    os.environ["GEVENT_RESOLVER"] = "ares"
    from psycogreen.gevent import patch_psycopg
    patch_psycopg()