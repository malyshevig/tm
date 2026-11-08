from bookflow import BookFlowTasks
from flow.proxy import workflow_action


class BooksAction(BookFlowTasks):

    @workflow_action(workflow_id="bookflow")
    def get_isbn(self, file_id:str):
        print (f"Getting isbn for file_id={file_id}" )