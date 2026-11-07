from flow.flow import Flow


class BookFlow(Flow):
    task_type = "book_process_flow"

    def __init__(self, worker_id):
        super().__init__(worker_id, BookFlow.task_type)

    def run(self):
        with self.get_task_cycle() as task:
            file_id = task.details["file_id"]
