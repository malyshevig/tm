

class TaskException(Exception):
    def __init__(self, msg:str):
        self.msg=msg


class TaskNotFound(TaskException):
    def __init__(self, task_id, msg=None):
        self.task_id = task_id
        msg = msg if msg else f"task {task_id} not found"
        super().__init__(msg)


class IncorrectWorkerId(TaskException):
    def __init__(self, task_id, worker_id, msg=None):
        self.task_id = task_id
        self.worker_id = worker_id
        msg = msg if msg else f"incorrect worker_id {worker_id} for task {task_id}"
        super().__init__(msg)


class IncorrectTaskStatusForOperation(TaskException):
    def __init__(self, task_id, status, msg=None):
        self.task_id = task_id
        self.status = status
        msg = msg if msg else f"incorrect status {status} for operation on task {task_id}"
        super().__init__(msg)


class DatabaseException(TaskException):
    def __init__(self, error):
        super().__init__("Database error")
        self.error = error