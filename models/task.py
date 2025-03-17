from services.database import Base 
from services.database import Base 
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func, Enum
from enum import Enum as PyEnum 


class TaskStatus(PyEnum):
    PENDING = "pending" 
    COMPLETED = "completed"
    
class Priority(PyEnum):
    HIGH = "high" 
    LOW = "low"
    MEDIUM = "medium"
    
class Task(Base):
    __tablename__ = "task"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    title               = Column(String(100), unique=True, nullable=False)
    description         = Column(String(250), unique=False, nullable=True)  
    status              = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING) 
    priority            = Column(Enum(Priority), nullable=False, default=Priority.LOW) 
    created_at          = Column(DateTime, default=func.now(), nullable=False)