import json
from typing import Optional, Any

from fastapi import FastAPI, Form
import uvicorn
from starlette.responses import JSONResponse

from src.tm.mgr import TaskManager
from tm import errors, model
from tm.errors import TaskException
from tm.model import NewTask, TaskInfo, Task

app = FastAPI()
task_manager = TaskManager()

@app.get("/tm/api/v1/heartbeat")
async def hb(agent_id: str):
    return JSONResponse(
        status_code=200,
        content={
            "body": "Health is ok"
        },
    )


@app.get("/tm/api/v1/heartbeat")
async def hb():
    return JSONResponse(
        status_code=200,
        content={
            "body": "Health is ok"
        },
    )

@app.post("/tm/api/v1/worker/{worker_id}/{task_type}/assign", response_model=Task)
async def assign(worker_id: str, task_type:str):
    task:TaskInfo=task_manager.assign_task(worker_id, task_type)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={
                "body": "No tasks to perform"
            },
        )
    return Task(task_id=task.task_id, details=task.details, task_type=task.task_type)


def return_code_on_error (err: TaskException):
    if isinstance(err, errors.TaskNotFound):
        return JSONResponse(
            status_code=404,
            content={
                "body": err.msg
            },
        )
    if isinstance(err,errors.IncorrectTaskStatusForOperation):
        return JSONResponse(
            status_code=406,
            content={
                "body": err.msg
            },
        )
    if isinstance(err, errors.IncorrectWorkerId):
        return JSONResponse(
            status_code=401,
            content={
                "body": err.msg
            },
        )
    if isinstance(err, errors.DatabaseException):
        return JSONResponse(
            status_code=503,
            content={
                "body": err.msg
            },
        )
    return JSONResponse(
            status_code=503,
            content={
                "body": "Unexpected Internal Server Error"
            },
        )


@app.post("/tm/api/v1/worker/{worker_id}/task/{task_id}/accept")
async def accept(worker_id: str, task_id:int):
    try:
        task_manager.accept(task_id=task_id, worker_id=worker_id)
        return JSONResponse(
            status_code=200,
            content={
                "body": "Keep working on the task"
            },
        )

    except errors.TaskException as e:
        return return_code_on_error(e)

@app.post("/tm/api/v1/worker/{worker_id}/task/{task_id}/update")
async def update(worker_id: str, task_id:int, details: str=Form(...)):
    try:
        task_manager.update(worker_id, task_id,  details=json.loads(details))
        return JSONResponse(
            status_code=200,
            content={
                "body": "Update accepted"
            },
        )
    except TaskException as e:
        return return_code_on_error(e)



@app.post("/tm/api/v1/worker/{worker_id}/task/{task_id}/failed")
async def failed(worker_id: str, task_id:int, details: str=Form(...)):
    task_manager.fail(worker_id, task_id, details=json.loads(details))
    return JSONResponse(
        status_code=200,
        content={
            "body": "Update accepted"
        },
    )


@app.post("/tm/api/v1/worker/{worker_id}/task/{task_id}/completed")
async def completed(worker_id: str, task_id:int, details: str=Form(...)):
    try:
        task_manager.complete(worker_id, task_id, details=json.loads(details))

        return JSONResponse(
            status_code=200,
            content={
                "body": "Update accepted"
            },
        )
    except TaskException as e:
        return return_code_on_error(e)


@app.post("/tm/api/v1/tm/task")
async def create_task(task_type:str=Form(...), details: str=Form(...)):
    new_task_info = task_manager.create(NewTask(task_type=task_type, details=json.loads(details),status=model.TASK_STATUS_IDLE))
    return new_task_info

@app.get("/tm/api/v1/tm/task")
async def tasks( limit: Optional[int] = 20, offset: Optional[int] = 0):

    task_list = task_manager.get_tasks(limit, offset)
    return task_list


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Task Manager service"
    )

    # Опциональный аргумент с коротким (-o) и длинным (--output) именем
    parser.add_argument(
        "-p", "--port",
        default=8200,
        help="Port (by default: 8200)"
    )

    # Аргумент с ограниченным списком возможных значений (choices)

    # 3. Парсим аргументы из командной строки
    args = parser.parse_args()
    port = int(args.port)

    uvicorn.run(app, host="0.0.0.0", port=port)
