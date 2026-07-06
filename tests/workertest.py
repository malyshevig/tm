import unittest

from tm import Worker
from tm.mgr import TaskManager
from tm.model import NewTask


class WorkerTest(unittest.TestCase):
    def test_create(self):
        wk =  Worker(1, "docling")

        task = {"src_file": "/tmp/1,txt", "dst_dir": "/tmp"}
        wk.create_task("docling", task)

        print (f"task = {task}")


if __name__ == '__main__':
    unittest.main()