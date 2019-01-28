import re

from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, BooleanField, SubmitField,
                     HiddenField)
from wtforms.validators import ValidationError

# from ..data.validators import ValidateDOI, ValidateYear


class SimpleValidator(object):
    def __init__(self):
        self.message = None

    def __call__(self, form, field):
        type_ = form['type_'].data
        self.message = u'{}: {} -- Format incorrect'.format(type_, field.data)
        if type_ == "year":
            try:
                year = int(field.data)
            except TypeError:
                raise ValidationError(self.message)
            if not 1800 < year < 3000:
                raise ValidationError(self.message)
        elif type_ == "pmid":
            try:
                pmid = int(field.data)
            except TypeError:
                raise ValidationError(self.message)
        elif type_ == "doi":
            doi = field.data
            regexp = re.compile(r'^10.\d{4,9}')
            if not doi:
                pass
            elif not self.regexp.match(doi) or re.search(r'\s\n\t', doi):
                raise ValidationError(self.message)
        elif type_ in ["volume", "issue"]:
            if not field.data:
                pass
            elif len(field.data) > 6:
                raise ValidationError(self.message)
        elif type_ in ["authors", "title", "abstract"]:
            try:
                if len(field.data) > 10:
                    raise ValidationError(self.message)
            except AttributeError:
                raise ValidationError(self.message)
        elif type_ == "pages":
            pass
        else:
            raise ValidationError(type_)

class SimpleStringForm(FlaskForm):
    value = StringField('Value', validators=[SimpleValidator()],
                        render_kw={'autocomplete':'off'})
    type_ = HiddenField('')
    force = BooleanField('Force Data')
    submit = SubmitField('Submit Data')

class SimpleIntForm(FlaskForm):
    value = IntegerField('Value', validators=[SimpleValidator()], 
                         render_kw={'autocomplete':'off'})
    type_ = HiddenField('')
    force = BooleanField('Force Data')
    submit = SubmitField('Submit Data')