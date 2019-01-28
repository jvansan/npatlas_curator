from celery.utils.log import get_task_logger
from flask import (abort, current_app, flash, jsonify, render_template,
                   request, url_for, redirect)
from flask_login import login_required

from .forms import SimpleIntForm, SimpleStringForm
from . import checker
from .. import celery, db
from ..admin.views import require_admin
from ..models import (CheckerDataset, Dataset, Problem, CheckerArticle,
                      CheckerCompound)
from .Checker import Checker

logger = get_task_logger(__name__)


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')


@celery.task(bind=True)
def start_checker_task(self, dataset_id, standardize_compounds=False):

    checker = Checker(dataset_id, celery_task=self, logger=logger)
    checker.run(standardize_compounds=standardize_compounds)
    result = "/admin/resolve/dataset{}".format(dataset_id) 

    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': result}


@checker.route('/checkerstart/dataset<int:dataset_id>', methods=['POST'])
@login_required
@require_admin
def startchecker(dataset_id):
    standard = bool(request.args.get("standard", False))
    current_app.logger.info("Compound standardization is %s", 
                            "ON" if standard else "OFF")
    checker_task = start_checker_task.delay(dataset_id=dataset_id, 
                                            standardize_compounds=standard)
    checker_dataset = CheckerDataset.query.filter_by(dataset_id=dataset_id).first()

    if not checker_dataset:
        checker_dataset = CheckerDataset(dataset_id=dataset_id, 
                                         celery_task_id=checker_task.id)
        db.session.add(checker_dataset)

    else:
        checker_dataset.celery_task_id = checker_task.id
        checker_dataset.completed = False

    try:
        db.session.commit()
    except:
        db.session.rollback()
        flash('Error: database could not be reached')
        abort(400)

    return jsonify({'task_id': checker_task.id}), 202


@checker.route('/checkerstatus')
@login_required
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
@login_required
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


@checker.route('/admin/resolve/dataset<int:ds_id>')
@login_required
@require_admin
def problem_list(ds_id):
    problems = Problem.query.filter_by(dataset_id=ds_id).all()
    return render_template('checker/problems.html', ds_id=ds_id,
        problems=problems)


@checker.route('/admin/resolve/dataset<int:ds_id>/problem<int:prob_id>',
               methods=['GET', 'POST'])
@login_required
@require_admin
def resolve_problem(ds_id, prob_id):
    # Get all the necessary data from the database
    problem = Problem.query.get_or_404(prob_id)
    article = CheckerArticle.query.get_or_404(problem.article_id)
    if problem.compound_id:
        compound = CheckerCompound.query.get_or_404(problem.compound_id)
    else:
        compound = None

    # Make sure problem is associated with this dataset
    if problem.dataset_id != ds_id:
        abort(404)
    form = None
    if problem.problem == "journal":
        pass
    elif problem.problem == "genus":
        pass
    elif problem.problem == "flat_match" or problem.problem == "duplicate":
        pass
    else:
        form = simple_problem_form_factory(problem, article)

    
    if (form.validate_on_submit() or form.force.data):
        flash("Form submitted!")
        return redirect(url_for('checker.problem_list', ds_id=ds_id))
    
    else:
        flash_errors(form)

    return render_template('checker/resolve.html', ds_id=ds_id,
                           problem=problem, article=article, form=form)


def simple_problem_form_factory(problem, article):
    if problem.problem == "year":
        form = create_numeric_form(article.year, problem.problem)
    elif problem.problem == "pmid":
        form = create_numeric_form(article.pmid, problem.problem)
    elif problem.problem == "doi":
        form = create_string_form(article.doi, problem.problem)
    elif problem.problem == "volume":
        form = create_string_form(article.volume, problem.problem)
    elif problem.problem == "issue":
        form = create_string_form(article.issue, problem.problem)
    elif problem.problem == "authors":
        form = create_string_form(article.authors, problem.problem)
    elif problem.problem == "title":
        form = create_string_form(article.title, problem.problem)
    elif problem.problem == "pages":
        form = create_string_form(article.pages, problem.problem)
    elif problem.problem == "abstract":
        form = create_string_form(article.abstract, problem.problem)
    return form

def create_numeric_form(value, type_):
    return SimpleIntForm(value=value, type_=type_)

def create_string_form(value, type_):
    return SimpleStringForm(value=value, type_=type_)