import re

from wtforms.validators import ValidationError


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
            elif not regexp.match(doi) or re.search(r'\s\n\t', doi):
                raise ValidationError(self.message)
        elif type_ in ["volume", "issue"]:
            if not field.data:
                pass
            elif len(field.data) > 6:
                raise ValidationError(self.message)
        elif type_ in ["authors", "title", "abstract"]:
            try:
                if len(field.data) < 10:
                    raise ValidationError(self.message)
            except AttributeError:
                raise ValidationError(self.message)
        elif type_ == "pages":
            pass
        else:
            raise ValidationError(type_)


class TypeSelectValidator(object):
    def __init__(self):
        self.message = "Select a valid organism type."

    def __call__(self, form, field):
        if not form['genus_type'].data:
            raise ValidationError(self.message)


class NpaIdValidator(object):

    def __init__(self):
        self.message = "Please enter an NPAID"

    def __call__(self, form, field):
        other = form['select']
        if other.data == "replace" and not field.data:
            raise ValidationError(self.message)