from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from database import base



class User(base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=func.now())


class Conversation(base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    created_at = Column(DateTime, default=func.now())

class Message(base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id",ondelete='CASCADE'),
        nullable=False

    )
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())







