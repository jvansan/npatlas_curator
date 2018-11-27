# -*- coding: utf-8 -*-
"""ORM Connection to MySQL DB
"""
from sqlalchemy import create_engine
# from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, func, Column, Integer, Numeric, String,
                        ForeignKey)
from sqlalchemy.types import CHAR, TIMESTAMP, Text
from sqlalchemy.orm import sessionmaker, relationship
# from sqlalchemy.schema import CreateTable


Base = declarative_base()


# Many-to-Many Relation Tables
compound_name = Table('compound_has_compound_name', Base.metadata,
                      Column('compound_name_compound_name_id', Integer,
                             ForeignKey('compound_name.compound_name_id'),
                             primary_key=True),
                      Column('compound_compound_id', Integer,
                             ForeignKey('compound.compound_id'),
                             primary_key=True),
                      mysql_engine='InnoDB',
                      mysql_charset='utf8')

compound_reassignment = Table('compound_has_reassignment', Base.metadata,
                              Column('compound_compound_id', Integer,
                                     ForeignKey('compound.compound_id'),
                                     primary_key=True),
                              Column('reference_reference_id', Integer,
                                     ForeignKey('reference.reference_id'),
                                     primary_key=True),
                              Column('reassignment_type_reassignment_type_id',
                                     Integer,
                                     ForeignKey('origin.origin_id'),
                                     primary_key=True),
                              mysql_engine='InnoDB',
                              mysql_charset='utf8'
                              )

compound_synthesis = Table('compound_has_synthesis', Base.metadata,
                           Column('compound_compound_id', Integer,
                                  ForeignKey('compound.compound_id'),
                                  primary_key=True),
                           Column('reference_reference_id', Integer,
                                  ForeignKey('reference.reference_id'),
                                  primary_key=True),
                           Column('synthesis_synthesis_id', Integer,
                                  ForeignKey('synthesis.synthesis_id'),
                                  primary_key=True),
                           mysql_engine='InnoDB',
                           mysql_charset='utf8'
                           )


# CompoundOrigin Association Object
class CompoundOrigin(Base):
    __tablename__ = 'compound_has_origin'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    compound_id = Column('compound_compound_id', Integer,
                         ForeignKey('compound.compound_id'),
                         primary_key=True)
    origin_id = Column('origin_origin_id', Integer,
                       ForeignKey('origin.origin_id'),
                       primary_key=True)
    reference_id = Column('reference_reference_id', Integer,
                          ForeignKey('reference.reference_id'),
                          primary_key=True)
    original_isolation_reference = Column(Integer, default=1)


# Compound Information Section
class Compound(Base):
    __tablename__ = 'compound'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('compound_id', Integer, primary_key=True)
    insert_date = Column(
        'compound_insert_date', TIMESTAMP, nullable=False,
        default=func.current_timestamp())
    inchikey = Column('compound_inchikey', CHAR(27), nullable=False,
                      unique=True)
    inchi = Column('compound_inchi', String(2000), nullable=False)
    molecular_formula = Column('compound_molecular_formula', String(255))
    molecular_weight = Column('compound_molecular_weight', Numeric(9, 4))
    accurate_mass = Column('compound_accurate_mass', Numeric(9, 4))
    m_plus_H = Column('compound_m_plus_H', Numeric(9, 4))
    m_plus_Na = Column('compound_m_plus_Na', Numeric(9, 4))
    smiles = Column('compound_smiles', String(2000))
    molblock = Column('compound_molblock', Text)
    cluster_id = Column('compound_cluster_id', Integer)
    node_id = Column('compound_node_id', Integer)
    names = relationship('Name', secondary=compound_name,
                         back_populates='compounds')
    curation_data = relationship('CurationData')
    db_ids = relationship('ExternalDB')
    # origin = relationship('Origin', secondary='compound_has_origin',
    #                       back_populates='compounds')
    # references = relationship('Reference', secondary='compound_has_origin',
    #                           back_populates='compounds')

    def __repr__(self):
        return "<Compound(inchikey='%s')>" % self.inchikey


class Name(Base):
    __tablename__ = 'compound_name'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('compound_name_id', Integer, primary_key=True)
    insert_date = Column('compound_name_insert_date', TIMESTAMP,
                         nullable=False,
                         default=func.current_timestamp())
    name = Column('compound_name_name', String(2000), nullable=False)
    compounds = relationship('Compound', secondary=compound_name,
                             back_populates='names')

    def __repr__(self):
        return "<Name(name='%s')>" % self.name


class CurationData(Base):
    __tablename__ = 'curation_data'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('curation_data_id', Integer, primary_key=True)
    insert_date = Column('curation_data_insert_date', TIMESTAMP,
                         nullable=False,
                         default=func.current_timestamp())
    file_name = Column('curation_data_file_name', String(255))
    compound_id = Column('compound_compound_id', Integer,
                         ForeignKey('compound.compound_id'))


class ExternalDB(Base):
    __tablename__ = 'compound_external_db'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    compound_id = Column('compound_compound_id', Integer,
                         ForeignKey('compound.compound_id'), primary_key=True)
    db_id = Column('compound_external_db_id', Integer,
                   ForeignKey(
                       'compound_external_db_id.compound_external_db_id'),
                   primary_key=True)
    db_code = Column('compound_external_db_code', String(20), nullable=False)
    extdb = relationship('ExternalDBID')
    compound = relationship('Compound')


class ExternalDBID(Base):
    __tablename__ = 'compound_external_db_id'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('compound_external_db_id', Integer, primary_key=True)
    name = Column('compound_external_db_name', String(45))


# Origin Data Section
class Origin(Base):
    __tablename__ = 'origin'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('origin_id', Integer, primary_key=True)
    insert_date = Column(
        'origin_insert_date', TIMESTAMP, nullable=False,
        default=func.current_timestamp())
    genus_id = Column('genus_genus_id', Integer, ForeignKey('genus.genus_id'),
                      nullable=False)
    species = Column('origin_species', String(255), nullable=False)
    # compounds = relationship('Compound', secondary='compound_has_origin',
    #                          back_populates='origin')
    # reference = relationship('Reference', secondary='compound_has_origin')
    genus = relationship('Genus')


class Genus(Base):
    __tablename__ = 'genus'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('genus_id', Integer, primary_key=True)
    name = Column('genus_genus', String(255), nullable=False)
    origin_type_id = Column('origin_type_origin_type_id', Integer,
                            ForeignKey('origin_type.origin_type_id'),
                            nullable=False)
    official = Column('genus_official', Integer)
    origin_type = relationship('OriginType', back_populates='genera')


class OriginType(Base):
    __tablename__ = 'origin_type'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('origin_type_id', Integer, primary_key=True)
    name = Column('origin_type_type', String(255), nullable=False)
    genera = relationship('Genus', back_populates='origin_type')


# Reference Data Section
class Reference(Base):
    __tablename__ = 'reference'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('reference_id', Integer, primary_key=True)
    insert_date = Column(
        'reference_insert_date', TIMESTAMP, nullable=False,
        default=func.current_timestamp())
    authors = Column('reference_author_list', String(2000))
    journal_id = Column('journal_journal_id', Integer,
                        ForeignKey('journal.journal_id'))
    journal = relationship('Journal')
    year = Column('reference_year', Integer)
    volume = Column('reference_volume', String(255))
    issue = Column('reference_issue', String(255))
    pages = Column('reference_pages', String(45))
    doi = Column('reference_doi', String(255))
    pmid = Column('reference_pmid', Integer)
    title = Column('reference_title', String(2000))
    reference_type_id = Column('reference_type_reference_type_id', Integer,
                               ForeignKey('reference_type.reference_type_id'),
                               nullable=False)
    reference_type = relationship('ReferenceType')
    abstract = Column('reference_abstract', Text)
    # compounds = relationship('Compound', secondary='compound_has_origin',
                             # back_populates='references')


class ReferenceType(Base):
    __tablename__ = 'reference_type'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('reference_type_id', Integer, primary_key=True)
    name = Column('reference_type_name', String(45), nullable=False)


class Journal(Base):
    __tablename__ = 'journal'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('journal_id', Integer, primary_key=True)
    title = Column('journal_title', String(255), nullable=False)
    abbrev = relationship('JournalAbbreviation', back_populates='journal')


class JournalAbbreviation(Base):
    __tablename__ = 'journal_abbreviation'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('journal_journal_id', Integer,
                ForeignKey('journal.journal_id'), primary_key=True)
    abbrev = Column('journal_abbreviation', String(45), nullable=False)
    journal = relationship('Journal', back_populates='abbrev')


# Sythesis Data Section
class Synthesis(Base):
    __tablename__ = 'synthesis'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    id = Column('synthesis_id', Integer, primary_key=True)
    description = Column('synthesis_description', String(2000))

# TODO: Activity ORM


class AtlasDB(object):

    """Interface to ORM
    """

    # Bind tables to access layer
    Base = Base
    metadata = Base.metadata
    Compound = Compound
    Name = Name
    CurationData = CurationData
    ExternalDB = ExternalDB
    ExternalDBID = ExternalDBID
    Origin = Origin
    OriginType = OriginType
    Genus = Genus
    Reference = Reference
    ReferenceType = ReferenceType
    Journal = Journal
    JournalAbbreviation = JournalAbbreviation
    Synthesis = Synthesis
    CompoundOrigin = CompoundOrigin

    def dbInit(self, dbtype, user, passwd, host, dbname):
        """Initialize DB to a given connection

        Parameters
        ----------
        conn_string : str
            SQLAlchemy connection string
        """
        # engine = create_engine('{0}://{1}:{2}@{3}'.format(
        #     dbtype, user, passwd, host))
        # engine.execute("CREATE DATABASE IF NOT EXISTS {0} CHARACTER SET utf8"
        #         .format(dbname))
        self.engine = create_engine('{0}://{1}:{2}@{3}/{4}'.format(
            dbtype, user, passwd, host, dbname))
        self.Base.metadata.bind = self.engine
        self.Base.metadata.create_all()

    def startSession(self, autocommit=False, autoflush=False):
        """Start a new session for the DB

        Returns
        -------
        SQLAlchemy.orm.Session
            Session for interacting with DB
        """
        Session = sessionmaker(bind=self.engine, autocommit=autocommit, autoflush=autoflush)
        return Session()

    @staticmethod
    def getTableColumns(tablename):
        """Get a list of the columns for a given table
.first():
    print = self.ReferenceType(
        Parameters
        ----------
        tablename : AtlasDB.Table


        Returns
        -------
        list
            List of columns in a tablename
        """
        return tablename.__table__.columns.keys()

    def collectPassedCompounds(self, sess):
        return sess.query(self.Compound.inchikey,
                          self.Compound.smiles).all()

    def initPrepopulated(self, sess):
        """Add prepoulated information if not present
        """
        self._addExternalDBs(sess)
        self._addOriginTypes(sess)
        self._addRefTypes(sess)

    def _addExternalDBs(self, sess):
        if not sess.query(self.ExternalDBID).first():
            pubchem = self.ExternalDBID(name='PubChem')
            chemspider = self.ExternalDBID(name='ChemSpider')
            chembl = self.ExternalDBID(name='ChEMBL')
            berdy = self.ExternalDBID(name='Berdy')
            sess.add_all([pubchem, chemspider, chembl, berdy])
            if not sess.autocommit:
                sess.commit()

    def _addOriginTypes(self, sess):
        if not sess.query(self.OriginType).first():
           bact = self.OriginType(name='Bacterium')
           fung = self.OriginType(name='Fungus')
           sess.add_all([bact, fung])
           if not sess.autocommit:
               sess.commit()

    def _addRefTypes(self, sess):
        if not sess.query(self.ReferenceType).first():
            print_ = self.ReferenceType(name='Print')
            online = self.ReferenceType(name='Online')
            sess.add_all([print_, online])
            if not sess.autocommit:
                sess.commit()

    def getGenus(self, genus_name, origin_type_id, sess):
        genus = sess.query(self.Genus)\
                .filter((self.Genus.name == genus_name) &
                        (self.Genus.origin_type_id == origin_type_id))\
                .first()
        if not genus:
            genus = self.Genus(
                    name=genus_name,
                    origin_type_id=origin_type_id 
                    )
            sess.add(genus)
            if not sess.autocommit:
                sess.commit()
        return genus

    def getJournal(self, title, abbrev, sess):
        journal = sess.query(self.Journal)\
                .filter(self.Journal.title == title)\
                .first()
        if not journal:
            journal = self.Journal(
                    title=title,
                    abbrev=[self.JournalAbbreviation(abbrev=abbrev)])
            sess.add(journal)
            if not sess.autocommit:
                sess.commit()
        return journal

# Instance of Atlas DB to pass around
atlasdb = AtlasDB()
