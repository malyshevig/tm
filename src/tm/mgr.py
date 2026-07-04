import logging
from ast import dump
from contextlib import contextmanager
from typing import Callable, Any

import psycopg2
import psycopg2.pool as pool
import psycopg2.extras

from tm import model
from tm.errors import TaskNotFound, IncorrectWorkerId, IncorrectTaskStatusForOperation, DatabaseException, TaskException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")
logger = logging.getLogger(__name__)

from tm.model import TaskInfo, NewTask

_pool = pool.ThreadedConnectionPool(1, 20, user="tm",
                                    password="begemot",
                                    host="gek",
                                    port="5432",
                                    database="tm")


@contextmanager
def get_client():
    client = _pool.getconn()
    try:
        yield client
    finally:
        client.close()


class TaskManager:

    def __init__(self):

        pass

    # Вариант 3: SELECT с преобразованием в Pydantic модель (рекомендуется)
    def get_task_by_id(self, task_id: int) -> TaskInfo | None:
        with get_client() as conn:
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    sql = """
                        SELECT task_id, created_dt, updated_dt, task_type, 
                               details, status, worker_id, update_details, fail_count
                        FROM tasks
                        WHERE task_id = %s
                    """
                    cursor.execute(sql, (task_id,))
                    row = cursor.fetchone()

                    if row:
                        return TaskInfo(**row)
                    return None
            except psycopg2.Error as e:
                logger.error(e)
                raise e


    def get_task_by_type_status(self, task_type: str, task_status: str) -> list[TaskInfo]:
        with get_client() as conn:
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    sql = """
                           SELECT task_id, created_dt, updated_dt, task_type, 
                                  details, status, worker_id, update_details, fail_count
                           FROM tasks
                           WHERE task_type = %s and status = %s 
                       """
                    cursor.execute(sql, (task_type, task_status))
                    rows = cursor.fetchall()

                    return [TaskInfo(**row) for row in rows]
            except psycopg2.Error as e:
                logger.error(e)
                raise e

    def create(self, task: NewTask) -> TaskInfo:
        insert_task_sql = '''
                     insert into tasks (
                         task_type, details, status  
                     )
                     values (%(task_type)s, %(details)s, %(status)s)
                     returning task_id;
                     '''

        with get_client() as client:
            try:
                cursor = client.cursor()
                params = task.model_dump()
                params['details'] = psycopg2.extras.Json(params['details'])

                cursor.execute(insert_task_sql, params)
                client.commit()
                new_id = cursor.fetchone()[0]
                task = self.get_task_by_id(new_id)
                if task is None:
                    raise
                else:
                    return task

            except psycopg2.Error as e:
                logger.error(e)
                raise e


    def get_tasks(self, limit:int, offset:int):
        with get_client() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Общее количество
                sql = """
                    SELECT task_id, created_dt, updated_dt, task_type, 
                           details, status, worker_id, update_details, fail_count
                    FROM tasks
                    ORDER BY task_id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                """
                cursor.execute(sql, {
                    'limit': limit,
                    'offset': offset
                })
                rows = cursor.fetchall()

                tasks = [TaskInfo(**row) for row in rows]
                return tasks


    def assign_task(self, worker_id: str, task_type: str):
        with get_client() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                sql = """
                        WITH next_task AS (
                            SELECT task_id
                            FROM tasks
                            WHERE status = 'idle' and task_type = %(task_type)s
                            ORDER BY created_dt ASC
                            LIMIT 1
                            FOR UPDATE SKIP LOCKED
                        )
                        UPDATE tasks
                        SET status = %(new_status)s,
                            updated_dt = now(),
                            worker_id = %(worker_id)s
                        WHERE task_id = (SELECT task_id FROM next_task)
                        RETURNING task_id, created_dt, updated_dt, task_type, 
                                  details, status, worker_id, update_details, fail_count
                    """
                cursor.execute(sql, {'worker_id': worker_id, 'task_type': task_type,
                                     'new_status': model.TASK_STATUS_ASSIGNED})
                row = cursor.fetchone()

                if row:
                    conn.commit()
                    return TaskInfo(**row)
                else:
                    conn.rollback()
                    raise None


    def assert_task_status(self, cursor, task_id: int, worker_id: str, status: str) -> TaskInfo:
        task = None
        try:
            sql = """
                            SELECT task_id, created_dt, updated_dt, task_type, 
                                   details, status, worker_id, update_details, fail_count
                            FROM tasks
                            WHERE task_id = %s
                            FOR UPDATE
                        """
            cursor.execute(sql, (task_id,))
            row = cursor.fetchone()

            task = TaskInfo(**row) if row is not None else None

        except psycopg2.Error as e:
            logger.error(e)
            raise e


        if task is None:
            raise TaskNotFound(task_id=task_id)

        if task.status != status:
            raise IncorrectTaskStatusForOperation(task_id=task_id, status=task.status)

        if worker_id != task.worker_id:
            raise IncorrectWorkerId(worker_id=worker_id, task_id=task_id)


        return task

    def accept(self, task_id: int, worker_id: str):
        try:
            with get_client() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # Assert inside transaction
                    self.assert_task_status(cursor, task_id, worker_id, model.TASK_STATUS_ASSIGNED)

                    sql = """
                        UPDATE tasks
                        SET status = %(status)s,
                            updated_dt = now()
                        WHERE task_id = %(task_id)s
                        """
                    cursor.execute(sql, {'task_id': task_id, 'status': model.TASK_STATUS_IN_PROGRESS})
                    conn.commit()
                    return cursor.rowcount > 0
        except psycopg2.Error as e:
            logger.error(e)
            raise DatabaseException(e)
        except TaskException as e:
            raise e


    def _update(self, worker_id, task_id:int, details:dict[str, Any],
                new_status: str= None, increase_fail_count: bool=False):

        try:
            with get_client() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    self.assert_task_status(cursor, task_id, worker_id, model.TASK_STATUS_IN_PROGRESS)

                    sql = """UPDATE tasks
                            SET update_details = %(details)s,
                                updated_dt = now()
                        """
                    if new_status:
                        sql += " , status = %(new_status)s"
                    if increase_fail_count:
                        sql += " , fail_count = fail_count + 1"

                    sql += """WHERE
                            task_id = %(task_id)s
                            """

                    details = psycopg2.extras.Json(details)
                    params = {'task_id': task_id, 'details': details, "new_status": new_status}

                    cursor.execute(sql, params)
                    conn.commit()

            return cursor.rowcount > 0
        except psycopg2.Error as e:
            logger.error(e)
            raise DatabaseException(e)
        except TaskException as e:
            raise e


    def update(self, worker_id, task_id:int, details:dict[str, Any]):
        return self._update(worker_id, task_id, details)

    def complete(self, worker_id, task_id:int, details:str):
        return self._update(worker_id, task_id, details, new_status=model.TASK_STATUS_COMPLETED)

    def fail(self, worker_id, task_id:int, details:str):
        try:
            with get_client() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    task = self.assert_task_status(cursor, task_id, worker_id, model.TASK_STATUS_IN_PROGRESS)

                    fail_count = task.fail_count + 1
                    new_status = model.TASK_STATUS_IDLE
                    if fail_count > model.MAX_FAILURES_ALLOWED:
                        new_status = model.TASK_STATUS_FAILED

                    sql = """
                            UPDATE tasks
                            SET update_details = %(details)s,
                                fail_count = fail_count + 1, 
                                updated_dt = now(),
                                status = %(new_status)s
                            WHERE
                                task_id = %(task_id)s
                            """

                    details = psycopg2.extras.Json(details)
                    params = {'task_id': task_id, 'details': details, 'new_status': new_status}

                    cursor.execute(sql, params)
                    conn.commit()

            return cursor.rowcount > 0
        except psycopg2.Error as e:
            logger.error(e)
            raise DatabaseException(e)
        except TaskException as e:
            raise e
