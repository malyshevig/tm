import inspect
import json
from functools import wraps

from tm import Worker
from tm.client import TMClient

base_url = "http://localhost:82"
tmclient = TMClient(base_url)

def serialize_call(func, bound):
    arguments = {k: v for k, v in bound.arguments.items() if k != 'self'}

    return json.dumps({
        "method": func.__name__,
        "class": func.__qualname__.rsplit('.', 1)[0] if '.' in func.__qualname__ else None,
        "arguments": arguments
    })


def deserialize_call(details:dict, target):
    """
    Выполняет десериализованный вызов на целевом объекте.

    Args:
        details: dict с описанием вызова
        target: объект, на котором нужно вызвать метод

    Returns:
        Результат выполнения метода
    """

    method_name = details["method"]
    arguments = details["arguments"]

    # Получаем метод
    if not hasattr(target, method_name):
        raise AttributeError(f"У объекта {target} нет метода '{method_name}'")

    method = getattr(target, method_name)

    # Вызываем метод с распакованными аргументами
    return method, arguments



def workflow_call(workflow_id):
    def proxy(func):
        sig = inspect.signature(func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Сериализуем только аргументы (без self)
            serialized = serialize_call(func, bound)
            print(f"[SERIALIZE] {serialized}")

            # 4. Вызываем оригинальную функцию с очищенными аргументами
            #return func(*bound.args, **bound.kwargs)
            #ask_type = func.__qualname__
            task_type = f"{workflow_id}.{func.__name__}"
            tmclient.create_task(task_type, serialized)

            return serialized

        return wrapper
    return proxy


def workflow_action(workflow_id):
    def action(func):
        @wraps(func)
        def wrapper(self,  *args, **kwargs):
#            task_type = func.__qualname__
            task_type = f"{workflow_id}.{func.__name__}"


            worker = Worker(123, task_type, base_url )
            with worker.take_task() as task:
                details = task.details
                method, arguments = deserialize_call(details, self)
                func(self,**arguments)

            # 4. Вызываем оригинальную функцию с очищенными аргументами
            #return func(*bound.args, **bound.kwargs)

            return
        return wrapper
    return action
