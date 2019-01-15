import time
import random

from flask import jsonify, render_template, request, url_for, abort
from flask_login import login_required

from . import checker
from .. import celery
from ..admin.views import require_admin
from ..models import Dataset


@celery.task(bind=True)
def start_checker_task(dataset_id):
    time.sleep(5)
    total = random.randint(10,100)
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
    checker_task = start_checker_task.delay(dataset_id)
    return jsonify({}), 202, {'Location': url_for('checkerstatus',
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
