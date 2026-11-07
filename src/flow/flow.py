from tm import Worker


class Flow(Worker):
    def __init__(self, worker_id, task_type):
        super().__init__(worker_id, task_type)



