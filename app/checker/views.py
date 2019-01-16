import time
import random

from flask import jsonify, render_template, request, url_for, abort, flash
from flask_login import login_required

from . import checker
from .. import celery, db
from ..admin.views import require_admin
from ..models import Dataset, CheckerDataset


@celery.task(bind=True)
def start_checker_task(self, dataset_id):
    time.sleep(5)
    total = random.randint(90,100)
    for i in range(total):
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total,
                  'status': 'Working...'}
        )
        time.sleep(1)

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@checker.route('/checkerstart/dataset<int:dataset_id>', methods=['POST'])
@login_required
@require_admin
def startchecker(dataset_id):
    checker_task = start_checker_task.delay(dataset_id=dataset_id)
    flash(checker_task.id)
    checker_dataset = CheckerDataset.query.filter_by(dataset_id=dataset_id).first()

    if not checker_dataset:
        checker_dataset = CheckerDataset(dataset_id=dataset_id, 
                                        celery_task_id=checker_task.id,
                                        progress=0)
        db.session.add(checker_dataset)

    else:
        checker_dataset.celery_task_id=checker_task.id
        checker_dataset.progress=0

    try:
        db.session.commit()
    except:
        db.session.rollback()
        flash('Error: database could not be reached')
        abort(400)

    return jsonify({}), 202, {'Location': url_for('checker.checkerstatus',
                                                  task_id=checker_task.id)}


@checker.route('/checkerstatus', methods=['GET'])
def checkerstatus():
    ds_id = request.args.get('dsid')
    if not ds_id:
        abort(400)
    dataset = Dataset.query.get_or_404(ds_id)
    checkerds = dataset.checker_dataset

    response = {
        'running': True,
        'progress': checkerds.progress,
        'status': 'Test status'
    }
    return jsonify(response)


# @checker.route('/checkerstatus/<task_id>')
# def checkerstatus(task_id):
#     checker_task = start_checker_task.AsyncResult(task_id)
#     if checker_task.state == 'PENDING':
#         response = {
#             'state': checker_task.state,
#             'current': 0,
#             'total': 1,
#             'status': 'Pending...'
#         }
#     elif checker_task.state != 'FAILURE':
#         response = {
#             'state': checker_task.state,
#             'current': checker_task.info.get('current', 0),
#             'total': checker_task.info.get('total', 1),
#             'status': checker_task.info.get('status', 'Failed...')
#         }
#         if 'result' in checker_task.info:
#             response['result'] = checker_task.info['result']
#     else:
#         response = {
#             'state': checker_task.state,
#             'current': 1,
#             'total': 1,
#             'status': str(checker_task.info)
#         }

#     return jsonify(response)


@checker.route('/checkerrunning', methods=['GET'])
def checkerrunning():
    ds_id = request.args.get('dsid')
    if not ds_id:
        abort(400)
    dataset = Dataset.query.get_or_404(ds_id)

    response = {
        'running': dataset.checker_running()
    }
    return jsonify(response)
