import json
import logging
import threading
import time
import uuid
from contextlib import contextmanager

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from tm import model



logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")
logger = logging.getLogger(__name__)


class Worker():
    def __init__(self, worker_id, task_type):
        self.session = requests.Session()
        self.timeout = 10
        self.max_retries = 3
        self.worker_id = worker_id
        self.task_type = task_type
        self.poll_period = 10
        self.server = "http://localhost:8200"

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def request_assign (self):
        url =  f"{self.server}/tm/api/v1/worker/{self.worker_id}/{self.task_type}/assign"
        response = self.session.request(method="POST", url=url, timeout=self.timeout)
        if response.status_code == 404:
            return None

        response.raise_for_status()

        return model.Task(**response.json())

    def request_accept(self, task: model.Task):
        url = f"{self.server}/tm/api/v1/worker/{self.worker_id}/task/{task.task_id}/accept"
        response = self.session.request(method="POST", url=url, timeout=self.timeout)
        response.raise_for_status()

        return task

    def _build_update_payload(self, update_details: dict) -> dict:
        if update_details is None:
            update_details = {}

        return {
            "details": json.dumps(update_details),
        }

    def request_update(self, task: model.Task):
        logger.info(f"update task {task}")

        try:
            url = f"{self.server}/tm/api/v1/worker/{self.worker_id}/task/{task.task_id}/update"
            payload = self._build_update_payload(task.update_details)
            response = self.session.request(method="POST", data=payload, url=url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for task {task.task_id}: {e.response.text}")
            raise e
        except Exception as e:
            logger.exception(f"Unexpected error processing task {task.task_id}: {e}")
            raise e


    def request_complete(self, task: model.Task):

        payload = self._build_update_payload(task.update_details)

        url = f"{self.server}/tm/api/v1/worker/{self.worker_id}/task/{task.task_id}/completed"
        response = self.session.request(method="POST", url=url, data=payload, timeout=self.timeout)
        response.raise_for_status()

    def request_failed(self, task: model.Task):
        payload = self._build_update_payload(task.update_details)

        url = f"{self.server}/tm/api/v1/worker/{self.worker_id}/task/{task.task_id}/failed"
        response = self.session.request(method="POST", url=url, data=payload, timeout=self.timeout)
        response.raise_for_status()

    def get_task (self):
        try:
            task = self.request_assign()
            if task:
                task = self.request_accept(task)
                if task:
                    return task
            else:
                    return None

        except Exception as e:
            logger.error(e)
            raise e

    def get_task_cycle (self):
              while True:
                task = self.get_task()
                if task is not None:
                    return task
                time.sleep(self.poll_period)


    @contextmanager
    def take_task(self):
        task: model.Task = None
        thread: threading.Thread = None

        stop_event = threading.Event()
        task = (self.get_task_cycle())
        logger.info(f"worker process task {task}")

        try:
            def _worker():
                logger.info(f"worker process task {task}")

                while not stop_event.is_set():
                    logger.info(f"[Worker] tick at {time.strftime('%H:%M:%S')}")

                    self.request_update(task)
                    stop_event.wait(self.poll_period)  # ← Прерываемый sleep!
                logger.info("[Worker] stopped gracefully")

            thread = threading.Thread(target=_worker, daemon=True, name="bg-worker")
            thread.start()
            yield task
            logger.info(f"worker complete task {task}")
            self.request_complete(task)

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for task {task.task_id}: {e.response.text}")
        except Exception as e:
            logger.error(e)
            logger.info(f"worker fail task {task}")
            self.request_failed(task)
        finally:
            stop_event.set()  # Сигнализируем потоку остановиться
            if thread is not None:
                thread.join(timeout=self.poll_period)


    def create_task (self, task_type: str, details: dict):
        url =  f"{self.server}/tm/api/v1/tm/task"
        payload = self._build_update_payload(details)
        payload["task_type"] = task_type
        idempotency_key = str(uuid.uuid4())

        headers = {
            "Idempotency-Key": idempotency_key
        }

        response = self.session.request(method="POST", url=url, data=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()



def main():
    worker = Worker(worker_id=1, task_type="docling")
    while True:
        with worker.take_task() as task:
            logger.info(f"worker process task {task.details}")
            for i in range(10):
                task.update_details = {"updated": f"{i*100/10} %" }
                time.sleep(5)

            task.update_details = {"updated": f"{100} %" }


if __name__ == "__main__":
        main()