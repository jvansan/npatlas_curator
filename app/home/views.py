from flask import render_template, abort, send_from_directory
from flask_login import current_user, login_required

from . import home


@home.route('/')
def homepage():
    """
    Render homepage template as '/'
    """
    return render_template('home/index.html', title='Welcome')


@home.route('/guide')
def guide():
    """
    Render FAQ/Curation Guide template as "/guide"
    """
    return render_template('home/guide.html', title="Curation Guide")


@home.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # prevent non-admins from accessing the page
    if not current_user.is_admin:
        abort(403)

    return render_template('home/admin_dashboard.html', title="Dashboard")


@home.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static, request.path[1:])
