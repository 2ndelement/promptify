from typing import Optional
import uuid
import json
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Response
from loguru import logger
from pydantic import BaseModel
import requests
import redis
from fastapi.security import OAuth2PasswordBearer
from revChatGPT.V3 import Chatbot

from config import config
from util import *

chatbot = Chatbot(api_key=config.api_key, proxy=config.proxy)
prompts = []

try:
    with open("conversations.json", "r") as f:
        chatbot.conversation = json.load(f)
except FileNotFoundError:
    with open("conversations.json", "w") as f:
        json.dump({}, f)
        logger.info("conversations.json not found, created empty file")

try:
    with open("prompts.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)
except FileNotFoundError:
    with open("prompts.json", "w") as f:
        json.dump([], f)
        logger.info("prompts.json not found, created empty file")

redis_client = redis.Redis(
    host=config.database_host, port=config.database_port, db=config.database
)
try:
    redis_client.ping()
except redis.exceptions.ConnectionError:
    logger.error("Redis connection error")
    exit(1)


app = FastAPI()
router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/wx_login")
async def wx_login(body: dict = Body(...)):
    appid = config.app_id
    secret = config.app_secret
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={body['code']}&grant_type=authorization_code"

    response = requests.get(url)
    data = response.json()

    openid = data.get("openid")
    session_key = data.get("session_key")

    if openid:
        is_first_login = redis_client.get(openid + ":cnt") is None

        if is_first_login:
            initial_count = config.initial_count
            redis_client.set(openid + ":cnt", initial_count)

        # 生成JWT Token
        token_data = {"openid": openid}
        token = await generate_jwt_token(token_data)
        refresh_token = await generate_refresh_token(token_data)

        return {"openid": openid, "token": token, "refresh_token": refresh_token}
    else:
        raise HTTPException(status_code=400, detail="invalid code")


class conversationBody(BaseModel):
    prompt: str = Body(..., max_length=1000)
    conversation_id: str


async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/wx_login")),
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        openid = await verify_jwt_token(token)
        if openid is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return openid


@router.post("/conversation")
async def conversation(
    body: conversationBody, response: Response, openid: str = Depends(get_current_user)
):
    if redis_client.get(openid + ":cnt") is None:
        raise HTTPException(status_code=401, detail="Usage limit exceeded")
    response.headers["Content-Type"] = "text/event-stream"
    redis_client.decr(openid + ":cnt")
    return StreamingResponse(
        chatbot.ask_stream(body.prompt, convo_id=body.conversation_id),
        media_type="text/event-stream",
    )


@router.post("/create_conversation")
async def create_conversation(openid: str = Depends(get_current_user)):
    conversation_id = str(uuid.uuid4())
    return {"conversation_id": conversation_id}


@router.post("/refresh_token")
async def refresh_token(openid: str = Depends(get_current_user)):
    data = dict(openid=openid)
    return dict(
        token=generate_jwt_token(data), refresh_token=generate_refresh_token(data)
    )


@router.get("/prompts")
async def get_prompts(openid: str = Depends(get_current_user)):
    return prompts


@router.get("/cnt")
async def get_cnt(openid: str = Depends(get_current_user)):
    return redis_client.get(openid + ":cnt")


async def shutdown_event():
    with open("conversations.json", "w") as f:
        json.dump(chatbot.conversation, f)


app.add_event_handler("shutdown", shutdown_event)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app="app:app",
        host=config.server,
        port=config.port,
        reload=False,
        workers=1,
        log_level="info",
    )
