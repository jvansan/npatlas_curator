from flask_wtf import FlaskForm
from wtforms import (BooleanField, HiddenField, IntegerField, RadioField,
                     SelectField, StringField, SubmitField)
from wtforms.validators import DataRequired, Optional

from .validators import NpaIdValidator, SimpleValidator, TypeSelectValidator


class ResolveBaseForm(FlaskForm):
    force = BooleanField('Force Data')
    submit = SubmitField('Submit Data')
    reject = SubmitField('Reject Article')


class SimpleStringForm(ResolveBaseForm):
    value = StringField('Value', validators=[SimpleValidator()],
                        render_kw={'autocomplete':'off'})
    type_ = HiddenField('')


class SimpleIntForm(ResolveBaseForm):
    value = IntegerField('Value', validators=[SimpleValidator()], 
                         render_kw={'autocomplete':'off'})
    type_ = HiddenField('')


class JournalForm(ResolveBaseForm):
    value = HiddenField('')
    select = SelectField('Select Option', choices=[
                         ("alt", "Alternative Journal"), ("new", "New Journal")],
                         id="journalSelect",
                        )
    new_journal_full = StringField('Add New Journal (Enter Full Journal Name)')
    new_journal_abbrev = StringField('Add New Journal (Enter Journal Abbrev)')
    alt_journal = StringField('Add Alternative Journal (Select Correct Journal)',
                              render_kw={'autocomplete': 'on'})



GENUS_TYPES = [(None, ""),
               ("Bacterium", "Bacterium"), ("Fungus", "Fugus"), 
               ("Bacterium_Nonvalid", "Bacterium (Non official)"),
               ("Fungus_Nonvalid", "Fungus (Non official)"),
               ("Other", "Other (non-microbe)")
              ]

class GenusForm(ResolveBaseForm):
    value = HiddenField('')
    select = SelectField('Select Option', choices=[
                         ('alt', "Alternative Genus"), ("new", "New Genus")],
                         id="genusSelect")
    genus_type = SelectField('Select Type', choices=GENUS_TYPES,
                              validators=[TypeSelectValidator()])
    new_genus_name = StringField('Add New Genus Name')
    alt_genus_name = StringField('Add Alternative Genus Name (Select Genus Journal)',
                                 render_kw={'autocomplete': 'on'})


COMPOUND_OPTIONS = [
        ("new", "New Compound"),
        ("replace", "Replace Atlas Compound"),
        ("keep", "Keep Atlas Compound"),
        ("needs_work", "Needs Work")
]

class CompoundForm(ResolveBaseForm):
    value = HiddenField('')
    select = SelectField("Select Option:", choices=COMPOUND_OPTIONS, 
                        validators=[DataRequired()], id="compoundSelect")
    npaid = IntegerField("Replace NPA ID:", validators=[Optional()])
    notes = StringField("Notes:")
