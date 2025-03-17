from datetime import datetime, timedelta, timezone
from typing import Optional, List
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
from services.cache import get_cache, set_cache, clear_cache, get_id_list, add_to_id_list, remove_from_id_list 
import json

router = APIRouter(
    prefix="/task",
    tags=["Task"],
    responses={404: {"description": "Not found"}},
)

class PriorityEnum(str, Enum):
    HIGH = "high"
    LOW = "low"
    MEDIUM = "medium"

class TaskStatusEnum(str, Enum):
    PENDING = "pending" 
    COMPLETED = "completed"

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

        # Convert task object to a dictionary
        task_data = {
            "id": db_task.id,
            "title": db_task.title,
            "description": db_task.description,
            "priority": Priority(db_task.priority).value
        }

        # Cache the newly created task and update the ID list
        await set_cache(f"task:{db_task.id}", task_data)
        await add_to_id_list(db_task.id)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Successfully added the task."
            }
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A task already exists."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add new task. Error: {str(e)}"
        )



class FilterBase(BaseModel):
    status: Optional[List[TaskStatus]] = None
    priority: Optional[List[Priority]] = None 


@router.post("/all")
async def view_all_tasks(page: int, task_filter:FilterBase, db: db_dependency, current_user: Users = Depends(get_current_user)):
    page_size = 10
    offset = (page - 1) * page_size

    try:
        # Get task IDs from Redis
        task_ids = await get_id_list()
        tasks = []
        
        if len(task_filter.status) == 0 and len(task_filter.priority) == 0: 
            
            # Fetch cached tasks
            for task_id in task_ids[offset:offset + page_size]:
                cached_task = await get_cache(f"task:{task_id}")
                if cached_task:
                    tasks.append(cached_task)

        # Fallback to DB if cache miss
        if len(tasks) < page_size:
            
            query = db.query(Task)
            
            if task_filter.status:
                query = query.filter(Task.status.in_(task_filter.status))
            
            # Apply priority filter
            if task_filter.priority:
                query = query.filter(Task.priority.in_(task_filter.priority))
                
            
            for db_task in query:
                task_data = {
                    "id": db_task.id,
                    "title": db_task.title,
                    "description": db_task.description,
                    "status": TaskStatus(db_task.status).value,
                    "priority": Priority(db_task.priority).value
                }
                tasks.append(task_data)
                await set_cache(f"task:{db_task.id}", task_data)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Successfully fetched all tasks.",
                "body": tasks
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch all tasks. Error: {str(e)}"
        )
        
        
class TaskDeleteBase(BaseModel):
    id: int

@router.post("/view")
async def delete_task(task: TaskDeleteBase, db: db_dependency):
    try:
        db_task = db.query(Task).filter(Task.id == task.id).first()

        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        return JSONResponse(
            status_code=200,
            content={
                "id": db_task.id,
                "title": db_task.title,
                "description": db_task.description,
                "status": TaskStatus(db_task.status).value,
                "priority": Priority(db_task.priority).value            
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to view task. {str(e)}"
        )


class TaskDeleteBase(BaseModel):
    id: int

@router.post("/delete")
async def delete_task(task: TaskDeleteBase, db: db_dependency):
    try:
        db_task = db.query(Task).filter(Task.id == task.id).first()

        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        db.delete(db_task)
        db.commit()

        # Remove from cache and ID list
        await clear_cache(f"task:{task.id}")
        await remove_from_id_list(task.id)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Successfully deleted the task."
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task. {str(e)}"
        )

class TaskEditBase(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatusEnum
    priority: PriorityEnum

@router.post("/edit")
async def edit_task(task: TaskEditBase, db: db_dependency):
    try:
        db_task = db.query(Task).filter(Task.id == task.id).first()

        if db_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        db_task.title = task.title
        db_task.description = task.description
        db_task.priority = Priority(task.priority) 
        db_task.status = TaskStatus(task.status) 

        db.commit()
        db.refresh(db_task)

        # Update cache
        task_data = {
            "id": db_task.id,
            "title": db_task.title,
            "description": db_task.description,
            "priority": Priority(db_task.priority).value
        }
        await set_cache(f"task:{db_task.id}", task_data)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Successfully edited the task."
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit task. {str(e)}"
        )
