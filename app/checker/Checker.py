import re
import logging
import time

from .Compound import Compound
from .NameString import NameString
from .. import db
from ..models import CheckerArticle, CheckerCompound, CheckerDataset, Dataset
from ..utils import atlasdb, pubchem_search


class Checker(object):

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


    def run(self):
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
                check_compound = self.create_checker_compound(compound)
                self.check_compound(check_compound)

            # time.sleep(1)

        self.logger.info("Done checking!")
        dataset.checker_dataset.completed = True
        commit()


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
        pass
    

    @staticmethod
    def create_checker_article(article):
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


    def create_checker_compound(self, db_compound):
        # Start fresh
        if db_compound.checker_compound:
            db.session.delete(db_compound.checker_compound)
            commit()

        # Regularize the name
        # Especially important for "not named" or similar
        reg_name = NameString(db_compound.name)
        reg_name.regularize_name()

        reg_compound = Compound(
            db_compound.smiles,
            name=reg_name.get_name(),
            standardize=False
        )
        reg_compound.cleanStructure()

        check_compound = CheckerCompound(
            id=db_compound.id,
            name=reg_name.get_name(),
            formula=reg_compound.formula,
            smiles=reg_compound.smiles,
            inchi=reg_compound.inchi,
            inchikey=reg_compound.inchikey,
            molblock=reg_compound.molblock,
            source_genus=db_compound.source_organism.split()[0],
            source_species=" ".join(db_compound.source_organism.split()[1:]),
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

    def add_problem(self, art_id, problem, value):
        self.review_list.append(
                Correction(art_id, problem, value)
        )

    ## Start Checker Rules
    def check_doi(self, checker_article):
        regexp = re.compile(r'^(10.\d{4,9})\/([-._;()/:+A-Za-z0-9]+)$')
        if checker_article.doi:
            if re.search(r'^(http|dx|doi)', checker_article.doi):
                checker_article.doi = clean_doi(checker_article.doi)
            match = regexp.match(checker_article.doi)
            if not match:
                self.add_problem(checker_article.id, "doi",
                                 checker_article.doi)

    def check_pmid(self, checker_article):
        # Make sure integer
        # This is enforced by datatype in DB
        pass
        
    def check_journal(self, checker_article):
        pass
        
    def check_year(self, checker_article):
        # Make sure year string is valid
        match = re.match('^[1-2][0-9]{3}$', str(checker_article.year))
        if not match:
            self.add_problem(checker_article.id, "year",
                             checker_article.year)
        
    def check_volume(self, checker_article):
        # > 6 characters or special characters FLAG
        if checker_article.volume:
            if len(checker_article.volume) > 6:
                self.add_problem(checker_article.id, "volume",
                                 checker_article.volume)
        
    def check_issue(self, checker_article):
        # > 6 characters or special characters FLAG
        if checker_article.issue:
            if len(checker_article.issue) > 6:
                self.add_problem(checker_article.id, "volume",
                                 checker_article.issue)
        
    def check_pages(self, checker_article):
    # only first pages #s INT < 100,000
    # INT-INT
    # or alphabetical characters
        pages = checker_article.pages
        if pages:
            if re.match('^[0-9]',pages):
                res = (x for x in pages.split('-') if x)
                # Add problem if any string is greater than 6 characters
                if [x for x in res if len(x) > 6]:
                    self.add_problem(checker_article.id, "pages",
                                     checker_article.pages)
                else:
                    checker_article.pages = '-'.join(res)
            elif re.match('^[A-Za-z]', pages):
                # Do nothing for now
                pass
            else:
                # Check pages if they don't start with Alphanumeric char
                self.add_problem(checker_article.id, "pages",
                                 checker_article.pages)
        
    def check_authors(self, checker_article):
        # at least 6 char, no numbers
        if (len(checker_article.authors) < 6 or
            has_numbers(checker_article.authors)):
            self.add_problem(checker_article.id, "authors",
                             checker_article.authors)

    def check_title(self, checker_article):
        # at least > 6 char
        if (len(checker_article.title) < 6):
            self.add_problem(checker_article.id, "title",
                             checker_article.title)

    def check_abstract(self, checker_article):
        # If abstract, should be min 10 char 
        # Probably should be more!
        if checker_article.abstract:
            if (len(checker_article.abstract) < 10):
                self.add_problem(checker_article.id, "abstract",
                                 checker_article.abstract)


class Correction(object):
    """
    Object to store data which needs review
    """

    def __init__(self, art_id, problem, value):
        self.verify_problem(problem)
        self.art_id = art_id
        self.problem = problem
        self.value = value

    def __repr__(self):
        return "{} -> {}".format(self.art_id, self.problem)

    @staticmethod
    def verify_problem(problem):
        assert (
            problem == "doi" or problem == "pmid" or problem == "journal"
            or problem == "year" or problem == "volume" or problem == "issue"
            or problem == "authors" or problem == "title" or 
            problem == "abstract"
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
    return regexp.sub("", doi)

def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)