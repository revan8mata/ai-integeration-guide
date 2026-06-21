import models
import oauth2
from sqlalchemy.orm import Session
from fastapi import Cookie, FastAPI, Depends, Body, HTTPException, status, Response , APIRouter
from database import get_db
from sqlalchemy import select
ROUTER = APIRouter(tags=['conversations'])



# @ROUTER.post("/conversation")
# async def conversations(,current_user : int = Depends(oauth2.get_current_user)):
#
#     conv = db.execute(select(models.Conversation)

# DELETE /conversations/{id}
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

@ROUTER.patch('/conversations/{id}', status_code=status.HTTP_200_OK)
async def update_conversation(id : int ,db: Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    conversation = db.execute(select(models.Conversation).where(models.Conversation.id == id,)).scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="conversation not found")
    patched_name = models.Conversation.title(

    )