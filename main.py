from fastapi import  FastAPI,status
from google import genai
import auth
import schemas
import users
import models
# import conversation
import os
import config
from config import settings
from fastapi.middleware.cors import CORSMiddleware

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
# app.include_router(conversaion.ROUTER)


client = genai.Client(api_key=settings.api_key)

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Explain how AI works in a few words"
)


@app.post("/", status_code=status.HTTP_201_CREATED,response_model=schemas.gemini)
async def talk(prompt : schemas.Prompt):
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt.content
    )
    return response









