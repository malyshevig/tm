import unittest

from bookflow import BookFlowTasks
from bookflow.action_isbn import BooksAction


class FlowTest(unittest.TestCase):

    def test_flow(self):
        BookFlowTasks().get_isbn(file_id="name")


class ActionTest(unittest.TestCase):

    def test_action(self):
        BooksAction().get_isbn("")