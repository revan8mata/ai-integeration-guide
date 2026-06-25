from dns.e164 import query

import models
import oauth2
from sqlalchemy.orm import Session
from fastapi import  FastAPI, Depends, Body, HTTPException, status, Response , APIRouter,File, UploadFile
from database import get_db
from sqlalchemy import select
from fastapi import File, UploadFile
import google.genai as genai
import fitz
from google import genai
from config import settings
from google.genai import types


ROUTER = APIRouter(tags=['DOCS'],prefix="/docs")

client = genai.Client(api_key=settings.api_key)

@ROUTER.post('/')
async def post_docs(file: UploadFile = File(...),db: Session = Depends(get_db),current_user : int = Depends(oauth2.get_current_user)):
    if file.content_type == "application/pdf":
        pdf = fitz.open(stream=await file.read(), filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
    else:
        content = await file.read()
        text = content.decode("utf-8")

    docs = models.Document(
        user_id = current_user.id,
        filename = file.filename,
    )                                               #medadata of docs
    db.add(docs)
    db.commit()
    db.refresh(docs)

    words = text.split()
    chunks = [" ".join(words[i:i+500]) for i in range(0, len(words), 500)]

    for chunk_text in chunks:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk_text,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )

        vector = result.embeddings[0].values

        embed = models.Chunk(
            document_id=docs.id,
            text=chunk_text,
            embedding=vector

        )
        db.add(embed)
    db.commit()
    return  {"text" : "doc uploaded successfully", "doc_id" : docs.id}

@ROUTER.get('/')
async def get_docs(db: Session = Depends(get_db),current_user : int = Depends(oauth2.get_current_user)):
    query = db.execute(select(models.Document)
    .where(models.Document.user_id == current_user.id)
             .order_by(models.Document.created_at)
                       ).scalars().all()

    return query


@ROUTER.delete('/{id}')
async def delete_docs(id: int,db: Session = Depends(get_db),current_user : int = Depends(oauth2.get_current_user)):

    doc = db.execute(select(models.Document)
    .where(models.Document.id == id,
           models.Document.user_id == current_user.id)
    .scalar_one_or_none())

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "document deleted"}



# return

# text = "the cat sat on the mat and looked around"

# words = text.split()
# ["the", "cat", "sat", "on", "the", "mat", "and", "looked", "around"]

# chunks = [" ".join(words[i:i+4]) for i in range(0, len(words), 4)]
# chunk size 4 for simplicity

# chunk 1: words[0:4]  → ["the", "cat", "sat", "on"]    → "the cat sat on"
# chunk 2: words[4:8]  → ["the", "mat", "and", "looked"] → "the mat and looked"
# chunk 3: words[8:12] → ["around"]                       → "around"

# print(chunks)
# ["the cat sat on", "the mat and looked", "around"]