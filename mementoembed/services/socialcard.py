import logging
import json

import htmlmin
import requests_cache

from flask import render_template


module_logger = logging.getLogger('mementoembed.services.socialcard')

def generate_social_card_html(urim, surrogate, urlroot, image=True):

    if image:
        return htmlmin.minify( render_template(
            "social_card.html",
            urim = urim,
            urir = surrogate.original_uri,
            image = surrogate.striking_image,
            archive_uri = surrogate.archive_uri,
            archive_favicon = surrogate.archive_favicon,
            archive_collection_id = surrogate.collection_id,
            archive_collection_uri = surrogate.collection_uri,
            archive_collection_name = surrogate.collection_name,
            archive_name = surrogate.archive_name,
            original_favicon = surrogate.original_favicon,
            original_domain = surrogate.original_domain,
            original_link_status = surrogate.original_link_status,
            surrogate_creation_time = surrogate.creation_time,
            memento_datetime = surrogate.memento_datetime,
            me_title = surrogate.title,
            me_snippet = surrogate.text_snippet,
            server_domain = urlroot
        ), remove_empty_space=True, 
        remove_optional_attribute_quotes=False )
    else:
        return htmlmin.minify( render_template(
            "social_card.html",
            urim = urim,
            urir = surrogate.original_uri,
            image = None,
            archive_uri = surrogate.archive_uri,
            archive_favicon = surrogate.archive_favicon,
            archive_collection_id = surrogate.collection_id,
            archive_collection_uri = surrogate.collection_uri,
            archive_collection_name = surrogate.collection_name,
            archive_name = surrogate.archive_name,
            original_favicon = surrogate.original_favicon,
            original_domain = surrogate.original_domain,
            original_link_status = surrogate.original_link_status,
            surrogate_creation_time = surrogate.creation_time,
            memento_datetime = surrogate.memento_datetime,
            me_title = surrogate.title,
            me_snippet = surrogate.text_snippet,
            server_domain = urlroot
        ), remove_empty_space=True, 
        remove_optional_attribute_quotes=False )   

