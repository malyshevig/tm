from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

TASK_STATUS_IDLE = "idle"
TASK_STATUS_ASSIGNED = "assigned"
TASK_STATUS_IN_PROGRESS = "in-progress"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

MAX_FAILURES_ALLOWED = 3


class Task(BaseModel):
    task_id: int
    task_type: str
    details:dict[str, Any]

class NewTask(BaseModel):
    task_type: str
    details: dict[str, Any]
    status: str


class TaskUpdate(BaseModel):
    task_id: int
    details: dict[str, Any]

# Pydantic модель для представления задачи
class TaskInfo(BaseModel):
    task_id: int
    created_dt: datetime
    updated_dt: datetime
    task_type: str
    details: dict[str, Any]
    status: str
    worker_id: Optional[str] = None
    update_details: Optional[dict[str, Any]] = None
    fail_count: Optional[int] = 0


def TASK_STATUS_FAILED():
    return None