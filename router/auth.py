from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta, datetime 
from pydantic import BaseModel  
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from utils.passwords import create_access_token, verify_password, get_password_hash
from utils.users import authenticate_user
from config import JWT_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from services.database import engine
from sqlalchemy.orm import Session
from services.database import db_dependency

 
router = APIRouter( 
    tags=["Users"],
    responses={404: {"description": "Not found"}},
) 


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token")
async def login_for_access_token(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    
    user = authenticate_user(
                    db=db, 
                    username=form_data.username, 
                    password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")