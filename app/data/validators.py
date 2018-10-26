import re
from wtforms.validators import ValidationError

# Custom Validators
class ValidateYear(object):
    def __init__(self):
        self.message = u'Year field is not valid. Must be between 1800-3000.'

    def __call__(self, form, field):
        try:
            year = int(field.data)
        except TypeError:
            raise ValidationError(self.message)
        if not 1800 < year < 3000:
            raise ValidationError(self.message)


class ValidateDOI(object):
    def __init__(self):
        self.message = u"""DOI does not appear valid.
                           Must start with r'10.\d{4,9}' pattern
                           and may not contain whitespace"""
        self.regexp = re.compile(r'^10.\d{4,9}')

    def __call__(self, form, field):
        doi = field.data
        if not doi:
            pass
        elif not self.regexp.match(doi) or re.search(r'\s\n\t', doi):
            raise ValidationError(self.message)

class ValidateNumCompounds(object):
    def __init__(self):
        self.message = u"""Reported number of compounds does not match
                           number of curated compounds. Please correct or
                           select 'Needs Work' """

    def __call__(self, form, field):
        other = form['compounds']
        if field.data != len(other.data):
            raise ValidationError(self.message)