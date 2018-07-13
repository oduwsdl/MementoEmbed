import logging

from flask import render_template, Blueprint

from mementoembed.version import __appversion__

module_logger = logging.getLogger('mementoembed.ui')

bp = Blueprint('ui', __name__)

@bp.route('/')
def main_page():
    return render_template('index.html', pagetitle = "MementoEmbed", appversion = __appversion__)

@bp.route('/about/', methods=['GET', 'HEAD'])
def about_page():
    return render_template('about.html', pagetitle = "MementoEmbed", appversion = __appversion__)
