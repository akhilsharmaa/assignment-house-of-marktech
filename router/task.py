from datetime import datetime, timedelta, timezone
from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from services.database import db_dependency
from models.users import Users
from models.task import Task, TaskStatus, Priority
from utils.users import get_current_user
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from enum import Enum

router = APIRouter(
    prefix="/task",
    tags=["Task"],
    responses={404: {"description": "Not found"}},
) 

class PriorityEnum(str, Enum):  
    HIGH = "high" 
    LOW = "low"
    MEDIUM = "medium"
    
class TaskBase(BaseModel):   
    title: str
    description: str  
    priority: PriorityEnum

@router.post("/new")
async def create_new_task(task: TaskBase, 
                              db: db_dependency, 
                              current_user: Users = Depends(get_current_user)): 

    db_task = Task( 
            title=task.title,  
            description=task.description,   
            priority=Priority(task.priority.value)
        )


    try: 
        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        return JSONResponse(
            status_code=200,
            content= {
                "message": "successfully added the task."
            }
        )     

    except IntegrityError as e: 
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A task already exists."
        )
        
    except Exception as e:
        # Catch any other unexpected errors
        db.rollback()  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add new task. Error: {str(e)}"
        )
        


@router.post("/all")
async def view_all_tasks(db: db_dependency, current_user: Users = Depends(get_current_user)): 

    try:
        db_tasks = db.query(Task).filter().all()
        
        result = []; 
        for ele in db_tasks: 
            result.append({
                    "id": ele.id,
                    "title": ele.title,
                    "description": ele.description,  
                    "priority": Priority(ele.priority).value
                })

        return JSONResponse(
            status_code=200,
            content= {
                "message": "successfully fetched all the tasks.", 
                "body":  result
            }
        )     

    except Exception as e:
        # Catch any other unexpected errors
        db.rollback()  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch all tasks. Error: {str(e)}"
        )
        

class TaskDeleteBase(BaseModel):   
    id: int 
    
@router.post("/delete")
async def delete_task(task: TaskDeleteBase, db: db_dependency): 

    try:

        db_task = db.query(Task).filter(Task.id == task.id).first();  
        
        if db_task is None:
            # Handle the case where the task doesn't exist
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="task not found."
            )
        
        
        db.delete(db_task)
        db.commit() 

        return JSONResponse(
            status_code=200,
            content= {
                "message": "successfully deleted the task."
            }
        )     

    except Exception as e:
        # Catch any other unexpected errors
        db.rollback()  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task. {str(e)}"
        )