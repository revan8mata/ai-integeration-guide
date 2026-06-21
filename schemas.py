from pydantic import BaseModel



class Prompt(BaseModel):
    content: str

    class Config:
        from_attributes = True



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