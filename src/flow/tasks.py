import json
import threading
from functools import wraps
from tm.client import TMClient

def add_task (task):
    task_id = TMClient.create_task("flow_task", task)
    return task_id

def whate_until_done (task_id):
    while True:
        task = TMClient.get_task(task_id)
        if task_status == "in progress":
            return task

        time.sleep(5)

def log_task (flow_id, task_id):
    TMClient.update_task(flow_id, task_id)


def task(name, action="create"):
    """
    Декоратор: вместо вызова функции записывает задачу в БД.
    Возвращает ID задачи.
    """
    def decorator(func):
        # Регистрируем функцию в глобальном реестре

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
               if action=="create":

                    # Сериализуем аргументы в JSON
                    flow_id = threading.local().flow_id

                    args_json = json.dumps(args)
                    kwargs_json = json.dumps(kwargs)

                    task = {"flow_id": flow_id, name=name, "func": func.__name__, "args": args_json, "kwargs": kwargs_json}

                    task_id = add_task (task)
                    result = whate_until_done (task_id)

                    log_task(flow_id, task_id)
                    return result
               elif action="work":
                   get_tasl("")

            finally:
                pass
        return wrapper
    return decorator


def flow(flow_id: str):
    """
    Декоратор: вместо вызова функции записывает задачу в БД.
    Возвращает ID задачи.
    """
    def decorator(func):
        # Регистрируем функцию в глобальном реестре

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Сериализуем аргументы в JSON
                threading.local().flow_id = flow_id
                return func(*args, **kwargs)
            finally:
                del threading.local().flow_id
        return wrapper
    return decorator