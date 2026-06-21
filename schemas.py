from pydantic import BaseModel, ConfigDict
from datetime import datetime




class Prompt(BaseModel):
    content: str

    model_config = ConfigDict(from_attributes=True)



class UserCreate(BaseModel):
    username: str
    password: str

class gemini(BaseModel):
    text: str

class TokenData(BaseModel):
    id: int | None = None

class conversation(BaseModel):
    user_id: int
    title: str

class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)