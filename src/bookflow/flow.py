from flow.flow import Flow
from tasks import BookFlowTasks





class BookFlow(Flow):
    task_type = "book_process_flow"

    def __init__(self, worker_id):
        super().__init__(worker_id, BookFlow.task_type)

    def run(self):
        taskMgr = BookFlowTasks()

        with self.get_task_cycle() as task:
            file_id = task.details["file_id"]
            isbn_details = taskMgr.get_isbn(file_id)
            if isbn_details:
                task.get_