import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
from atlasdb import atlasdb as atlas
from app import db, create_app
from app.models import Compound, Article, Dataset, Curator

import click

CONFIG_NAME = os.getenv("FLASK_CONFIG")
app = create_app(CONFIG_NAME)

def get_first_N_article_with_compounds(sess, N):

    articles = []
    for idx in range(1, N + 1):
        article = sess.query(atlas.Reference).filter(atlas.Reference.id==idx).first()
        compounds = sess.query(atlas.Compound)\
            .filter(atlas.Reference.id==atlas.CompoundOrigin.reference_id)\
            .filter(atlas.CompoundOrigin.compound_id==atlas.Compound.id)\
            .filter(atlas.Reference.id == idx)\
            .all()
        articles.append((article, compounds))
    return articles

def get_compound_origin(compound, sess):

    org = sess.query(atlas.Origin)\
                .filter(atlas.Origin.id==atlas.CompoundOrigin.origin_id)\
                .filter(atlas.CompoundOrigin.compound_id==atlas.Compound.id)\
                .filter(atlas.Compound.id==compound.id)\
                .first()

    return org

@app.cli.command()
def run_command():
    atlas.dbInit("mysql+pymysql", "jvansan", "", "127.0.0.1", "np_atlas_2018_07")
    sess = atlas.startSession()
    curator = Curator.query.filter_by(username="jvansan").first()
    articles = get_first_N_article_with_compounds(sess, 100)
    ds_articles = []
    for art_compound in articles:
        a = art_compound[0]
        compounds = []
        for c in art_compound[1]:
            org = get_compound_origin(c, sess)
            org_string = org.genus.name + " " + org.species
            compounds.append(
                Compound(
                    name=c.names[0].name,
                    smiles=c.smiles,
                    source_organism=org_string
                    ))
            # Make sure to sort the names of the compounds before insertion
            compounds.sort(key=lambda x: x.name)
        art = Article(
            pmid=a.pmid, journal=a.journal.title,
            year=a.year, volume=a.volume,
            issue=a.issue, pages=a.pages,
            authors=a.authors, doi=a.doi,
            title=a.title, abstract=a.abstract,
            num_compounds=len(compounds),
            compounds=compounds
                    )

        ds_articles.append(art)

    ds = Dataset(curator=curator, articles=ds_articles)
    db.session.add(ds)
    db.session.commit()

if __name__ == "__main__":
    atlas.dbInit("mysql+pymysql", "jvansan", "", "127.0.0.1", "np_atlas_2018_07")
    sess = atlas.startSession()
    articles = get_first_ten_article_with_compounds(sess)
    for art in articles:
        print(art[0].title, len(art[1]))
        print([x.names[0].name for x in art[1]])
        art[1].sort(key=lambda x: x.names[0].name)
        print([x.names[0].name for x in art[1]])
