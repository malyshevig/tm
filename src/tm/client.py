import json
import logging
import uuid
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")
logger = logging.getLogger(__name__)

class TMClient():
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 10
        self.max_retries = 3

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)


    def _build_update_payload(self, update_details: dict) -> dict:
        if update_details is None:
            update_details = {}

        return {
            "details": json.dumps(update_details),
        }


    def create_task (self, task_type: str, details: dict):
        session = requests.Session()

        url = f"{self.base_url}/tm/api/v1/tm/task"
        payload = self._build_update_payload(details)
        payload["task_type"] = task_type
        idempotency_key = str(uuid.uuid4())

        headers = {
            "Idempotency-Key": idempotency_key
        }

        response = self.session.request(method="POST", url=url, data=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        session.close()


    def update_task(self, worker_id, task_id, details):
        logger.info(f"update task {task_id}")

        try:
            url = f"{self.base_url}/tm/api/v1/worker/{worker_id}/task/{task_id}/update"
            payload = self._build_update_payload(details)
            response = self.session.request(method="POST", data=payload, url=url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for task {task_id}: {e.response.text}")
            raise e
        except Exception as e:
            logger.exception(f"Unexpected error processing task {task_id}: {e}")
            raise e