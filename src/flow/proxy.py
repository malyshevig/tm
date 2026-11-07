import inspect
import json
from functools import wraps


def serialize_call(func, bound):
    arguments = {k: v for k, v in bound.arguments.items() if k != 'self'}

    return json.dumps({
        "method": func.__name__,
        "class": func.__qualname__.rsplit('.', 1)[0] if '.' in func.__qualname__ else None,
        "arguments": arguments
    })


def deserialize_call(json_str: str, target):
    """
    Выполняет десериализованный вызов на целевом объекте.

    Args:
        json_str: JSON-строка с описанием вызова
        target: объект, на котором нужно вызвать метод

    Returns:
        Результат выполнения метода
    """
    data = json.loads(json_str)
    method_name = data["method"]
    arguments = data["arguments"]

    # Получаем метод
    if not hasattr(target, method_name):
        raise AttributeError(f"У объекта {target} нет метода '{method_name}'")

    method = getattr(target, method_name)

    # Вызываем метод с распакованными аргументами
    return method( **arguments)


def proxy(func):
    sig = inspect.signature(func)
    @wraps(func)
    def wrapper( *args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # Сериализуем только аргументы (без self)
        serialized = serialize_call(func, bound)
        print(f"[SERIALIZE] {serialized}")

        # 4. Вызываем оригинальную функцию с очищенными аргументами
        #return func(*bound.args, **bound.kwargs)

        return serialized


    return wrapper

