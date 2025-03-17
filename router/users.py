from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from services.database import db_dependency
from models.users import Users
from utils.passwords import get_password_hash
from utils.users import get_current_user
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/api",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
) 


class UserBase(BaseModel): 
    username: str
    email: str
    phone: str
    first_name: str
    last_name: str
    password: str


@router.post("/register")
async def create_user(user: UserBase, db: db_dependency):
    
    db_user = Users( 
            username=user.username,
            email=user.email,
            first_name=user.first_name, 
            last_name=user.last_name, 
            password=get_password_hash(user.password),  
        )

    try:
        # Add the new user to the database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return {
            "message": "User registered successfully.", 
            "username": db_user.username,
            "email": db_user.email
        }

    except IntegrityError as e: 
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )
        
    except Exception as e:
        # Catch any other unexpected errors
        db.rollback()  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user. Error: {str(e)}"
        )


@router.post("/me", response_model=UserBase)
async def read_users_me(db: db_dependency, current_user: Users = Depends(get_current_user)): 
    return JSONResponse(
        status_code=200,
        content= {
            "username": current_user.username,
            "email": current_user.email, 
            "first_name": current_user.first_name, 
            "last_name": current_user.last_name,  
        }
    )     