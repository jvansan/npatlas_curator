from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from ..models import Curator


class CuratorForm(FlaskForm):
    """
    For admin to add or edit curator
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First name')
    last_name = StringField('Last name')
    password = StringField('Password', validators=[DataRequired(), EqualTo('confirm_password')])
    confirm_password = StringField('Confirm Password')
    submit = SubmitField('Submit Curator')

    # def validate_email(self, field):
    #     if Curator.query.filter_by(email=field.data).first():
    #         raise ValidationError('Email is already in use.')

    # def validate_user(self, field):
    #     if Curator.query.filter_by(username=field.data).first():
    #         raise ValidationError('Username is already in use.')
