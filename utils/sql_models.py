# -*- coding: utf-8 -*-
"""Plain SQLAlchemy models for inserting/loading data

Only provides access to SQL models
DOES NOT CREATE TABLES
"""
from sqlalchemy import (Table, func, Column, Integer, Numeric, String,
                        ForeignKey, Boolean, DateTime, Text, create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref


Base = declarative_base()


class Curator(Base):
    """
    Subset of curator model,
    only for getting Curator id by username or email
    """

    __tablename__ = "curator"
    id = Column(Integer, primary_key=True)
    username = Column(String(20), index=True, unique=True)
    email = Column(String(60), index=True, unique=True)

    def __repr__(self):
        return "<Curator: {}>".format(self.username)


# Define dataset_article and article_compound many-to-many relationships
dataset_article = Table(
    'dataset_article',
    Base.metadata,
    Column('dataset_id', Integer, ForeignKey('dataset.id'),
              primary_key=True),
    Column('article_id', Integer, ForeignKey('article.id'),
              primary_key=True)
)

article_compound = Table(
    'article_compound',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('article.id'),
              primary_key=True),
    Column('compound_id', Integer, ForeignKey('compound.id'),
              primary_key=True)
)


class Dataset(Base):
    """
    Create dataset table/model
    """
    __tablename__ = "dataset"
    id = Column(Integer, primary_key=True)
    curator_id = Column(Integer, ForeignKey('curator.id'))
    curator = relationship('Curator', backref='datasets', lazy=True)
    create_date = Column(DateTime, default=func.current_timestamp())
    last_edit_date = Column(DateTime, default=func.current_timestamp(),
                               onupdate=func.current_timestamp())
    last_article_id = Column(Integer, ForeignKey('article.id'))
    instructions = Column(String(1000))
    completed = Column(Boolean, default=False)
    articles = relationship('Article', secondary=dataset_article,
                               backref=backref('datasets', lazy=True, cascade="all"))


class Article(Base):
    """
    Create article table/model
    """
    __tablename__ = "article"
    id = Column(Integer, primary_key=True)
    pmid = Column(Integer)
    journal = Column(String(255))
    year = Column(Integer)
    volume = Column(String(255))
    issue = Column(String(255))
    pages = Column(String(255))
    authors = Column(Text)
    doi = Column(String(255))
    title = Column(Text)
    abstract = Column(Text)
    num_compounds = Column(Integer)
    compounds = relationship('Compound', secondary=article_compound,
                                backref=backref('article', cascade="all"))
    # Tracking column
    completed = Column(Boolean, default=False)
    notes = Column(Text)
    needs_work = Column(Boolean, default=False)
    is_nparticle = Column(Boolean, default=True)


class Compound(Base):
    """
    Create compound table/model
    """
    __tablename__ = "compound"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    smiles = Column(String(1000))
    source_organism = Column(String(255))
    cid = Column(Integer)
    csid = Column(Integer)
    cbid = Column(Integer)
    curated_compound = Column(Boolean, default=True)


# ORM Interface
class CuratorDB(object):

    # Bind tables to access layer
    Base = Base
    metadata = Base.metadata

    def __init__(self, URI):
        """Initialize DB to a given connection

        Parameters
        ----------
        URI : str
            SQLAlchemy connection string
        """
        self.engine = create_engine(URI)
        self.Base.metadata.bind = self.engine

    def startSession(self, autocommit=False, autoflush=False):
        """Start a new session for the DB

        Returns
        -------
        SQLAlchemy.orm.Session
            Session for interacting with DB
        """
        Session = sessionmaker(bind=self.engine, autocommit=autocommit, autoflush=autoflush)
        return Session()