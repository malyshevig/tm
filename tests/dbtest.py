import unittest

from tm.mgr import TaskManager
from tm.model import NewTask


class TestStringMethods(unittest.TestCase):

    def test_conn(self):
        pass

    def test_create(self):
        tm = TaskManager()
        task =tm.create(task=NewTask(task_type='docling', details={'file': '/tmp/1,pdf'}, status='idle'))
        print (f"task = {task}")

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()