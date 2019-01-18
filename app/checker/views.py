import random
import time

from flask import (abort, current_app, flash, jsonify, render_template,
                   request, url_for)
from flask_login import login_required

from . import checker
from .. import celery, db
from ..admin.views import require_admin
from ..models import CheckerDataset, Dataset


@celery.task(bind=True)
def start_checker_task(self, dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    time.sleep(5)
    total = random.randint(90,100)
    for i in range(total):
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total,
                  'status': 'Working...'}
        )
        time.sleep(1)

    dataset.checker_dataset.completed = True
    try:
        db.session.commit()
    except:
        db.session.rollback()

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@checker.route('/checkerstart/dataset<int:dataset_id>', methods=['POST'])
@login_required
@require_admin
def startchecker(dataset_id):
    checker_task = start_checker_task.delay(dataset_id=dataset_id)
    checker_dataset = CheckerDataset.query.filter_by(dataset_id=dataset_id).first()

    if not checker_dataset:
        checker_dataset = CheckerDataset(dataset_id=dataset_id, 
                                         celery_task_id=checker_task.id)
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

    return jsonify({'task_id': checker_task.id}), 202


@checker.route('/checkerstatus')
def checkerstatus():
    task_id = request.args.get('taskid')
    if not task_id:
        abort(400)
    checker_task = start_checker_task.AsyncResult(task_id)
    
    if checker_task.state == 'PENDING':
        current_app.logger.debug('PENDING...')
        response = {
            'state': checker_task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif checker_task.state != 'FAILURE':
        current_app.logger.debug("{}: {}/{} - {}"\
        .format(checker_task.state, checker_task.info.get('current',0), 
                checker_task.info.get('total',1), 
                checker_task.info.get('status', 'Failed')))
        response = {
            'state': checker_task.state,
            'current': checker_task.info.get('current', 0),
            'total': checker_task.info.get('total', 1),
            'status': checker_task.info.get('status', 'Failed...')
        }
        if 'result' in checker_task.info:
            response['result'] = checker_task.info['result']
    else:
        response = {
            'state': checker_task.state,
            'current': 1,
            'total': 1,
            'status': str(checker_task.info)
        }

    return jsonify(response)


@checker.route('/checkerrunning', methods=['GET'])
def checkerrunning():
    ds_id = request.args.get('dsid')
    if not ds_id:
        abort(400)
    dataset = Dataset.query.get_or_404(ds_id)

    response = {
        'running': dataset.checker_running(),
        'complete': dataset.checker_completed(),
        'task_id': dataset.checker_task_id()
    }
    
    return jsonify(response)
