
from fastapi import  FastAPI,status,Depends, HTTPException
from google import genai
from sqlalchemy.orm import Session
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


