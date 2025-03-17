import jwt
from pydantic import BaseModel 
from fastapi import Depends, FastAPI, HTTPException, status, Depends 
from config import oauth2_scheme, JWT_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context
from models.users import Users 
from services.database import db_dependency, get_db
from utils.passwords import verify_password

def get_user(db: db_dependency, username: str):
    result = db.query(Users).filter(Users.username == username).first();  
    return result; 

def authenticate_user(db: db_dependency, username: str, password: str): 
    user = get_user(db, username); 
    if not user: 
        return False; 
    if not verify_password(password, user.password):
            return False
    return user
    
    
class TokenData(BaseModel):
    username: str | None = None
    
def get_current_user(db: db_dependency, token: str = Depends(oauth2_scheme)) -> Users: 
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}, 
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except Exception as e:
            raise credentials_exception
    
     
    user = get_user(db=db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
 