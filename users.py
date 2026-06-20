from sqlalchemy import select

import utilities
import schemas
import models
import oauth2
from fastapi import Cookie, FastAPI, Depends, Body, HTTPException, status, Response , APIRouter
from logging import exception
from sqlalchemy.orm import Session
from database import get_db

ROUTER = APIRouter(tags=['login'])

#
@ROUTER.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    reg: schemas.UserCreate,
    db: Session = Depends(get_db)
):

    register = db.execute(
        select(models.User)
        .where(models.User.username == reg.username)
    ).first()

    if register:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    hashed = utilities.hash(reg.password)

    new_user = models.User(
        username=reg.username,
        hashed_password=hashed
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "notif": f"{new_user.username} is now a user"
    }
# Steps:
# 1. Validate input
# 2. Check duplicate username
# 3. Hash password
# 4. Create User model
# 5. Save DB
# 6. Return response