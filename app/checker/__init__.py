from flask import Blueprint

checker = Blueprint('checker', __name__)

from . import views