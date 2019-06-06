import logging

from flask import render_template, Blueprint, current_app

from mementoembed.version import __appversion__

module_logger = logging.getLogger('mementoembed.ui')

bp = Blueprint('ui', __name__)

@bp.route('/')
def main_page():
    return render_template('index.html', pagetitle = "MementoEmbed", appversion = __appversion__,
    thumbnail_viewport_width=current_app.config['THUMBNAIL_VIEWPORT_WIDTH'],
    thumbnail_viewport_height=current_app.config['THUMBNAIL_VIEWPORT_HEIGHT'],
    thumbnail_width=current_app.config['THUMBNAIL_WIDTH'],
    thumbnail_height=current_app.config['THUMBNAIL_HEIGHT'],
    thumbnail_timeout=current_app.config['THUMBNAIL_TIMEOUT'],
    imagereel_width=current_app.config['IMAGEREEL_WIDTH'],
    imagereel_height=current_app.config['IMAGEREEL_HEIGHT'],
    imagereel_duration=current_app.config['IMAGEREEL_DURATION'],
    imagereel_count=current_app.config['IMAGEREEL_COUNT']
    )

@bp.route('/about/', methods=['GET', 'HEAD'])
def about_page():
    return render_template('about.html', pagetitle = "MementoEmbed", appversion = __appversion__)
