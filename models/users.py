from pydantic import BaseModel
from services.database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, func


class Users(Base):
    __tablename__ = "users"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    username            = Column(String(50), unique=True, nullable=False)
    email               = Column(String(100), unique=True, nullable=True)
    phone               = Column(String(10), unique=True, nullable=True)
    first_name          = Column(String(50), nullable=False)
    last_name           = Column(String(50), nullable=False)
    password            = Column(String(255), nullable=False) 
    is_admin            = Column(Boolean, default=False) 
    is_cashier          = Column(Boolean, default=False) 
    created_at          = Column(DateTime, default=func.now(), nullable=False)