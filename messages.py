import models
import oauth2
from sqlalchemy.orm import Session
from fastapi import Cookie, FastAPI, Depends, Body, HTTPException, status, Response , APIRouter
from database import get_db
from sqlalchemy import select
import schemas
from google import genai
from config import settings


ROUTER = APIRouter(tags=['MESSAGES'])


@ROUTER.get("/conversations/{id}")
async def get_conversation(id: int, db: Session = Depends(get_db), current_user : int = Depends(oauth2.get_current_user)):
    convo_section = (db.execute(select(models.Conversation)
                               .where(models.Conversation.id == id,
                               models.Conversation.user_id == current_user.id))
                     .scalar_one_or_none())
    if convo_section is None:
        raise HTTPException(status_code=404,detail="conversation not found")

    messages = db.execute(select(models.Message)
                              .where(models.Message.conversation_id == id)
                                  .order_by(models.Message.created_at)).scalars().all()

    for message in messages:
        print(message.role)
        print(message.content[:40])
    return {"conversation": messages}

# get messages contained in conversation