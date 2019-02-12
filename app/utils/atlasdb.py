# -*- coding: utf-8 -*-
"""ORM Connection to MySQL DB
"""
import logging
from sqlalchemy import (Column, ForeignKey, Integer, Numeric, String, Table,
                        create_engine, func, select)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, sessionmaker, object_session
from sqlalchemy.types import CHAR, TIMESTAMP, Text


Base = declarative_base()


# Many-to-Many Relation Tables
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
                                     primary_key=True)
                              )


# CompoundOrigin Association Object
class CompoundOrigin(Base):
    __tablename__ = 'compound_has_origin'
    # __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
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
    # Relationships
    compound = relationship("Compound", backref="compound_origin")
    origin = relationship("Origin")
    reference = relationship("Reference")

    @hybrid_property
    def origin_reference(self):
        return (self.origin, self.reference)

    @origin_reference.setter
    def origin_reference(self, orig_ref_tuple):
        assert len(orig_ref_tuple) == 2
        assert isinstance(orig_ref_tuple[0], Origin)
        assert isinstance(orig_ref_tuple[1], Reference)
        self.origin = orig_ref_tuple[0]
        self.reference = orig_ref_tuple[1]


# CompoundSynthesis Association Object
class CompoundSynthesis(Base):
    __tablename__ = "compound_has_synthesis"
    compound_id = Column('compound_compound_id', Integer,
                         ForeignKey('compound.compound_id'),
                         primary_key=True)
    synthesis_id = Column('synthesis_synthesis_id', Integer,
                       ForeignKey('synthesis.synthesis_id'),
                       primary_key=True)
    reference_id = Column('reference_reference_id', Integer,
                          ForeignKey('reference.reference_id'),
                          primary_key=True)
    # Relationships
    compound = relationship("Compound", backref="compound_synthesis")
    synthesis = relationship("Synthesis")
    reference = relationship("Reference")

    @hybrid_property
    def synthesis_reference(self):
        return (self.synthesis, self.reference)

    @synthesis_reference.setter
    def synthesis_reference(self, synth_ref_tuple):
        assert len(synth_ref_tuple) == 2
        assert isinstance(synth_ref_tuple[0], Synthesis)
        assert isinstance(synth_ref_tuple[1], Reference)
        self.synthesis = synth_ref_tuple[0]
        self.reference = synth_ref_tuple[1]


# CompoundName Association Object
class CompoundName(Base):
    __tablename__ = 'compound_has_compound_name'
    compound_id = Column('compound_compound_id', Integer,
                         ForeignKey('compound.compound_id'),
                         primary_key=True)
    name_id = Column('compound_name_compound_name_id', Integer,
                     ForeignKey('compound_name.compound_name_id'),
                     primary_key=True)
    reference_id = Column('reference_reference_id', Integer,
                          ForeignKey('reference.reference_id'),
                          primary_key=True)
    original_isolation_name = Column(Integer, default=1)

    # Relationships
    compound = relationship("Compound", backref="compound_name")
    name = relationship("Name")
    reference = relationship("Reference")
    
    @hybrid_property
    def name_reference(self):
        return (self.name, self.reference)

    @name_reference.setter
    def name_reference(self, name_ref_tuple):
        assert len(name_ref_tuple) == 2
        assert isinstance(name_ref_tuple[0], Name)
        assert isinstance(name_ref_tuple[1], Reference)
        self.name = name_ref_tuple[0]
        self.reference = name_ref_tuple[1]


# Compound Information Section
class Compound(Base):
    __tablename__ = 'compound'
    id = Column('compound_id', Integer, primary_key=True)
    insert_date = Column(
        'compound_insert_date', TIMESTAMP, nullable=False,
        default=func.current_timestamp())
    inchikey = Column('compound_inchikey', CHAR(27), nullable=False,
                      unique=True)
    inchi = Column('compound_inchi', String(4000), nullable=False)
    molecular_formula = Column('compound_molecular_formula', String(255))
    molecular_weight = Column('compound_molecular_weight', Numeric(9, 4))
    accurate_mass = Column('compound_accurate_mass', Numeric(9, 4))
    m_plus_H = Column('compound_m_plus_H', Numeric(9, 4))
    m_plus_Na = Column('compound_m_plus_Na', Numeric(9, 4))
    smiles = Column('compound_smiles', String(2000))
    molblock = Column('compound_molblock', Text)
    cluster_id = Column('compound_cluster_id', Integer)
    node_id = Column('compound_node_id', Integer)
    # Simple relationships
    curation_data = relationship('CurationData', uselist=False)
    db_ids = relationship('ExternalDB')
    # Complex Associations
    # These get associations with references attached as tuple
    names = association_proxy('compound_name', 'name_reference')
    syntheses = association_proxy('compound_synthesis', 'synthesis_reference')
    origins = association_proxy('compound_origin', 'origin_reference')

    def __repr__(self):
        return "<Compound(inchikey='%s')>" % self.inchikey

    @hybrid_property
    def original_origin_reference(self):
        co = object_session(self).query(CompoundOrigin)\
            .filter(CompoundOrigin.compound_id==self.id)\
            .filter(CompoundOrigin.original_isolation_reference==1)\
            .one()
        return co.origin_reference

    @hybrid_property
    def original_origin(self):
        co = object_session(self).query(CompoundOrigin)\
            .filter(CompoundOrigin.compound_id==self.id)\
            .filter(CompoundOrigin.original_isolation_reference==1)\
            .one()
        return co.origin

    @hybrid_property
    def original_name_reference(self):
        cn = object_session(self).query(CompoundName)\
            .filter(CompoundName.compound_id==self.id)\
            .filter(CompoundName.original_isolation_name==1)\
            .one()
        return cn.name_reference

    @hybrid_property
    def original_name(self):
        cn = object_session(self).query(CompoundName)\
            .filter(CompoundName.compound_id==self.id)\
            .filter(CompoundName.original_isolation_name==1)\
            .one()
        return cn.name


class Name(Base):
    __tablename__ = 'compound_name'
    id = Column('compound_name_id', Integer, primary_key=True)
    insert_date = Column('compound_name_insert_date', TIMESTAMP,
                         nullable=False,
                         default=func.current_timestamp())
    name = Column('compound_name_name', String(2000), nullable=False)

    def __repr__(self):
        return "<Name(name='%s')>" % self.name


class CurationData(Base):
    __tablename__ = 'curation_data'
    id = Column('curation_data_id', Integer, primary_key=True)
    insert_date = Column('curation_data_insert_date', TIMESTAMP,
                         nullable=False,
                         default=func.current_timestamp())
    file_name = Column('curation_data_file_name', String(255))
    compound_id = Column('compound_compound_id', Integer,
                         ForeignKey('compound.compound_id'))


class ExternalDB(Base):
    __tablename__ = 'compound_external_db'
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
    id = Column('compound_external_db_id', Integer, primary_key=True)
    name = Column('compound_external_db_name', String(45))


# Origin Data Section
class Origin(Base):
    __tablename__ = 'origin'
    id = Column('origin_id', Integer, primary_key=True)
    insert_date = Column(
        'origin_insert_date', TIMESTAMP, nullable=False,
        default=func.current_timestamp())
    genus_id = Column('genus_genus_id', Integer, ForeignKey('genus.genus_id'),
                      nullable=False)
    species = Column('origin_species', String(255), nullable=False)
    genus = relationship('Genus')


class Genus(Base):
    __tablename__ = 'genus'
    id = Column('genus_id', Integer, primary_key=True)
    name = Column('genus_genus', String(255), nullable=False)
    origin_type_id = Column('origin_type_origin_type_id', Integer,
                            ForeignKey('origin_type.origin_type_id'),
                            nullable=False)
    official = Column('genus_official', Integer)
    origin_type = relationship('OriginType', back_populates='genera')


class OriginType(Base):
    __tablename__ = 'origin_type'
    id = Column('origin_type_id', Integer, primary_key=True)
    name = Column('origin_type_type', String(255), nullable=False)
    genera = relationship('Genus', back_populates='origin_type')


# Reference Data Section
class Reference(Base):
    __tablename__ = 'reference'
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
    patent_number = Column('reference_patent_number', String(200))
    # compounds = relationship('Compound', secondary='compound_has_origin',
                             # back_populates='references')


class ReferenceType(Base):
    __tablename__ = 'reference_type'
    id = Column('reference_type_id', Integer, primary_key=True)
    name = Column('reference_type_name', String(45), nullable=False)


class Journal(Base):
    __tablename__ = 'journal'
    id = Column('journal_id', Integer, primary_key=True)
    title = Column('journal_title', String(255), nullable=False)
    abbrev = relationship('JournalAbbreviation', back_populates='journal')


class JournalAbbreviation(Base):
    __tablename__ = 'journal_abbreviation'
    id = Column('journal_journal_id', Integer,
                ForeignKey('journal.journal_id'), primary_key=True)
    abbrev = Column('journal_abbreviation', String(100), nullable=False)
    journal = relationship('Journal', back_populates='abbrev')


# Synthesis Data Section
class Synthesis(Base):
    __tablename__ = 'synthesis'
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
    CompoundSynthesis = CompoundSynthesis
    CompoundName = CompoundName

    def dbInit(self, conn_string):
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
        self.engine = create_engine(conn_string, pool_size=2, max_overflow=0,
            pool_pre_ping=True)
        self.Base.metadata.bind = self.engine
        self.Base.metadata.create_all()

    def startSession(self, autocommit=False, autoflush=False):
        """Start a new session for the DB

        Returns
        -------
        SQLAlchemy.orm.Session
            Session for interacting with DB
        """
        Session = sessionmaker(bind=self.engine, autocommit=autocommit,
                               autoflush=autoflush)
        return Session()

    @staticmethod
    def getTableColumns(tablename):
        """Get a list of the columns for a given table

        Parameters
        ----------
        tablename : AtlasDB.Table


        Returns
        -------
        list
            List of columns in a tablename
        """
        return tablename.__table__.columns.keys()

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
            mibig = self.ExternalDBID(name='MIBiG')
            sess.add_all([pubchem, chemspider, chembl, berdy, mibig])
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
            journal = self.ReferenceType(name='Journal Article')
            patent = self.ReferenceType(name='Patent')
            sess.add_all([journal, patent])
            if not sess.autocommit:
                sess.commit()

    def getGenus(self, genus_name, origin_type_id, sess):
        genus = sess.query(self.Genus)\
                .filter((self.Genus.name == genus_name) &
                        (self.Genus.origin_type_id == origin_type_id))\
                .first()
        if not genus:
            logging.warn("Adding a new Genus the the DB.")
            genus = self.Genus(
                    name=genus_name,
                    origin_type_id=origin_type_id
                    )
            sess.add(genus)
        return genus

    def getJournal(self, title, abbrev, sess):
        journal = sess.query(self.Journal)\
                .filter(self.Journal.title == title)\
                .first()
        if not journal:
            logging.warn("Adding a new Journal the the DB.")
            journal = self.Journal(
                    title=title,
                    abbrev=[self.JournalAbbreviation(abbrev=abbrev)])
            sess.add(journal)
        return journal


# Instance of Atlas DB to pass around
atlasdb = AtlasDB()
