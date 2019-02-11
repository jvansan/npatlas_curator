from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# local imports
from app import db, login_manager


class Curator(UserMixin, db.Model):
    """
    Create curator table/model
    """

    __tablename__ = "curator"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(60), index=True, unique=True)
    username = db.Column(db.String(20), index=True, unique=True)
    first_name = db.Column(db.String(60), index=True)
    last_name = db.Column(db.String(60), index=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        """
        Prevent password from being accessed
        """
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, password):
        """
        Set password to hashed password
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Check if hashed password matches actual password
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<Curator: {}>".format(self.username)

# Setup user loader
@login_manager.user_loader
def load_user(user_id):
    return Curator.query.get(int(user_id))


# Define dataset_article, article_compound, and dataset_problem 
# many-to-many relationships
dataset_article = db.Table(
    'dataset_article',
    db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id'),
              primary_key=True),
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'),
              primary_key=True)
)

article_compound = db.Table(
    'article_compound',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'),
              primary_key=True),
    db.Column('compound_id', db.Integer, db.ForeignKey('compound.id'),
              primary_key=True)
)


class Dataset(db.Model):
    """
    Create dataset table/model
    """
    __tablename__ = "dataset"
    id = db.Column(db.Integer, primary_key=True)
    curator_id = db.Column(db.Integer, db.ForeignKey('curator.id'))
    curator = db.relationship('Curator', backref='datasets', lazy=True)
    create_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_edit_date = db.Column(db.DateTime, default=db.func.current_timestamp(),
                               onupdate=db.func.current_timestamp())
    last_article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    instructions = db.Column(db.String(1000))
    completed = db.Column(db.Boolean, default=False)
    articles = db.relationship('Article', secondary=dataset_article,
                               backref=db.backref('datasets', lazy=True))
    training = db.Column(db.Integer, default=0)
    checker_dataset = db.relationship('CheckerDataset', uselist=False,
                                      backref='dataset')
    problems = db.relationship('Problem', backref='dataset')

    def get_articles(self):
        articles = Article.query.join(dataset_article)\
            .filter_by(dataset_id=self.id)
        return articles

    def get_compounds(self):
        compounds = []
        for art in self.articles:
            compounds.extend(art.compounds)
        return compounds

    def get_curator_id(self):
        """
        Get curator id if assigned dataset
        Send a zero if not assigned - useful for admin access to data
        """
        return self.curator.id if self.curator else 0
    
    def standard_running(self):
        return (not self.checker_dataset.standardized and 
                not self.checker_dataset.completed
                if self.checker_dataset else False)

    def checker_running(self):
        return (self.checker_dataset.standardized and
                self.checker_dataset.running
                if self.checker_dataset else False)

    def checker_completed(self):
        """
        Boolean return if checker dataset exists and has completed checking
        """
        return (self.checker_dataset.standardized and 
                self.checker_dataset.completed
                if self.checker_dataset else False)

    def checker_task_id(self):
        """
        Return task id string if checker dataset exists, else None
        """
        return self.checker_dataset.celery_task_id if self.checker_dataset else None

    def inserted(self):
        return self.checker_dataset.inserted if self.checker_dataset else False


class Article(db.Model):
    """
    Create article table/model
    """
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    pmid = db.Column(db.Integer)
    journal = db.Column(db.String(255))
    year = db.Column(db.Integer)
    volume = db.Column(db.String(255))
    issue = db.Column(db.String(255))
    pages = db.Column(db.String(255))
    authors = db.Column(db.Text)
    doi = db.Column(db.String(255))
    title = db.Column(db.Text)
    abstract = db.Column(db.Text)
    num_compounds = db.Column(db.Integer)
    compounds = db.relationship('Compound', secondary=article_compound,
                                backref='article')
    # Tracking column
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    needs_work = db.Column(db.Boolean, default=False)
    is_nparticle = db.Column(db.Boolean, default=True)
    npa_artid = db.Column(db.Integer)
    checker_article = db.relationship('CheckerArticle', uselist=False,
                                      backref='article')


class Compound(db.Model):
    """
    Create compound table/model
    """
    __tablename__ = "compound"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    smiles = db.Column(db.String(1000))
    source_organism = db.Column(db.String(255))
    npaid = db.Column(db.Integer)
    checker_compound = db.relationship('CheckerCompound', uselist=False,
                                       backref='compound')


# ================================================================
# =====                Checker Database Models               =====
# ================================================================

class CheckerDataset(db.Model):
    """
    Create CheckerDataset table/model
    """
    __tablename__ = "dataset_checker"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    celery_task_id = db.Column(db.String(48), nullable=False)
    standardized = db.Column(db.Boolean, default=False)
    running = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    inserted = db.Column(db.Boolean, default=False)


class CheckerArticle(db.Model):
    """
    Create CheckerArticle table/model
    """
    __tablename__ = "checker_article"
    id = db.Column(db.Integer, db.ForeignKey('article.id'), primary_key=True)
    pmid = db.Column(db.Integer)
    doi = db.Column(db.String(255))
    npa_artid = db.Column(db.Integer)
    journal = db.Column(db.String(1000))
    journal_abbrev = db.Column(db.String(255))
    year = db.Column(db.Integer)
    volume = db.Column(db.String(255))
    issue = db.Column(db.String(255))
    pages = db.Column(db.String(255))
    authors = db.Column(db.Text)
    title = db.Column(db.Text)
    abstract = db.Column(db.Text)


class CheckerCompound(db.Model):
    """
    Create CheckerCompound table.model
    """
    __tablename__ = "checker_compound"
    id = db.Column(db.Integer, db.ForeignKey('compound.id'), primary_key=True)
    name = db.Column(db.Text)
    formula = db.Column(db.String(255))
    smiles = db.Column(db.Text)
    inchi = db.Column(db.Text)
    inchikey = db.Column(db.String(40))
    molblock = db.Column(db.Text)
    source_genus = db.Column(db.String(255))
    source_species = db.Column(db.String(255))
    npaid = db.Column(db.Integer)
    mibig_id = db.Column(db.Integer)
    pubchem_id = db.Column(db.Integer)
    berdy_id = db.Column(db.Integer)
    resolve = db.Column(db.Integer)

    def get_article_id(self):
        article = self.compound.article[0]
        return article.id


class Journal(db.Model):

    """Table of accepted Journal Names

    Attributes
    ----------
    altjournals : AltJournal
        Relation to AltJournal table. Store all know typos
        and deprecations of a given genus
    journal : str
        Name of journal
    """

    __tablename__ = "journal"
    id = db.Column(db.Integer, primary_key=True)
    journal = db.Column(db.Text, nullable=False)
    abbrev = db.Column(db.String(255), nullable=False)
    altjournals = db.relationship('AltJournal', backref='journal')

    @staticmethod
    def check_journal_match(journal_name):
        # Full name query first
        journal_match = Journal.query.filter_by(journal=journal_name).first()
        # Abbreviation query second
        if not journal_match:
            journal_match = Journal.query.filter_by(abbrev=journal_name).first()
        # Last check the list of known alternatives
        if not journal_match:
            alt_query = journal_name.lower().replace('.', '')
            alt = AltJournal.query.filter_by(altjournal=alt_query).first()
            if alt:
                journal_match = alt.journal

        return journal_match


class AltJournal(db.Model):
    """Table of known altenatives to the given Journal names

    Attributes
    ----------
    altjournal : str
        Alternative name of journal
    journal_id : int
        Id of known journal
    """

    __tablename__ = "altjournal"
    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(db.Integer, db.ForeignKey('journal.id'))
    altjournal = db.Column(db.Text)


class Genus(db.Model):
    """Table of accepted Genera

    Attributes
    ----------
    altgenera : AltGenus
        Relation to AltGenus table. Store all know typos
        and deprecations of a given genus
    genus : str
        Name of genus
    genustype : str
        either Bacterium, Fungus, or Other
    """
    __tablename__ = "genus"
    id = db.Column(db.Integer, primary_key=True)
    genus = db.Column(db.String(255), nullable=False)
    genustype = db.Column(db.String(55))
    # One-to-many relationship with Alternative Genera
    altgenera = db.relationship('AltGenus', backref='genus')
    
    @staticmethod
    def check_genus_match(genus_name):
        genus_match = Genus.query.filter_by(genus=genus_name).first()
        if not genus_match:
            alt_query = genus_name.lower()
            alt = AltGenus.query.filter_by(altgenus=alt_query).first()
            if alt:
                genus_match = alt.genus

        return genus_match


class AltGenus(db.Model):
    """Table of known altenatives to the given Genus names

    Attributes
    ----------
    altgenus : str
        Alternative name of genus
    genus_id : int
        Id of known genus
    genustype : str
        either Bacterium or Fungus
    """

    __tablename__ = "altgenus"
    id = db.Column(db.Integer, primary_key=True)
    genus_id = db.Column(db.Integer, db.ForeignKey('genus.id'))
    altgenus = db.Column(db.String(255))
    genustype = db.Column(db.String(55))


# Tables for saving info to review
class Problem(db.Model):
    """
    Problem table/model

    Attributes
    ----------
    dataset_id : int
        Dataset the problem belongs to
    article_id : int
        If problem with article -> save ID
    compound_id : int
        If problem with compound -> save ID
    problem : str
        One of the types of issues
    resolved: bool
        Has a problem been handled
    """

    __tablename__ = "problem"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    compound_id = db.Column(db.Integer, db.ForeignKey('compound.id'))
    problem = db.Column(db.String(255), nullable=False)
    resolved = db.Column(db.Boolean, default=False)


# Famous retractions
class Retraction(db.Model):
    """
    Retraction table/model

    Attributes
    ----------
    """
    __tablename__ = "retractions"
    id = db.Column(db.Integer, primary_key=True)
    article_doi = db.Column(db.String(255))
    compound_name = db.Column(db.String(255))
    compound_inchikey = db.Column(db.String(255))