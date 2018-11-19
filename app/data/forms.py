from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, IntegerField,
                     TextAreaField, FormField, FieldList, BooleanField)
from wtforms import Form as NoCsrfForm
from wtforms.validators import DataRequired, length, Optional

from .validators import ValidateYear, ValidateDOI, ValidateNumCompounds
from ..models import Compound
from .. import db


class ModelFieldList(FieldList):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model", None)
        super(ModelFieldList, self).__init__(*args, **kwargs)
        if not self.model:
            raise ValueError("ModelFieldList requires model to be set")

    def populate_obj(self, obj, name):
        while len(getattr(obj, name)) < len(self.entries):
            newModel = self.model()
            db.session.add(newModel)
            getattr(obj, name).append(newModel)
        while len(getattr(obj, name)) > len(self.entries):
            db.session.delete(getattr(obj, name).pop())
        super(ModelFieldList, self).populate_obj(obj, name)


class CompoundForm(NoCsrfForm):
    """
    Form for compound curation
    """

    id = IntegerField('ID')
    name = StringField('Compound Name', validators=[DataRequired()])
    smiles = StringField('SMILES', validators=[DataRequired()])
    source_organism = StringField('Source Organism',
                                   validators=[DataRequired()])
    npaid = IntegerField('Article in Atlas?', validators=[Optional()], 
                         filters = [lambda x: x or None])

class ArticleForm(FlaskForm):
    """
    Form for users to curate article data
    """

    doi = StringField('DOI', validators=[Optional(), ValidateDOI()],
                      filters = [lambda x: x or None])
    pmid = IntegerField('PMID', validators=[Optional()])
    journal = StringField('Journal', validators=[DataRequired(),
                                                length(max=255)])
    title = TextAreaField('Title', validators=[DataRequired()],
                          render_kw={"rows": 3})
    abstract = TextAreaField('Abstract', render_kw={"rows": 8}, 
                             validators=[Optional()],
                             filters = [lambda x: x or None])

    year = IntegerField('Year', validators=[DataRequired(), ValidateYear()])
    volume = StringField('Volume', validators=[Optional(), length(max=10)],
                         filters = [lambda x: x or None])
    issue = StringField('Issue', validators=[Optional(), length(max=10)],
                        filters = [lambda x: x or None])
    pages = StringField('Pages', validators=[Optional(), length(max=20)],
                        filters = [lambda x: x or None])
    authors = TextAreaField('Authors', validators=[DataRequired()],
                                                 render_kw={"rows": 2})
    notes = TextAreaField('Notes', validators=[Optional()],
                          render_kw={"rows": 2},
                          filters = [lambda x: x or None])
    needs_work = BooleanField('Needs Work')
    num_compounds = IntegerField('Number of Compounds',
                                 validators=[DataRequired(),
                                             ValidateNumCompounds()])
    compounds = ModelFieldList(FormField(CompoundForm), model=Compound,
                                    min_entries=1)
    # add_compound = SubmitField('Add Compound')
    submit = SubmitField('Submit Data')
    reject = SubmitField('Reject Article')
