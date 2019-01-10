from functools import wraps

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import admin
from .. import db
from ..data import data
from ..data.forms import ArticleForm, CompoundForm
from ..models import Article, Compound, Curator, Dataset
from .forms import CuratorForm


def require_admin(func):
    """
    Decorator to prevent non-admins from accessing the page
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return decorated_function


@admin.route('/admin/datasets')
@login_required
@require_admin
def list_datasets():
    """
    List all datasets and give checker access
    """
    # Get page
    page = request.args.get('page', 1, type=int)

    datasets = Dataset.query.order_by(Dataset.id.desc()).paginate(page, 10, False)

    next_url = url_for("admin.list_datasets", page=datasets.next_num)\
        if datasets.has_next else None
    prev_url = url_for("admin.list_datasets", page=datasets.prev_num)\
        if datasets.has_prev else None

    return render_template('admin/datasets.html', datasets=datasets, title='Add Datasets',
                           next_url=next_url, prev_url=prev_url)


@admin.route('/admin/articles')
@login_required
@require_admin
def list_articles():
    """
    List all articles
    """
    page = request.args.get('page', 1, type=int)
    articles = Article.query.paginate(page, 10, False)

    next_url = url_for("admin.list_articles", page=articles.next_num)\
        if articles.has_next else None
    prev_url = url_for("admin.list_articles", page=articles.prev_num)\
        if articles.has_prev else None

    return render_template('admin/articles/articles.html', articles=articles, title='All Articles',
                            article_redirect=lambda x: url_for('admin.article', id=x),
                            next_url=next_url, prev_url=prev_url)


@admin.route('/admin/articles/article<int:id>', methods=['GET', 'POST'])
@login_required
@require_admin
def article(id):
    """
    See article from admin perspective
    """
    # Get article from DB and populate form
    article = Article.query.get_or_404(id)

    form = ArticleForm(obj=article)

    if form.validate_on_submit():
        form.populate_obj(article)

        actual_cmpds = []
        for cmpd in form.compounds:
            cmpd_form = cmpd.form
            db_cmpd = None
            if cmpd_form.id.data:
                db_cmpd = Compound.query.get(cmpd_form.id.data)
            if not db_cmpd:
                db_cmpd = Compound()

            db_cmpd.name = cmpd_form.name.data
            db_cmpd.smiles = cmpd_form.smiles.data
            db_cmpd.source_organism = cmpd_form.source_organism.data
            db_cmpd.cid = cmpd_form.cid.data
            db_cmpd.csid = cmpd_form.csid.data
            db_cmpd.cbid = cmpd_form.cbid.data

            if not db_cmpd.id:
                db.session.add(db_cmpd)

            actual_cmpds.append(db_cmpd)

        article.compounds = actual_cmpds

        try:
            db.session.commit()
            flash('Data saved!')
        except:
            db.session.rollback()
            flash('Error sending data to database...')

        return redirect(url_for('admin.list_articles'))

    return render_template('data/article.html', title='Article', form=form)


@admin.route('/admin/curators')
@login_required
@require_admin
def list_curators():
    """
    List all curators
    """
    curators = Curator.query.all()

    return render_template('admin/curators/curators.html', curators=curators, title='Curators',
                            data_redirect=lambda x: url_for('data.curator_dashboard', cur_id=x)
                            )


@admin.route('/admin/curators/add', methods=['GET', 'POST'])
@login_required
@require_admin
def add_curator():
    """
    Add a curator to the database
    """
    add_curator = True
    form = CuratorForm()
    if form.validate_on_submit():
        curator = Curator(email=form.email.data,
                          username=form.username.data,
                          first_name=form.first_name.data,
                          last_name=form.last_name.data,
                          password=form.password.data)
        try:
            db.session.add(curator)
            db.session.commit()
            flash('You have successfully added a new curator.\nNote the password is {}'\
                    .format(form.password.data))
        except:
            db.session.rollback()
            flash('Error: Curator already exists')

        return redirect(url_for('admin.list_curators'))

    return render_template('admin/curators/curator.html', action="Add",
                       add_curator=add_curator, form=form,
                       title='Add Curator')


@admin.route('/admin/curators/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@require_admin
def edit_curator(id):
    """
    Edit a curator to the database
    """
    add_curator = False

    curator = Curator.query.get_or_404(id)
    form = CuratorForm(obj=curator)
    if form.validate_on_submit():
        curator.email = form.email.data
        curator.username = form.username.data
        curator.first_name = form.first_name.data
        curator.last_name = form.last_name.data
        curator.password = form.password.data
        try:
            db.session.commit()
            flash('You have successfully added a new curator.\nNote the password is {}'\
                    .format(form.password.data))
        except:
            db.session.rollback()
            flash('Error: Curator data could not be edited.')

        return redirect(url_for('admin.list_curators'))

    form.email.data = curator.email
    form.username.data = curator.username
    form.first_name.data = curator.first_name
    form.last_name.data = curator.last_name

    return render_template('admin/curators/curator.html', action="Edit",
                           add_curator=add_curator, form=form,
                           title='Edit Curator')
