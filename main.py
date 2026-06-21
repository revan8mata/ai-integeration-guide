from certifi import where
from fastapi import  FastAPI,status,Depends, HTTPException
from google import genai
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user
from sqlalchemy import select
import auth
import schemas
import users
import models
import conversations
import oauth2
import os
import config
from config import settings
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
app = FastAPI()

origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.ROUTER)
app.include_router(users.ROUTER)
app.include_router(conversations.ROUTER)

client = genai.Client(api_key=settings.api_key)


@app.post("/", status_code=status.HTTP_201_CREATED,response_model=schemas.gemini)
async def talk(prompt : schemas.Prompt,db: Session = Depends(get_db), current_user : int = Depends(oauth2.get_current_user)):
    conversation = models.Conversation(
        user_id=current_user.id,
        title=prompt.content[:40]
    )
    db.add(conversation)
    db.flush()
    message = models.Message(
        conversation_id=conversation.id,
        role="user",
        content=prompt.content
    )
    db.add(message)
    db.flush()
    try :
        response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt.content
    )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=f"llm error: {str(e)}. try again later"
        )
    assistant_message = models.Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response.text
    )
    db.add(assistant_message)
    db.commit()
    return response


@app.get("/")
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
# retereve all massages assoiciated with that conversation id



@app.post("/conversations/{conversation_id}/messages",response_model=schemas.gemini)
async def sdd(conversation_id : int, prompt: schemas.Prompt, db: Session = Depends(get_db), current_user : int = Depends(oauth2.get_current_user)):
    query = (db.execute(select(models.Conversation)
                      .where(models.Conversation.id == conversation_id,
                             models.Conversation.user_id == current_user.id))).scalar_one_or_none() #find out the conversation blongs to the user
    if not query:
        raise HTTPException(status_code=404, detail="conversation not found or not aaccessable by you")
    query2 = db.execute(select(models.Message)
                        .where(models.Message.conversation_id == conversation_id,)
                        .order_by(models.Message.created_at)).scalars().all()        #we can order based on id aswell
    print(query2)

    history = []

    for message in query2:
        history.append({
            "role": "model" if message.role == "assistant" else "user",
            "parts": [
                {"text": message.content}
            ]
        })
    history.append({
        "role": "user",
        "parts": [
            {"text": prompt.content}
        ]
    })
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=f"LLM error: {str(e)}"
        )
    message1 = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=prompt.content
    )
    db.add(message1)
    message2 = models.Message(
        conversation_id=conversation_id,
        role="assistant",
        content=response.text
    )
    db.add(message2)
    db.commit()
    return {"text" : response.text}

@app.get("/conversations", response_model=list[schemas.ConversationOut])
async def get_conversations(db: Session = Depends(get_db),current_user : int = Depends(oauth2.get_current_user)):
    conversations = db.execute(select(models.Conversation)
                               .where(models.Conversation.user_id== current_user.id)
                               .order_by(models.Conversation.created_at)).scalars().all()
    print(conversations)
    return conversations




