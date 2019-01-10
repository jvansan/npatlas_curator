from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user

from . import auth
from .. import db
from ..models import Curator
from .forms import LoginForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle requests to "/login"
    Log a curator in through login form
    """
    form = LoginForm()
    if form.validate_on_submit():
        curator = Curator.query.filter_by(username=form.username.data).first()
        if curator and curator.verify_password(form.password.data):
            # login
            login_user(curator)

            # redirect to appropriate place
            if curator.is_admin:
                return redirect(url_for('home.admin_dashboard'))
            else:
                return redirect(url_for('data.curator_dashboard', cur_id=curator.id))
        else:
            flash('Invalid username or password.')

    # load login template
    return render_template('auth/login.html', form=form, title="Login")


@auth.route('/logout')
@login_required
def logout():
    """
    Handle requests to "/logout"
    Log a curator out through link
    """
    logout_user()
    flash('You have successfully been logged out.')

    # redirect to home page
    return redirect(url_for('auth.login'))
