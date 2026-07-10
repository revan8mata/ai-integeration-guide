from pydantic import BaseModel, ConfigDict
from datetime import datetime


from enum import Enum

class EventType(str, Enum):
    document_uploaded = "document_uploaded"
    new_conversation = "new_conversation"
    delete_conversation = "delete_conversation"

class WebhookCreate(BaseModel):
    url: str
    event_type: EventType


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