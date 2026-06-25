import models
import oauth2
from sqlalchemy.orm import Session
from fastapi import Cookie, FastAPI, Depends, Body, HTTPException, status, Response , APIRouter
from database import get_db
from sqlalchemy import select
import schemas
from google import genai
from config import settings
from retrieval import get_relevant_chunks
ROUTER = APIRouter(tags=['conversations'])

client = genai.Client(api_key=settings.api_key)


@ROUTER.get("/conversations", response_model=list[schemas.ConversationOut])
async def get_conversations(db: Session = Depends(get_db),current_user : int = Depends(oauth2.get_current_user)):
    conversations = db.execute(select(models.Conversation)
                               .where(models.Conversation.user_id== current_user.id)
                               .order_by(models.Conversation.created_at)).scalars().all()
    print(conversations)
    return conversations
# conversations list sidebar


@ROUTER.post("/", status_code=status.HTTP_201_CREATED,response_model=schemas.gemini)
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

    retrieval = await get_relevant_chunks(prompt.content, db)
    try :
        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents= f"""Answer the user's question using ONLY the context below. If the answer isn't in the context, say you don't know.
Context:
{retrieval}

User question: {prompt.content}"""
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
#start conversations
@ROUTER.post("/conversations/{conversation_id}/messages",response_model=schemas.gemini)
async def conversation (conversation_id : int, prompt: schemas.Prompt, db: Session = Depends(get_db), current_user : int = Depends(oauth2.get_current_user)):
    query = (db.execute(select(models.Conversation)
                      .where(models.Conversation.id == conversation_id,
                             models.Conversation.user_id == current_user.id))).scalar_one_or_none() #find out the conversation blongs to the user
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
    retrieval = await get_relevant_chunks(prompt.content, db)
    history.insert(0, {
        "role": "user",
        "parts": [{"text": f"""Use ONLY this context to answer questions. If not in context, say you don't know.

    Context:{retrieval}"""}]
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