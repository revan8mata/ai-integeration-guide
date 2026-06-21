import models
import oauth2

from fastapi import Cookie, FastAPI, Depends, Body, HTTPException, status, Response , APIRouter


ROUTER = APIRouter(tags=['conversations'])



@ROUTER.post("/conversation")
async def conversations(,current_user : int = Depends(oauth2.get_current_user)):

    conv = db.execute(select(models.Conversation)

