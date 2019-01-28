import logging
import re
import time

from .. import db
from ..models import (CheckerArticle, CheckerCompound, CheckerDataset, Dataset,
                      Genus, Journal, Problem)
from ..utils import pubchem_search
from ..utils.atlasdb import atlasdb
from .Compound import Compound
from .NameString import NameString, decapitalize_first

# This unit contains far too much tight coupling between checker and flask app

class Checker(object):
    # Hacky solution to keeping URI in config file
    atlasdb = atlasdb
    try:
        import sys
        import warnings
        sys.path.append("../..")
        from instance.config import ATLAS_DATABASE_URI
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            atlasdb.dbInit(ATLAS_DATABASE_URI)
    except ImportError:
        raise Exception("Missing ATLAS_DATABASE_URI in config")

    def __init__(self, dataset_id, *args, **kwargs):
        self.dataset_id = dataset_id

        self.task = kwargs.get("celery_task", None)
        self.logger = kwargs.get("logger") or self.default_logger()

        self.review_list = []

    def update_status(self, current, total, status):
        if self.task:
            self.task.update_state(
                state='PROGRESS',
                meta={'current': current, 'total': total,
                    'status': status}
            )
        else:
            logger.info("PROGRESS: {}/{}\nStatus: {}"\
                  .format(current, total, status))

    def run(self, standardize_compounds=False):
        self.logger.info("Setting up dataset")
        dataset = Dataset.query.get_or_404(self.dataset_id)
        total = len(dataset.articles)

        for i, article in enumerate(dataset.get_articles()):
            
            # Skip over articles which are not properly curated
            if (not article.completed or article.needs_work 
                or not article.is_nparticle):
                self.logger.warning("Skipping article {}!".format(article.id))
                continue

            check_art = self.create_checker_article(article)

            self.update_status(i, total, check_art.doi)
            self.check_article(check_art)

            for compound in article.compounds:
                check_compound = self.create_checker_compound(
                    compound, standardize=standardize_compounds)
                self.check_compound(check_compound)

            # time.sleep(1)

        self.logger.info("Done checking!")
        self.logger.info("There are %d problems to review", len(self.review_list))
        self.save_review_list()
        dataset.checker_dataset.completed = True
        commit()

    def save_review_list(self):
        counter = 0
        old_problems = Problem.query.filter_by(dataset_id=self.dataset_id).delete()
        commit()
        for corr in self.review_list:
            counter += 1
            prob = Problem(
                dataset_id=self.dataset_id,
                problem=corr.problem,
                article_id=corr.article_id,
                compound_id=corr.compound_id
            )

            db_add_commit(prob)

        self.logger.info("Saved %d problems to DB", counter)
            


    def check_article(self, checker_article):
        self.check_doi(checker_article)
        self.check_pmid(checker_article)
        self.check_journal(checker_article)
        self.check_year(checker_article)
        self.check_volume(checker_article)
        self.check_issue(checker_article)
        self.check_pages(checker_article)
        self.check_authors(checker_article)
        self.check_title(checker_article)
        self.check_abstract(checker_article)
        commit()

    def check_compound(self, checker_compound):
        """
        Two main options:
         1 - This compound is already in the Atlas as has been recurated
            -> checker_compound should have npaid
         2 - This a potentially new compound
        """
        # Branch 2 - potentially new compound
        if not checker_compound.npaid:
            # Check if structure is a duplicate
            # First find connectivity matches
            if self.compound_flat_match(checker_compound):
                if self.compound_full_match(checker_compound):
                    self.add_problem(checker_compound.get_article_id(), "duplicate",
                                     comp_id=checker_compound.id)
            # Impose strict verification for flat matches
                else:
                    self.add_problem(checker_compound.get_article_id(), "flat_match",
                                     comp_id=checker_compound.id)
            # Check for name match (ignores "Not named")
            # if self.
        # Branch 1 - recurated compound
        else:
            pass

        self.check_source_organism(checker_compound)

    @staticmethod
    def create_checker_article(article, standardize=False):
        # Start fresh 
        if article.checker_article:
            db.session.delete(article.checker_article)
            commit()

        check_art = CheckerArticle(
            id=article.id,
            pmid=article.pmid,
            doi=article.doi,
            npa_artid=article.npa_artid,
            journal=article.journal,
            year=article.year,
            volume=article.volume,
            issue=article.issue,
            pages=article.pages,
            authors=article.authors,
            title=article.title,
            abstract=article.abstract
        )

        db_add_commit(check_art)
        return check_art

    def create_checker_compound(self, db_compound, standardize=False):
        # Start fresh
        if db_compound.checker_compound:
            db.session.delete(db_compound.checker_compound)
            commit()

        # Regularize the name
        # Especially important for "not named" or similar
        reg_name = NameString(db_compound.name)

        # Currently not standardizing because it takes ~10x longer
        reg_compound = Compound(
            db_compound.smiles,
            name=reg_name.get_name(),
            standardize=standardize
        )
        reg_compound.cleanStructure()

        genus, species = split_source_organism(db_compound.source_organism)
        check_compound = CheckerCompound(
            id=db_compound.id,
            name=reg_name.get_name(),
            formula=reg_compound.formula,
            smiles=reg_compound.smiles,
            inchi=reg_compound.inchi,
            inchikey=reg_compound.inchikey,
            molblock=reg_compound.molblock,
            source_genus=genus,
            source_species=species,
            npaid=db_compound.npaid
        )
        self.parse_external_ids(check_compound, db_compound)

        # We don't care about these yet...
        # if not check_compound.pubchem_id:
        #     self.get_checker_compound_cid(check_compound)

        db_add_commit(check_compound)
        return check_compound

    @staticmethod
    def get_checker_compound_cid(checker_compound):  
        checker_compound.pubchem_id = pubchem_search.get_cid_from_inchikey(
            checker_compound.inchikey)

    @staticmethod
    def parse_external_ids(checker_compound, db_compound):
        note = str(db_compound.article[0].notes)
        checker_compound.mibig_id = find_mibig_id(note)
        checker_compound.pubchem_id = find_pubchem_cid(note)
        checker_compound.berdy_id = find_berdy_id(note)

    def default_logger(self, *args, **kwargs):
        """Logging util function

        Parameters
        ----------
        worker : str
            Description of worker
        level : logging.LEVEL, optional
            Default to INFO logging, set to log.DEBUG for development
        """
        level = kwargs.get("level", "INFO")
        logging.basicConfig(
            format='%(levelname)s: %(message)s',
            level=logging.getLevelName(level)
        )

    def add_problem(self, art_id, problem, comp_id=None):
        self.review_list.append(
                Correction(art_id, problem, comp_id)
        )

    ## Start Checker Rules
    def check_doi(self, checker_article):
        regexp = re.compile(r'^(10.\d{4,9})\/([-._;()/:+A-Za-z0-9]+)$')
        if checker_article.doi:
            # if re.search(r'^(http|dx|doi)', checker_article.doi):
            checker_article.doi = clean_doi(checker_article.doi)
            match = regexp.match(checker_article.doi)
            if not match:
                self.add_problem(checker_article.id, "doi")

    def check_pmid(self, checker_article):
        # Make sure integer
        # This is enforced by datatype in DB
        pass
        
    def check_journal(self, checker_article):
        journal = Journal.check_journal_match(checker_article.journal)
        if journal:
            checker_article.journal = journal.journal
            checker_article.journal_abbrev = journal.abbrev
        else:
            self.add_problem(checker_article.id, "journal")
        
    def check_year(self, checker_article):
        # Make sure year string is valid
        match = re.match('^[1-2][0-9]{3}$', str(checker_article.year))
        if not match:
            self.add_problem(checker_article.id, "year")
        
    def check_volume(self, checker_article):
        # > 6 characters or special characters FLAG
        if checker_article.volume:
            if len(checker_article.volume) > 6:
                self.add_problem(checker_article.id, "volume")
        
    def check_issue(self, checker_article):
        # > 6 characters or special characters FLAG
        if checker_article.issue:
            if len(checker_article.issue) > 6:
                self.add_problem(checker_article.id, "issue")
        
    def check_pages(self, checker_article):
    # only first pages #s INT < 100,000
    # INT-INT
    # or alphabetical characters
    # Watchout for en dash and em dash
        pages = checker_article.pages
        if pages:
            pages = re.sub(u"\u2013|\u2014", "-", pages)
            if re.search('^[0-9]',pages):
                res = [x.strip() for x in pages.split('-') if x]
                res = clean_num_pages(res)
                # Add problem if any string is greater than 6 characters
                if [x for x in res if len(x) > 6]:
                    self.add_problem(checker_article.id, "pages")
                else:
                    checker_article.pages = '-'.join(res)
            elif re.search('^[A-Za-z]', pages):
                # Do nothing for now
                # max length = 10
                pass
            else:
                # Check pages if they don't start with Alphanumeric char
                self.add_problem(checker_article.id, "pages")
        
    def check_authors(self, checker_article):
        # at least 6 char, no numbers
        if (len(checker_article.authors) < 6 or
            has_numbers(checker_article.authors)):
            self.add_problem(checker_article.id, "authors")

    def check_title(self, checker_article):
        # at least > 6 char
        if (len(checker_article.title) < 6):
            self.add_problem(checker_article.id, "title")

    def check_abstract(self, checker_article):
        # If abstract, should be min 10 char 
        # Probably should be more!
        # "No abstract" is common
        if checker_article.abstract:
            if (len(checker_article.abstract) < 20):
                self.add_problem(checker_article.id, "abstract")

    def check_source_organism(self, checker_compound):
        genus = Genus.check_genus_match(checker_compound.source_genus)
        if genus:
            checker_compound.source_genus = genus.genus
        else:

            self.add_problem(checker_compound.get_article_id(), "genus",
                             comp_id=checker_compound.id)

    def compound_flat_match(self, compound):
        """
        Query NP Atlas DB to see if there is a flat match
        Return boolean match 
        """
        sess = self.atlasdb.startSession()
        res = sess.query(atlasdb.Compound)\
            .filter(atlasdb.Compound.inchikey.startswith(compound.inchikey.split('-')[0]))\
            .first()
        sess.close()
        return bool(res)

    def compound_full_match(self, compound):
        """
        Query NP Atlas DB to see if there is a full match
        Return boolean match 
        """
        sess = self.atlasdb.startSession()
        res = sess.query(atlasdb.Compound)\
            .filter(atlasdb.Compound.inchikey == compound.inchikey)\
            .first()
        sess.close()
        return bool(res)

    ## TODO: COMPLETE THIS FUNCTION
    def compound_name_match(self, compound):
        if compound.name != "Not named":
            sess = self.atlasdb.startSession()
            res = sess.query(atlasdb.Name)\
                    .filter(atlasdb.Name.name == compound.name)\
                    .first()



class Correction(object):
    """
    Object to store data which needs review
    """

    def __init__(self, art_id, problem, comp_id=None):
        self.verify_problem(problem)
        self.article_id = art_id
        self.compound_id = comp_id
        self.problem = problem

    def __repr__(self):
        return "{} -> {}".format(self.art_id + self.comp_id, self.problem)

    @staticmethod
    def verify_problem(problem):
        assert (
            problem == "doi" or problem == "pmid" or problem == "journal"
            or problem == "year" or problem == "volume" or problem == "issue"
            or problem == "authors" or problem == "title" or problem == "pages"
            or problem == "abstract" or problem == "duplicate" 
            or problem == "flat_match" or problem == "genus"
        )


# =============================================================================
# ==========                Helper functions                      =============
# =============================================================================

def db_add_commit(db_object):
    db.session.add(db_object)
    commit()


def commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def find_mibig_id(note):
    """
    Search note string for BGC string
    """
    return find_id_string("BGC[0-9]+", note)


def find_pubchem_cid(note):
    """
    Search note string for CID string
    """
    return find_id_string("CID[0-9]+", note)


def find_berdy_id(note):
    """
    Search note string for BERDY string
    """
    return find_id_string("BERDY[0-9]+", note)


def find_id_string(regexp_string, input_string):
    result = re.search(regexp_string, input_string)
    if result:
        return get_id_int(result.group())
    else:
        return None

def get_id_int(id_string):
    """
    Take an ID string like BGC000001 and return integer value
    """
    try:
        return int(re.sub("[A-Za-z]+", "", id_string))
    except AttributeError:
        return None


def clean_doi(doi):
    regexp = re.compile("(https?://)(dx.)?doi.org/")
    return regexp.sub("", doi).strip()


def clean_num_pages(page_list):
    """
    Try to expand page numbers so that 100-10 -> 100-110
    """
    if len(page_list) == 2:
        if len(page_list[1]) < len(page_list[0]):
            plen = len(page_list[0])-len(page_list[1])
            page_list[1] = page_list[0][0:plen]+page_list[1]
    return page_list


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


def split_source_organism(org_string):
    data = [x for x in org_string.split(' ') if x]
    # Check data makes sense
    if len(data) > 1:
        genus = data[0]
        species = ' '.join(data[1:])
        species = clean_species(species)
    else:
        genus = data[0]
        species = "sp."
    return genus, species

def clean_species(species_string):
    species_string = decapitalize_first(species_string)
    # species_string = re.sub("^(?!sp.)sp$", "sp.", species_string)
    return re.sub(r'\b(sp|sps|sps\.|spp\.|spp)(?!\S)', "sp.", species_string, re.IGNORECASE)
