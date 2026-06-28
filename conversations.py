from starlette.responses import StreamingResponse

import models
import oauth2
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, Body, HTTPException, status, Response , APIRouter
from database import get_db
from sqlalchemy import select
import schemas
from google import genai
from config import settings
from retrieval import get_relevant_chunks
from rate_limit import check_rate_limit, r

ROUTER = APIRouter(tags=['conversations'])

client = genai.Client(api_key=settings.api_key)

async def streameresponse(history, conversation_id,current_user_id ,db):
    full_text = ""
    try:
        async for chunk in await client.aio.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=history
            ):
            full_text += chunk.text
            yield chunk.text
    except Exception as e:
        db.rollback()
        r.decr(f"rate_limit:{current_user_id}:chat")
        yield f"error: {str(e)}"
        return

    assistant_message = models.Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_text
        )

    db.add(assistant_message)
    db.commit()


@ROUTER.post("/talk", status_code=status.HTTP_201_CREATED)
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

    check_rate_limit(current_user.id, "chat", 10, 60)

    retrieval = await get_relevant_chunks(prompt.content,current_user.id, db)
    history = [f"""Answer the user's question using ONLY the context below. If the answer isn't in the context, say you don't know.
    Context:
    {retrieval}

    User question: {prompt.content}"""]


    return StreamingResponse(
    streameresponse(history, message.conversation_id, current_user.id, db),
    media_type="text/event-stream"
)

#start conversations


@ROUTER.post("/conversations/{conversation_id}/messages",response_model=schemas.gemini)
async def conversation (conversation_id : int, prompt: schemas.Prompt, db: Session = Depends(get_db), current_user : int = Depends(oauth2.get_current_user)):
    query = (db.execute(select(models.Conversation)
                      .where(models.Conversation.id == conversation_id,
                             models.Conversation.user_id == current_user.id))).scalar_one_or_none() #find out the conversation that blongs to the user
    if not query:
        raise HTTPException(status_code=404, detail="conversation not found or not aaccessable by you")
    query2 = db.execute(select(models.Message)
                        .where(models.Message.conversation_id == conversation_id)
                        .order_by(models.Message.created_at)).scalars().all()        #we can order based on id aswell

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
    retrieval = await get_relevant_chunks(prompt.content,current_user.id, db)
    history.insert(0, {
        "role": "user",
        "parts": [{"text": f"""Use ONLY this context to answer questions. If not in context, say you don't know.

    Context:{retrieval}"""}]
    })

    check_rate_limit(current_user.id, "chat", 10, 60)

    message1 = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=prompt.content
    )
    db.add(message1)
    db.flush()

    return StreamingResponse(
        streameresponse(history, message.conversation_id, current_user.id, db),
        media_type="text/event-stream")
# keep going with already existing conversations

@ROUTER.delete('/conversations/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(id : int ,
                       db: Session = Depends(get_db),
                       current_user:models.User = Depends(oauth2.get_current_user)):

    dlt_conversation = db.execute(select(models.Conversation).where(models.Conversation.id == id,
                                          models.Conversation.user_id == current_user.id)).scalar_one_or_none()
    if not dlt_conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="conversation not found")
    db.delete(dlt_conversation)
    db.commit()

    #delete conversations

@ROUTER.patch('/conversations/{id}', status_code=status.HTTP_200_OK)
async def update_conversation(id : int ,title : str,db: Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    conversation = db.execute(select(models.Conversation).where(models.Conversation.id == id,
                                                                models.Conversation.user_id == current_user.id)).scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="conversation not found")
    conversation.title = title
    # patched_name = models.Conversation( title = title)
    db.commit()
    db.refresh(conversation)
    return conversation
    #update the conversation title


@ROUTER.get("/conversations", response_model=list[schemas.ConversationOut])
async def get_conversations(db: Session = Depends(get_db),current_user : int = Depends(oauth2.get_current_user)):
    conversations = db.execute(select(models.Conversation)
                               .where(models.Conversation.user_id== current_user.id)
                               .order_by(models.Conversation.created_at)).scalars().all()

    return conversations
# conversations list sidebar