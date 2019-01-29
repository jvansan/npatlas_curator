import os
import json
from collections import Counter
from flask import (abort, flash, redirect, render_template, url_for,
                   request, jsonify, session, current_app)
from flask_login import current_user, login_required
from rdkit.Chem import AllChem as Chem
from requests.exceptions import RequestException

from . import data
from .. import db, celery
from .forms import ArticleForm
from ..models import Article, Dataset, Compound, Curator, dataset_article
from ..utils.pubchem_smiles_standardizer import get_standardized_smiles
from ..utils.NoneDict import NoneDict


#####################################################################
###                      SERVER VIEWS/METHODS                     ###
#####################################################################
@data.route("/data")
@login_required
def data_redirect():
    """
    Redirect user to dashboard
    """
    return redirect(url_for('data.curator_dashboard', cur_id=current_user.id))


@data.route('/data/curator<int:cur_id>')
@login_required
def curator_dashboard(cur_id):
    """
    Render data dashboard template at '/data/curator<int:id>'
    """
    # Get curator from DB
    curator = Curator.query.get_or_404(cur_id)

    # Make sure current user or admin
    if not current_user.is_admin and cur_id != current_user.id:
        abort(403)

    datasets = Dataset.query.order_by(Dataset.id.desc())\
               .filter_by(curator_id=cur_id).all()

    return render_template('data/dashboard.html', title='Data Dashboard',
                           datasets=datasets, curator=curator,
                           article_redirect=article_redirect,
                           dataset_redirect=dataset_redirect,
                           training_score_redirect=training_score_redirect)


@data.route('/data/curator<int:cur_id>/dataset<int:ds_id>/trainingscore',
            methods=['GET', 'POST'])
@login_required
def trainingscore(cur_id, ds_id):
    """Score and render training set diffs at 
       '/data/curator<int:id>/dataset<int:ds_id>/traningset'
    """
    # Check that scoring scheme JSON exists
    # load it if it does
    # Throw 500 error if not
    ts_path = os.path.join('app','static','training-set.json')
    current_app.logger.debug("Loading training set solutions, {}".format(ts_path))
    if not os.path.isfile(ts_path):
        current_app.logger.debug("Training set file could not be loaded")
        abort(500)
    else:
        with open(ts_path, 'r') as f:
            training_set_data = json.load(f)
        current_app.logger.debug("Successfully got training set solutions")

    # Get dataset
    dataset = Dataset.query.get_or_404(ds_id)

    # Check user is allowed to access dataset
    if dataset.curator_id != current_user.id and not current_user.is_admin:
        abort(403)

    # Check dataset is actually training set
    if not dataset.training:
        abort(404)

    current_app.logger.debug("Starting scoring dataset.")
    # Iterate over dataset and make scoring comparisons
    score = 10
    errors = []
    for idx, art in enumerate(dataset.articles):
        minus_score = 0
        training_solution = training_set_data.get("{}".format(idx+1))
        if not training_solution:
            current_app.logger.error("Could not get the correct solution...")

        # Make sure article was accepted or rejected correctly
        if art.is_nparticle != (not training_solution.get("reject")):
            current_app.logger.debug("Incorrect IS NPARTICLE")
            errors.append({
                "artid": art.id,
                "type": "Article Rejected",
                "expected": training_solution.get("reject"),
                "actual": not art.is_nparticle
            })
            minus_score += 1

        # Ignore the rest of scoring for rejected articles
        if not training_solution.get("reject"):
            # Make sure compound count is correct
            if art.num_compounds != training_solution.get("count"):
                current_app.logger.debug("Incorrect Compound Count")
                errors.append({
                    "artid": art.id,
                    "type": "Compound Count",
                    "expected": training_solution.get("count"),
                    "actual": art.num_compounds
                })
                minus_score += 1

            # Check names match
            names = [x.name for x in art.compounds]
            if Counter(map(str.lower, names)) != Counter(map(str.lower, training_solution.get("names"))):
                current_app.logger.debug("Incorrect Compound Name")
                errors.append({
                    "artid": art.id,
                    "type": "Incorrect Compound Name(s)",
                    "expected": training_solution.get("names"),
                    "actual": names
                })
                minus_score += 1

        if minus_score >= 1:
            score = score - 1
    current_app.logger.debug("Completed scoring dataset")
    current_app.logger.debug("Score for {} was {}/10".format(current_user.username, score))

    return render_template("data/trainingscore.html", title="Training Set Score",
                           cur_id=cur_id, ds_id=ds_id,
                           score=score, errors=errors,
                           article_redirect=article_redirect)


@data.route('/data/curator<int:cur_id>/dataset<int:ds_id>',
            methods=['GET', 'POST'])
@login_required
def dataset(cur_id, ds_id):
    """
    Render article list for dataset
    """
    # Get page
    page = request.args.get('page', 1, type=int)

    # Get dataset from DB
    dataset = Dataset.query.get_or_404(ds_id)

    # Check user is allows to access dataset
    if dataset.curator_id != current_user.id and not current_user.is_admin:
        abort(403)

    articles = dataset.get_articles().paginate(page, 10, False)

    next_url = url_for("data.dataset", page=articles.next_num,
                       cur_id=cur_id, ds_id=ds_id)\
        if articles.has_next else None
    prev_url = url_for("data.dataset", page=articles.prev_num,
                       cur_id=cur_id, ds_id=ds_id)\
        if articles.has_prev else None

    return render_template('data/articles.html', cur_id=cur_id,
                           ds_id=ds_id, articles=articles,
                           title='Dataset {}'.format(dataset.id),
                           article_redirect=article_redirect,
                           next_url=next_url,
                           prev_url=prev_url)


@data.route('/data/curator<int:cur_id>/dataset<int:ds_id>/article<int:art_id>',
            methods=['GET', 'POST'])
@login_required
def article(cur_id, ds_id, art_id):
    """
    Render article curation form
    """
    # Get article from DB and populate form
    article = Article.query.get_or_404(art_id)
    # Flash Error About Non-NP Article
    if not article.is_nparticle:
        flash("Article previously flagged as not about natural product isolation!",
              "danger")
    # Get dataset from DB
    dataset = Dataset.query.get_or_404(ds_id)

    # Make sure user has access to article
    if article not in dataset.articles and not current_user.is_admin:
        abort(403)
    if dataset.curator_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = ArticleForm(obj=article)

    # if form.add_compound.data:
    #     form.compounds.append_entry()

    if (form.validate_on_submit() or (form.is_submitted() and
        ((form.needs_work.data) or form.reject.data))):
        # Variable to track if on last article but unfinished dataset
        skip = False

        form.populate_obj(article)

        # Get compounds from forms and save to article
        actual_cmpds = get_article_compounds(form)
        article.compounds = actual_cmpds

        # Determine if article was rejected
        # Also allow for change
        if form.reject.data:
            article.is_nparticle = False
        elif form.submit.data:
            article.is_nparticle = True

        # Session tracking
        article.completed = True
        if len([art for art in dataset.articles if art.completed]) == len(dataset.articles):
            dataset.completed = True
            if not dataset.training:
                standardize_dataset.delay(ds_id)
            flash('Dataset completed!!')
        elif dataset.articles.index(article) == len(dataset.articles) - 1:
            skip = True
            flash("Please go back and complete unfinished articles!")

        # Get next article_id dataset
        if not dataset.completed and not skip:
            current_dataset_idx = dataset.articles.index(article)
            next_dataset_idx = current_dataset_idx + 1
            next_art_id = dataset.articles[next_dataset_idx].id
            dataset.last_article_id = next_art_id

        try_dbcommit()
        # Clear session cookie
        session.pop('compound', None)
        session.pop('_flashes', None)

        if dataset.completed or skip:
            if dataset.training:
                return redirect(url_for('data.trainingscore',
                                cur_id=current_user.id,
                                ds_id=ds_id))
            else:
                return redirect(url_for('data.curator_dashboard',
                                cur_id=current_user.id))

        else:
            return redirect(url_for('data.article', cur_id=cur_id,
                                    ds_id=ds_id, art_id=next_art_id))
    else:
        flash_errors(form)

    # Retrieve session cookie to redirect to correct compound
    try:
        compId = session['compound']
    except KeyError:
        compId = None
    return render_template('data/article.html', title='Article', form=form, compId=compId)


@data.route('/data/nextArticle', methods=['POST'])
@login_required
def next_article():
    # Store current URL and get data
    currentUrl = request.form['url'].strip('/')
    urlSplit = currentUrl.split('/')
    art_id = int(urlSplit[-1].strip('article'))
    ds_id = int(urlSplit[-2].strip('dataset'))
    # Get article from DB and populate form
    article = Article.query.get_or_404(art_id)
    # Get dataset from DB
    dataset = Dataset.query.get_or_404(ds_id)

    # See if there is a next article
    current_dataset_idx = dataset.articles.index(article)
    if (len(dataset.articles) == (current_dataset_idx + 1)):
        returnUrl = False
    else:
        next_dataset_idx = current_dataset_idx + 1
        next_art_id = dataset.articles[next_dataset_idx].id
        returnUrl = '/'.join(urlSplit[:3] + ["article{}".format(next_art_id)])
    return jsonify({'url': returnUrl})


@data.route('/data/backArticle', methods=['POST'])
@login_required
def back_article():
    # Store current URL and get data
    currentUrl = request.form['url'].strip('/')
    urlSplit = currentUrl.split('/')
    art_id = int(urlSplit[-1].strip('article'))
    ds_id = int(urlSplit[-2].strip('dataset'))
    # Get article from DB
    article = Article.query.get_or_404(art_id)
    # Get dataset from DB
    dataset = Dataset.query.get_or_404(ds_id)

    # See if there is a next article
    current_dataset_idx = dataset.articles.index(article)
    if (current_dataset_idx == 0):
        returnUrl = False
    else:
        prev_dataset_idx = current_dataset_idx - 1
        prev_art_id = dataset.articles[prev_dataset_idx].id
        returnUrl = '/'.join(urlSplit[:3] + ["article{}".format(prev_art_id)])
    return jsonify({'url': returnUrl})


@data.route('/data/addCompound', methods=['POST'])
@login_required
def add_compound():
    # Store current URL and get data
    data = request.get_json()
    currentUrl = data['url'].strip('/')
    urlSplit = currentUrl.split('/')
    art_id = int(urlSplit[-1].strip('article'))
    # Get article from DB
    article = Article.query.get_or_404(art_id)
    article = save_data_to_article(article, data)

    # Initialize a blank compound
    compound = Compound()
    # Make sure list isn't empty
    if article.compounds:
        # Get the source organism for the last compound of an article
        compound.source_organism = article.compounds[-1].source_organism
    # Add a blank compound to the article
    article.compounds.append(compound)
    try_dbcommit()

    # Store compound index in session cookie
    session['compound'] = len(article.compounds) - 1

    # Send back json with url to redirect
    return jsonify({'url': currentUrl})

@data.route('/data/delCompound', methods=['POST'])
@login_required
def delete_compound():
    # Clear session cookie
    session.pop('compound', None)
    # Store current URL and get data
    data = request.get_json()
    currentUrl = data['url'].strip('/')
    urlSplit = currentUrl.split('/')
    art_id = int(urlSplit[-1].strip('article'))
    comp_id = int(data['compId'])
    # Get article from DB
    article = Article.query.get_or_404(art_id)
    article = save_data_to_article(article, data)
    # Get compound from DB
    compound = Compound.query.get_or_404(comp_id)
    # Compound index in article
    idx = article.compounds.index(compound)
    article.compounds.pop(idx)
    try_dbcommit()

    # Store session cookie as compound before deleted
    session['compound'] = idx - 1 if idx > 1 else 0

    return jsonify({'url': currentUrl})

@data.route('/data/smiToMol', methods=["POST"])
@login_required
def smilesToMolblock():
    data = request.get_json()
    smiles = data.get("smiles")
    try:
        m = Chem.MolFromSmiles(smiles)
        Chem.AddHs(m)
        Chem.Compute2DCoords(m)
        Chem.RemoveHs(m)
        molblock = Chem.MolToMolBlock(m)
        current_app.logger.info("Successfully coverted SMILES %s to MOLblock",
                                smiles)
        return jsonify({'molblock': molblock, 'success': 1})
    except Exception as e:
        current_app.logger.error("%s: %s", type(e).__name__, e)
        current_app.logger.error("Unable to convert SMILES %s to MOLblock",
                                 smiles)
        return jsonify({'success': 0})


@celery.task
def standardize_dataset(ds_id):
    dataset = Dataset.query.get(ds_id)
    for compound in dataset.get_compounds():
        smiles = compound.smiles
        try:
            compound.smiles = get_standardized_smiles(smiles)
            db.session.commit()
        except (ValueError, TypeError, RequestException):
            print("Error standardzing SMILES %s", smiles)
            db.session.rollback()
    dataset.standardized = True
    db.session.commit()

#####################################################################
###                      HELPER FUNCTIONS                         ###
#####################################################################
def save_data_to_article(article, data):
    # Save article data from POST
    art = NoneDict(data['article'])
    article.pmid = art['pmid']
    article.doi = art['doi']
    article.title = art['title']
    article.journal = art['journal']
    article.authors = art['authors']
    article.abstract = art['abstract']
    article.year = art['year']
    article.pages = art['pages']
    article.volume = art['vol']
    article.issue = art['iss']
    article.num_compounds = art['num_compounds']
    article.needs_work = art['needs_work']
    article.notes = art['notes']
    # Save compound data from POST
    actual_cmpds = []
    for cmpd in data['compounds']:
        cmpd = NoneDict(cmpd)
        db_cmpd = None
        if cmpd['id']:
            db_cmpd = Compound.query.get_or_404(cmpd['id'])

        db_cmpd.name = cmpd['name']
        db_cmpd.smiles = cmpd['smiles']
        db_cmpd.source_organism = cmpd['source_organism']
        db_cmpd.curated_compounds = cmpd['curated_compound']

        actual_cmpds.append(db_cmpd)
    article.compounds = actual_cmpds

    return article

def dataset_redirect(cur_id, ds_id):
    return url_for('data.dataset', cur_id=cur_id, ds_id=ds_id)

def training_score_redirect(cur_id, ds_id):
    return url_for('data.trainingscore', cur_id=cur_id, ds_id=ds_id)

def article_redirect(cur_id, ds_id, art_id):
    return url_for('data.article', cur_id=cur_id, ds_id=ds_id, art_id=art_id)

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')

def try_dbcommit():
    try:
        db.session.commit()
        # flash('Data saved!')
    except:
        db.session.rollback()
        flash('Error sending data to database... Please contact us!')

def get_article_compounds(form):
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

        if not db_cmpd.id:
            db.session.add(db_cmpd)

        actual_cmpds.append(db_cmpd)

    return actual_cmpds