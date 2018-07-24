import logging

from flask import render_template, Blueprint, request, redirect, url_for, current_app

from mementoembed.version import __appversion__

module_logger = logging.getLogger('mementoembed.ui.product')

bp = Blueprint('ui.product', __name__)

@bp.route('/ui/product/socialcard/')
@bp.route('/ui/product/thumbnail/')
@bp.route('/ui/')
def ui_product_no_urim():
    return redirect(url_for('ui.main_page'))

@bp.route('/ui/product/socialcard/<path:subpath>')
def generate_social_card(subpath):

    social_card_template = render_template("new_social_card.html",
        urim = "{{ urim }}",
        urir = "{{ urir }}",
        image = "{{ image }}",
        archive_uri = "{{ archive_uri }}",
        archive_favicon = "{{ archive_favicon }}",
        archive_collection_id = "{{ archive_collection_id }}",
        archive_collection_uri = "{{ archive_collection_uri }}",
        archive_collection_name = "{{ archive_collection_name }}",
        archive_name = "{{ archive_name }}",
        original_favicon = "{{ original_favicon }}",
        original_domain = "{{ original_domain }}",
        original_link_status = "{{ original_link_status }}",
        surrogate_creation_time = "{{ surrogate_creation_time }}",
        memento_datetime = "{{ memento_datetime }}",
        me_title = "{{ me_title }}",
        me_snippet = "{{ me_snippet }}",
        server_domain = "{{ server_domain }}"
    )

    return render_template('generate_social_card.html', 
        urim = subpath,
        pagetitle="MementoEmbed - Generate a Social Card",
        surrogate_type="Social Card",
        textdata_endpoint="/services/memento/contentdata/",
        archivedata_endpoint="/services/memento/archivedata/",
        originalresourcedata_endpoint="/services/memento/originalresourcedata/",
        bestimage_endpoint="/services/memento/bestimage/",
        social_card_template=social_card_template,
        appversion = __appversion__
    ), 200

@bp.route('/ui/product/thumbnail/<path:subpath>', methods=['GET', 'POST'])
def generate_thumbnail(subpath):

    prefs = {}
    prefs['viewport_height'] = int(current_app.config['THUMBNAIL_VIEWPORT_HEIGHT'])
    prefs['viewport_width'] = int(current_app.config['THUMBNAIL_VIEWPORT_WIDTH'])
    prefs['timeout'] = int(current_app.config['THUMBNAIL_TIMEOUT'])
    prefs['thumbnail_height'] = int(current_app.config['THUMBNAIL_HEIGHT'])
    prefs['thumbnail_width'] = int(current_app.config['THUMBNAIL_WIDTH'])

    if request.method == 'POST':

        prefs['viewport_height'] = request.form['thumbnail_viewport_height']
        prefs['viewport_width'] = request.form['thumbnail_viewport_width']
        prefs['thumbnail_height'] = request.form['thumbnail_height']
        prefs['thumbnail_width'] = request.form['thumbnail_width']
        prefs['timeout'] = request.form['thumbnail_timeout']

    else:

        if 'Prefer' in request.headers:

            preferences = request.headers['Prefer'].split(',')

            for pref in preferences:
                key, value = pref.split('=')
                prefs[key] = int(value)

            module_logger.debug("The user hath preferences! ")

    return render_template('generate_thumbnail.html', 
        urim = subpath,
        pagetitle="MementoEmbed - Generate a Thumbnail",
        surrogate_type="Thumbnail",
        thumbnail_endpoint="/services/product/thumbnail/",
        appversion = __appversion__,
        viewport_height=prefs['viewport_height'],
        viewport_width=prefs['viewport_width'],
        timeout=prefs['timeout'],
        thumbnail_height=prefs['thumbnail_height'],
        thumbnail_width=prefs['thumbnail_width']
    ), 200
