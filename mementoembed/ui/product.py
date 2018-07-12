import logging

from flask import render_template, Blueprint

module_logger = logging.getLogger('mementoembed.ui.product')

bp = Blueprint('ui.product', __name__)

@bp.route('/ui/product/socialcard/<path:subpath>')
def generate_social_card():
    return render_template('generate_social_card.html', 
        pagetitle="MementoEmbed - Generate a Social Card",
        surrogate_type="Social Card",
        baseuri="/generate/socialcard/",
        oembed_endpoint="/services/oembed?&format=json&url="
    ), 200

@bp.route('/ui/product/thumbnail/<path:subpath>')
def generate_thumbnail():
    return "Not yet implemented", 500
