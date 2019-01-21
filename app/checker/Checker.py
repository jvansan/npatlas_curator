import time, random

from .. import db
from ..models import Dataset

class Checker(object):

    def __init__(self, dataset_id, celery_task=None):
        self.dataset_id = dataset_id
        self.task = celery_task

    def run(self):
        dataset = Dataset.query.get_or_404(dataset_id)
        total = random.randint(90,100)

        for i in range(total):
            if self.task:
                self.task.update_state(
                    state='PROGRESS',
                    meta={'current': i, 'total': total,
                        'status': 'Working...'}
                )
            else:
                print("PROGRESS: {}".format(total))

            time.sleep(1)

        dataset.checker_dataset.completed = True
        self.commit()
    
    def commit(self):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        