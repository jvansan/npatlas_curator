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


# Define dataset_article and article_compound many-to-many relationships
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
    training = db.Column(db.Boolean, default=False)
    checker_dataset = db.relationship('CheckerDataset', uselist=False,
                                      backref='dataset')

    def get_articles(self):
        articles = Article.query.join(dataset_article)\
            .filter_by(dataset_id=self.id)
        return articles

    def get_curator_id(self):
        """
        Get curator id if assigned dataset
        Send a zero if not assigned - useful for admin access to data
        """
        return self.curator.id if self.curator else 0

    def checker_running(self):
        """
        Boolean return if checker dataset exists and is running
        """
        return not self.checker_dataset.completed if self.checker_dataset else False

    def checker_completed(self):
        """
        Boolean return if checker dataset exists and has completed checking
        """
        return self.checker_dataset.completed if self.checker_dataset else False

    def checker_task_id(self):
        """
        Return task id string if checker dataset exists, else None
        """
        return self.checker_dataset.celery_task_id if self.checker_dataset else None


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
    completed = db.Column(db.Boolean, default=False)
    inserted = db.Column(db.Boolean, default=False)