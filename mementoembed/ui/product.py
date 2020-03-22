import logging

from flask import render_template, Blueprint, request, redirect, url_for, current_app

from mementoembed.version import __appversion__

module_logger = logging.getLogger('mementoembed.ui.product')

bp = Blueprint('ui.product', __name__)

@bp.route('/ui/product/wordcloud/')
@bp.route('/ui/product/imagereel/')
@bp.route('/ui/product/socialcard/')
@bp.route('/ui/product/thumbnail/')
@bp.route('/ui/')
def ui_product_no_urim():
    return redirect(url_for('ui.main_page'))

@bp.route('/ui/product/socialcard/<path:subpath>', methods=['HEAD', 'GET'])
def generate_social_card(subpath):

    prefs = {}
    prefs['datauri_favicon'] = 'no'
    prefs['datauri_image'] = 'no'
    prefs['remove_remote_javascript'] = 'no'



    # because Flask trims off query strings
    urim = request.full_path[len('/ui/product/socialcard/'):]
    urim = urim[:-1] if urim[-1] == '?' else urim

    if urim[0:4] != "http":

        pathprefs, urim = urim.split('/', 1)
        module_logger.debug("prefs: {}".format(pathprefs))
        module_logger.debug("urim: {}".format(urim))

        for entry in pathprefs.split(','):
            module_logger.debug("examining entry {}".format(entry))
            key, value = entry.split('=')
            module_logger.debug("setting preference {} to value {}".format(key, value))
            prefs[key] = value

    if prefs['remove_remote_javascript'] == 'yes':

        social_card_template = render_template("social_card_htmlonly.html",
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

    else:

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
        urim = urim,
        pagetitle="MementoEmbed - Generate a Social Card",
        surrogate_type="Social Card",
        textdata_endpoint="/services/memento/contentdata/",
        archivedata_endpoint="/services/memento/archivedata/",
        originalresourcedata_endpoint="/services/memento/originalresourcedata/",
        bestimage_endpoint="/services/memento/bestimage/",
        carddata_endpoint="/services/product/socialcard/",
        social_card_template=social_card_template,
        appversion = __appversion__,
        datauri_favicon = prefs['datauri_favicon'],
        datauri_image = prefs['datauri_image'],
        remove_remote_javascript = prefs['remove_remote_javascript']
    ), 200

@bp.route('/ui/product/thumbnail/<path:subpath>', methods=['HEAD', 'GET'])
def generate_thumbnail(subpath):

    prefs = {}
    prefs['viewport_height'] = int(current_app.config['THUMBNAIL_VIEWPORT_HEIGHT'])
    prefs['viewport_width'] = int(current_app.config['THUMBNAIL_VIEWPORT_WIDTH'])
    prefs['timeout'] = int(current_app.config['THUMBNAIL_TIMEOUT'])
    prefs['thumbnail_height'] = int(current_app.config['THUMBNAIL_HEIGHT'])
    prefs['thumbnail_width'] = int(current_app.config['THUMBNAIL_WIDTH'])
    prefs['remove_banner'] = current_app.config['THUMBNAIL_REMOVE_BANNERS'].lower()

    module_logger.debug("received path {}".format(subpath))

    # because Flask trims off query strings
    urim = request.full_path[len('/ui/product/thumbnail/'):]
    urim = urim[:-1] if urim[-1] == '?' else urim

    if urim[0:4] != "http":

        pathprefs, urim = urim.split('/', 1)
        module_logger.debug("prefs: {}".format(pathprefs))
        module_logger.debug("urim: {}".format(urim))

        for entry in pathprefs.split(','):
            module_logger.debug("examining entry {}".format(entry))
            key, value = entry.split('=')
            module_logger.debug("setting preference {} to value {}".format(key, value))

            try:
                prefs[key] = int(value)
            except ValueError:

                if key == 'remove_banner':
                    prefs[key] = value
                else:
                    module_logger.exception("failed to set value for preference {}".format(key))

    return render_template('generate_thumbnail.html', 
        urim = urim,
        pagetitle="MementoEmbed - Generate a Thumbnail",
        surrogate_type="Thumbnail",
        thumbnail_endpoint="/services/product/thumbnail/",
        appversion = __appversion__,
        viewport_height=prefs['viewport_height'],
        viewport_width=prefs['viewport_width'],
        timeout=prefs['timeout'],
        thumbnail_height=prefs['thumbnail_height'],
        thumbnail_width=prefs['thumbnail_width'],
        remove_banner=prefs['remove_banner']
    ), 200

@bp.route('/ui/product/imagereel/<path:subpath>', methods=['HEAD', 'GET'])
def generate_imagereel(subpath):

    prefs = {}
    prefs['imagereel_height'] = int(current_app.config['IMAGEREEL_HEIGHT'])
    prefs['imagereel_width'] = int(current_app.config['IMAGEREEL_WIDTH'])
    prefs['duration'] = int(current_app.config['IMAGEREEL_DURATION'])
    prefs['imagecount'] = int(current_app.config['IMAGEREEL_COUNT'])

    module_logger.debug("received path {}".format(subpath))

    # because Flask trims off query strings
    urim = request.full_path[len('/ui/product/imagereel/'):]
    urim = urim[:-1] if urim[-1] == '?' else urim

    if urim[0:4] != "http":

        pathprefs, urim = urim.split('/', 1)
        module_logger.debug("prefs: {}".format(pathprefs))
        module_logger.debug("urim: {}".format(urim))

        for entry in pathprefs.split(','):
            module_logger.debug("examining entry {}".format(entry))
            key, value = entry.split('=')
            module_logger.debug("setting preference {} to value {}".format(key, value))

            try:
                prefs[key] = int(value)
            except ValueError:

                if key == 'remove_banner':
                    prefs[key] = value
                else:
                    module_logger.exception("failed to set value for preference {}".format(key))

    return render_template('generate_imagereel.html', 
        urim = urim,
        pagetitle="MementoEmbed - Generate an Imagereel",
        surrogate_type="Imagereel",
        imagereel_endpoint="/services/product/imagereel/",
        appversion = __appversion__,
        imagereel_width=prefs['imagereel_width'],
        imagereel_height=prefs['imagereel_height'],
        duration=prefs['duration'],
        imagecount=prefs['imagecount']
    ), 200

@bp.route('/ui/product/wordcloud/<path:subpath>', methods=['HEAD', 'GET'])
def generate_wordcloud(subpath):

    prefs = {}

    module_logger.debug("received path {}".format(subpath))

    # because Flask trims off query strings
    urim = request.full_path[len('/ui/product/imagereel/'):]
    urim = urim[:-1] if urim[-1] == '?' else urim

    if urim[0:4] != "http":

        pathprefs, urim = urim.split('/', 1)
        module_logger.debug("prefs: {}".format(pathprefs))
        module_logger.debug("urim: {}".format(urim))

        for entry in pathprefs.split(','):
            module_logger.debug("examining entry {}".format(entry))
            key, value = entry.split('=')
            module_logger.debug("setting preference {} to value {}".format(key, value))

            try:
                prefs[key] = int(value)
            except ValueError:

                if key == 'remove_banner':
                    prefs[key] = value
                else:
                    module_logger.exception("failed to set value for preference {}".format(key))

    return render_template('generate_wordcloud.html', 
        urim = urim,
        pagetitle="MementoEmbed - Generate a Word Cloud",
        surrogate_type="Word Cloud",
        wordcloud_endpoint="/services/product/wordcloud/",
        appversion = __appversion__
    ), 200

@bp.route('/ui/product/docreel/<path:subpath>', methods=['HEAD', 'GET'])
def generate_docreel(subpath):

    prefs = {}

    module_logger.debug("received path {}".format(subpath))

    # because Flask trims off query strings
    urim = request.full_path[len('/ui/product/docreel/'):]
    urim = urim[:-1] if urim[-1] == '?' else urim

    if urim[0:4] != "http":

        pathprefs, urim = urim.split('/', 1)
        module_logger.debug("prefs: {}".format(pathprefs))
        module_logger.debug("urim: {}".format(urim))

        for entry in pathprefs.split(','):
            module_logger.debug("examining entry {}".format(entry))
            key, value = entry.split('=')
            module_logger.debug("setting preference {} to value {}".format(key, value))

            try:
                prefs[key] = int(value)
            except ValueError:

                if key == 'remove_banner':
                    prefs[key] = value
                else:
                    module_logger.exception("failed to set value for preference {}".format(key))

    return render_template('generate_docreel.html', 
        urim = urim,
        pagetitle="MementoEmbed - Generate a Docreel",
        surrogate_type="Docreel",
        docreel_endpoint="/services/product/docreel/",
        appversion = __appversion__
    ), 200
