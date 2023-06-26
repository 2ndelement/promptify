import jwt
from datetime import datetime, timedelta

from config import config

jwt_secret = config.jwt_secret
jwt_algorithm = config.jwt_algorithm
jwt_expire_minutes = config.jwt_expire_minutes


async def generate_jwt_token(data: dict):
    now = datetime.utcnow()
    expire = now + timedelta(minutes=jwt_expire_minutes)

    data["exp"] = expire
    token = jwt.encode(data, jwt_secret, algorithm=jwt_algorithm)
    return token


async def generate_refresh_token(data: dict):
    now = datetime.utcnow()
    expire = now + timedelta(minutes=jwt_expire_minutes * 2)

    data["exp"] = expire
    token = jwt.encode(data, jwt_secret, algorithm=jwt_algorithm)
    return token


async def verify_jwt_token(token: str):
    try:
        data = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        exp = data.get("exp")
        now = datetime.timestamp(datetime.utcnow())
        if exp is None or now > exp:
            return None
        return data.get("openid")
    except:
        return None
