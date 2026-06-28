import redis
from fastapi import HTTPException
r = redis.Redis(host='redis', port=6379, db=0)


def check_rate_limit(user_id: int, endpoint: str, max_requests: int, window_seconds: int):
    key = f"rate_limit:{user_id}:{endpoint}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, window_seconds)

    if count > max_requests:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
