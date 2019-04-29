import datetime
import os
from contextlib import contextmanager
from decimal import Decimal

from .. import db
from ..models import Dataset, Genus, Journal
from ..utils.atlasdb import atlasdb
from ..utils.Compound import Compound
from .ResolveEnum import ResolveEnum


class Inserter(object):
    # Hacky solution to keeping URI in config file
    atlasdb = atlasdb
    try:
        import sys
        import warnings
        sys.path.append("../..")
        from instance.config import ATLAS_DATABASE_URI
        # suppress annoying MariaDB version warning
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            atlasdb.dbInit(ATLAS_DATABASE_URI)
    except ImportError:
        raise Exception("Missing ATLAS_DATABASE_URI in config")

    def __init__(self, dataset_id, *args, **kwargs):
        self.dataset_id = dataset_id

        self.task = kwargs.get("celery_task", None)
        self.logger = kwargs.get("logger")
        self.changes = []

    def update_status(self, current, total, status):
        if self.task:
            self.task.update_state(
                state='PROGRESS',
                meta={'current': current, 'total': total,
                    'status': status}
            )
        self.logger.info("PROGRESS: {}/{}\nStatus: {}"\
                .format(current, total, status))

    def run(self):
        dataset = Dataset.query.get(self.dataset_id)

        self.dataset_sanity_check(dataset)
        total = len(dataset.articles)
        self.update_status(0, total, 'FIRING UP')
        # Start a session scope
        with atlas_session_scope() as session:
            
            # Iterate over checker_articles, double check the article is good
            # Add/update the data
            for idx, ds_article in enumerate(dataset.articles):
                # Skip over articles which are not properly curated/checked
                if (not ds_article.completed or ds_article.needs_work 
                    or not ds_article.is_nparticle):
                    self.logger.warning("Skipping article {}!".format(ds_article.id))
                    continue

                self.update_status(idx, total, "RUNNING")

                c_article = ds_article.checker_article

                if not c_article.npa_artid:
                    self.logger.info("Adding Reference - {}"\
                                     .format(c_article.doi))
                    reference = self.new_reference(c_article, session)
                else:
                    self.logger.info("Updating Reference {} - {}"\
                                     .format(c_article.npa_artid, c_article.doi))
                    reference = self.update_reference(c_article, session)

                # Iterate over compounds and add/update them
                # These functions also do association with origin + reference
                for ds_compound in ds_article.compounds:
                    c_compound = ds_compound.checker_compound

                    # Double check compound doesn't match Atlas without being handled
                    if (self.check_atlas_match(c_compound, session)
                        and not c_compound.resolve):
                        self.logger.error("Found an uncaught match for a compound!")
                        self.logger.error("{} - {}".format(
                                            c_compound.name, c_compound.inchikey))
                        self.reject_dataset()

                    # Assume new if no resolve enum value in DB
                    resolve_id = c_compound.resolve or 1 
                    resolve = ResolveEnum(resolve_id)
                    self.logger.debug("Resolving {} by {}-ing"\
                                     .format(c_compound.id, resolve.name))

                    if resolve.name == "new":
                        self.logger.info("Adding new compound: {}"\
                                         .format(c_compound.name))
                        self.new_compound(c_compound, reference, session)

                    elif resolve.name == "keep":
                        self.logger.info("Keeping NP Atlas Compound {}"\
                                         .format(c_compound.name))
                        continue

                    elif resolve.name == "replace" or resolve.name == "update":
                        self.logger.info("Replacing NPAID: {}"\
                                         .format(c_compound.npaid))
                        self.update_compound(c_compound, reference, session)
                    
                    else: # Only possible if mis-handled reject during checking
                        self.logger.error("Dataset contains rejected compounds - "+
                                          "There was an error in checker handling...")
                        self.reject_dataset()
        self.logger.info("Recorded {} changes".format(len(self.changes)))
        self.write_change_log(dataset)
        dataset.checker_dataset.inserted = True
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
            
    def write_change_log(self, dataset):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        outdir = os.path.realpath("insert_logs")
        info = "# Curator {} = {}\n# Insert Date: {}".format(
            dataset.curator_id, dataset.curator.username, 
            timestamp)
        header = '"CLASS","DB_ID","ATTRIBUTE","OLD_VALUE","NEW_VALUE"'
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        outfile = os.path.join(outdir, "change_{}.log".format(timestamp))
        lines = [info, header] + [x.to_string() for x in self.changes]
        self.logger.debug("Writing change log to {}".format(outfile))
        with open(outfile, 'w') as f:
            f.write("\n".join(lines))

    def new_compound(self, compound, reference, session):
        """
        Add a new compound to the NP Atlas and associate origin with reference
        """
        # Generate RDKit molecule with precomputed data
        calc_compound = Compound(compound.smiles, name=compound.name)
        
        # Prepare necessary data
        curation_data = atlasdb.CurationData(
            file_name="DB{:05d}".format(self.dataset_id)
        )
        name = self.get_compound_name(compound.name, session)
        origin = self.get_origin(compound, session)
        db_compound = atlasdb.Compound(
            inchikey=calc_compound.inchikey,
            inchi=calc_compound.inchi,
            molecular_formula=calc_compound.formula,
            molecular_weight=calc_compound.mass,
            accurate_mass=calc_compound.accurate_mass,
            m_plus_H=calc_compound.m_plus_h,
            m_plus_Na=calc_compound.m_plus_na,
            smiles=calc_compound.smiles,
            molblock=calc_compound.molblock,
            curation_data=curation_data
        )
        # Add external database ids 
        for k, v in {"pubchem_id": 1, "berdy_id": 4, "mibig_id": 5}.items():
            id_ = getattr(compound, k)
            if id_:
                db_compound.db_ids.append(
                    atlasdb.ExternalDB(db_code=id_, db_id=v)
                )
        session.add(db_compound)

        self.associate_compound_name(db_compound, name, reference, session, new=True)
        self.associate_compound_origin(db_compound, origin, reference, session, new=True)

    def update_compound(self, compound, reference, session):
        """
        Update compound in NP Atlas and associate origin with reference
        """
        # Generate RDKit molecule with precomputed data
        calc_compound = Compound(compound.smiles, name=compound.name)
        
        db_compound = session.query(atlasdb.Compound).get(compound.npaid)
        if not db_compound:
            self.logger.error("Compound was not found in the Atlas!")
            self.reject_dataset()

        # Update the main compound details
        self.save_update(db_compound, "inchi", calc_compound.inchi)
        self.save_update(db_compound, "inchikey", calc_compound.inchikey)
        self.save_update(db_compound, "molecular_formula", calc_compound.formula)
        self.save_update(db_compound, "molecular_weight", calc_compound.mass)
        self.save_update(db_compound, "accurate_mass", calc_compound.accurate_mass)
        self.save_update(db_compound, "m_plus_H", calc_compound.m_plus_h)
        self.save_update(db_compound, "m_plus_Na", calc_compound.m_plus_na)
        self.save_update(db_compound, "smiles", calc_compound.smiles)
        # Don't save molblock change (too large)
        # self.save_update(db_compound, "molblock", calc_compound.molblock)
        if db_compound.molblock != calc_compound.molblock:
            db_compound.molblock = calc_compound.molblock

        # Add/Update external database ids
        db_idxs = [x.db_id for x in db_compound.db_ids]
        for k, v in {"pubchem_id": 1, "berdy_id": 4, "mibig_id": 5}.items():
            id_ = getattr(compound, k)
            if v in db_idxs and id_:
                db_id = session.query(atlasdb.ExternalDB)\
                    .filter(atlasdb.ExternalDB.compound_id == db_compound.id)\
                    .first()
                db_id.db_code = id_
            elif id_:
                db_compound.db_ids.append(
                    atlasdb.ExternalDB(db_code=id_, db_id=v)
                )

        # Update and save original isolation name
        name = db_compound.original_name
        if name.name != compound.name:
            if name.name != "Not named":
                self.save_update(name, "name", compound.name)
            else:
                name = self.get_compound_name(compound.name, session)
            self.associate_compound_name(db_compound, name, reference, session,
                                         new=False)

        # Update and save original isolation origin
        origin = db_compound.original_origin
        if origin.genus.name != compound.source_genus:
            if not self.origin_has_many_compounds(origin, session):
                origin_type_id = self.get_origin_type_id(compound.source_genus)
                genus = atlasdb.getGenus(compound.source_genus, origin_type_id,
                                        session)
                self.save_update(origin, "genus_id", genus.id)
                self.save_update(origin, "species", compound.source_species)
            else:
                origin = self.get_origin(compound, session)
            self.associate_compound_origin(db_compound, origin, reference, session,
                                           new=False)
    
    def origin_has_many_compounds(self, origin, session):
        res = session.query(atlasdb.CompoundOrigin)\
            .filter(atlasdb.CompoundOrigin.origin_id == origin.id)\
            .all()
        return len(res) > 1 if res else False

    def associate_compound_name(self, compound, name, reference, session, new=False):
        compound_name = None
        if not new:
            compound_name = session.query(atlasdb.CompoundName)\
                    .filter((atlasdb.CompoundName.compound_id == compound.id) &
                            (atlasdb.CompoundName.name_id == name.id) &
                            (atlasdb.CompoundName.reference_id == reference.id)
                    ).first()
            if not compound_name:
                # Use the hybrid reference setter to replace original CompoundName
                compound.names[0] = (name, reference)
        else:
            compound_name = atlasdb.CompoundName(
                compound=compound,
                name=name,
                reference=reference
            )
            session.add(compound_name)

    def associate_compound_origin(self, compound, origin, reference, session, new=False):
        compound_origin = None
        if not new:
            compound_origin = session.query(atlasdb.CompoundOrigin)\
                .filter((atlasdb.CompoundOrigin.compound_id == compound.id) &
                        (atlasdb.CompoundOrigin.origin_id == origin.id) &
                        (atlasdb.CompoundOrigin.reference_id == reference.id)
                ).first()
            if not compound_origin:
                compound.origins[0] = (origin, reference)
        else:
            compound_origin = atlasdb.CompoundOrigin(
                compound=compound,
                origin=origin,
                reference=reference
            )
            session.add(compound_origin)

    def get_compound_name(self, name_string, session):
        # Get or create name
        name = session.query(atlasdb.Name)\
            .filter_by(name=name_string)\
            .first()
        if not name:
            name = atlasdb.Name(name=name_string)
            session.add(name)
        return name

    def check_atlas_match(self, compound, session):
        result = session.query(atlasdb.Compound)\
            .filter(atlasdb.Compound.inchikey == compound.inchikey)\
            .first()
        return bool(result)

    def get_origin(self, compound, session):
        origin_type_name = self.get_origin_type_name(compound.source_genus)
        origin = session.query(atlasdb.Origin)\
            .filter((atlasdb.Genus.name == compound.source_genus) &
                    (atlasdb.Origin.genus_id == atlasdb.Genus.id) &
                    (atlasdb.OriginType.name == origin_type_name) &
                    (atlasdb.Origin.species == compound.source_species))\
            .first()
        if not origin:
            if origin_type_name == 'Bacterium':
                origin_type_id = 1
            elif origin_type_name == 'Fungus':
                origin_type_id = 2
            else: # This indicates an error
                self.logger.error("Origin type is not Bacterium or Fungus")
                self.reject_dataset()
            genus = atlasdb.getGenus(compound.source_genus, origin_type_id,
                                     session)
            origin = atlasdb.Origin(
                genus=genus,
                species=compound.source_species
            )
            session.add(origin)
        return origin

    def get_origin_type_name(self, genus_string):
        genus = Genus.query.filter_by(genus=genus_string).first()
        return genus.genustype.split('_')[0]

    def get_origin_type_id(self, genus_string):
        origin_type_name = self.get_origin_type_name(genus_string)
        if origin_type_name == 'Bacterium':
            origin_type_id = 1
        elif origin_type_name == 'Fungus':
            origin_type_id = 2
        return origin_type_id

    def new_reference(self, article, session):
        """
        Add a new article and add it to the session
        """
        # Get required associated data first
        journal = atlasdb.getJournal(article.journal, article.journal_abbrev,
                                     session)
        ref_type = session.query(atlasdb.ReferenceType).get(1) # Journal article
        ref = atlasdb.Reference(
            authors=article.authors,
            journal=journal,
            year=article.year,
            volume=article.volume,
            issue=article.issue,
            pages=article.pages,
            doi=article.doi,
            pmid=article.pmid,
            title=article.title,
            reference_type=ref_type,
            abstract=article.abstract
        )
        session.add(ref)
        return ref

    def update_reference(self, article, session):
        """
        Get an article and update the data
        """
        ref = session.query(atlasdb.Reference).get(article.npa_artid)
        if not ref:
            self.logger.error("Reference was not found in the Atlas!")
            self.reject_dataset()
        
        # Double check Journal matches
        if ref.journal.title != article.journal:
            self.logger.warn("Journal does not match with NP Atlas.")
            journal = atlasdb.getJournal(article.journal, article.journal_abbrev,
                                         session)
            self.save_update(ref, "journal_id", journal.id)

        # Update the rest of the data
        self.save_update(ref, "doi", article.doi)
        self.save_update(ref, "pmid", article.pmid)
        self.save_update(ref, "authors", article.authors)
        self.save_update(ref, "year", article.year)
        self.save_update(ref, "volume", article.volume)
        self.save_update(ref, "issue", article.issue)
        self.save_update(ref, "pages", article.pages)
        self.save_update(ref, "title", article.title)
        self.save_update(ref, "abstract", article.abstract)

        return ref
        
    def save_update(self, db_obj, attr, new_value):
        """
        Consciously set a new value if there is a change, 
        record if a change does occur
        """
        old_value = getattr(db_obj, attr)
        if isinstance(old_value, float) or isinstance(old_value, Decimal):
            different = abs(Decimal(old_value) - Decimal(new_value)) > 1E-4
        else:
            different = old_value != new_value
        if different:
            setattr(db_obj, attr, new_value)
            self.add_change(db_obj, attr, old_value, new_value)

    def add_change(self, db_obj, attr, old_value, new_value):
        self.changes.append(
            Change(
                type(db_obj).__name__,
                getattr(db_obj, "id", None),
                attr,
                old_value,
                new_value
            )
        )

    def dataset_sanity_check(self, dataset):
        """
        Given a dataset from the Curator DB check several things
        0 Make sure not a training dataset and not already inserted
        1 Has the dataset been completed, standardized, and checked
        2 Are there any problems remaining for this dataset
        """
        if dataset.training or dataset.checker_dataset.inserted:
            self.reject_dataset()
        self.logger.debug("Passed First Sanity Check!")

        cdataset = dataset.checker_dataset
        dataset_ready = (dataset.completed and cdataset.standardized and
                         cdataset.completed)
        if not dataset_ready:
            self.reject_dataset()
        self.logger.debug("Passed Second Sanity Check!")

        if dataset.problems:
            self.reject_dataset()
        self.logger.debug("Passed Third Sanity Check!")

    def reject_dataset(self):
        db.session.rollback()
        self.atlasdb.engine.dispose()
        raise RuntimeError("Dataset is not ready for insertion")


@contextmanager
def atlas_session_scope():
    """Provide a transactional scope around a series of operations."""
    session = atlasdb.startSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Change(object):
    """
    Class for tracking changes made to the database
    """
    
    def __init__(self, class_, id_, attr, old_value, new_value):
        self.class_ = class_
        self.db_id = id_
        self.attribute=attr
        self.old_value = old_value
        self.new_value = new_value
    
    def to_string(self):
        return '"{}","{}","{}","{}","{}"'.format(
            self.class_, self.db_id, self.attribute, self.old_value,
            self.new_value)
