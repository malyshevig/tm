import logging
import time

from tm.mgr import TaskManager
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")
logger = logging.getLogger(__name__)


class Audit:
    def __init__(self, id):
        self.id = id


    def run(self):

        task_manager = TaskManager()
        while True:
            row_count= task_manager.audit(self.id)
            logger.info(f"Audit id: {self.id} , updated:{row_count}")
            time.sleep(10)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Task Manager service"
    )

    # Опциональный аргумент с коротким (-o) и длинным (--output) именем
    parser.add_argument(
        "-i", "--id",
        default="1",
        help="Audit id"
    )

    # Аргумент с ограниченным списком возможных значений (choices)

    # 3. Парсим аргументы из командной строки
    args = parser.parse_args()
    audit_id = args.id

    Audit(audit_id).run()