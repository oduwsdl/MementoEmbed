import re
import logging

from bs4 import BeautifulSoup
from readability import Document
from justext import justext, get_stoplist

module_logger = logging.getLogger('mementoembed.textprocessing')

p = re.compile(' +')

class TextProcessingError(Exception):

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception

def get_best_description(htmlcontent):

    description = None

    try:
        doc = Document(htmlcontent)
        d = doc.score_paragraphs()
    except Exception as e:
        raise TextProcessingError(
            "failed to process document using readability",
            original_exception=e)

    maxscore = 0

    maxpara = None

    for para in d:

        try:
            if d[para]['content_score'] > maxscore:
                maxpara = d[para]['elem']
                maxscore = d[para]['content_score']

        except Exception as e:
            raise TextProcessingError(
                "failed to process document using readability",
                original_exception=e)

    if maxpara is not None:
        allparatext = maxpara.text_content().replace('\n', ' ').replace('\r', ' ').strip()
        description = p.sub(' ', allparatext)
    else:

        try:
            paragraphs = justext(htmlcontent, get_stoplist("English"))
        except Exception as e:
            raise TextProcessingError(
                "failed to process document using justext",
                original_exception=e)

        allparatext = ""
        
        for paragraph in paragraphs:

            try:
                if not paragraph.is_boilerplate:

                    allparatext += " {}".format(paragraph.text)
            except Exception as e:
                raise TextProcessingError(
                    "failed to process document using justext",
                    original_exception=e)

        if allparatext == "":

            for paragraph in paragraphs:

                try:
                    allparatext += "{}".format(paragraph.text)
                except Exception as e:
                    raise TextProcessingError(
                        "failed to process document using justext",
                        original_exception=e)
        
        if allparatext != "":
            description = allparatext.strip()
        else:
            # we give up at this point
            description = ""

    return description


def extract_text_snippet(htmlcontent):
    
    try:
        soup = BeautifulSoup(htmlcontent, 'html5lib')
    except Exception as e:
        raise TextProcessingError(
            "failed to open document using BeautifulSoup",
            original_exception=e)

    snippet = None

    description_dict = {}

    try:
        for metatag in soup.find_all("meta"):

            if metatag.get("property") == "og:description":
                description_dict["og:description"] = metatag.get("content")

            if metatag.get("name") == "og:description":
                description_dict["og:description"] = metatag.get("content")

            if metatag.get("name") == "twitter:description":
                description_dict["twitter:description"] = metatag.get("content")

            if metatag.get("property") == "twitter:description":
                description_dict["twitter:description"] = metatag.get("content")
    except Exception as e:
        raise TextProcessingError(
            "failed to process document using BeautifulSoup",
            original_exception=e)

    # 1. favor title from the OGP metadata
    if "og:description" in description_dict:

        snippet = description_dict["og:description"]

        if len(snippet) == 0:
            snippet = None

    # 2. favor title from the twitter metadata
    if snippet is None:

        if "twitter:description" in description_dict:
            snippet = description_dict["twitter:description"]

            if len(snippet) == 0:
                snippet = None

    # 3. use readability or justext
    if snippet is None:
        snippet = get_best_description(htmlcontent)

    return snippet[0:197]


def extract_title(htmlcontent):

    module_logger.debug("attempting to extract title from input")

    try:
        soup = BeautifulSoup(htmlcontent, 'html5lib')
    except Exception as e:
        raise TextProcessingError(
            "failed to open document using BeautifulSoup",
            original_exception=e)

    title = None

    titledict = {}
    
    try:
        for metatag in soup.find_all("meta"):

            if metatag.get("property") == "og:title":
                titledict["og:title"] = metatag.get("content")

            if metatag.get("name") == "og:title":
                titledict["og:title"] = metatag.get("content")

            if metatag.get("name") == "twitter:title":
                titledict["twitter:title"] = metatag.get("content")

            if metatag.get("property") == "twitter:title":
                titledict["twitter:title"] = metatag.get("content")

    except Exception as e:
        raise TextProcessingError(
            "failed to process document using BeautifulSoup",
            original_exception=e)

    # 1. favor title from the OGP metadata
    if "og:title" in titledict:
        title = titledict["og:title"]

    # 2. favor title from the twitter metadata
    if title is None:

        if "twitter:title" in titledict:
            title = titledict["twitter:title"]

    if title is None:
        # 3. extract the title from the title tag

        try:
            title = soup.title.text
        except AttributeError:
            module_logger.warning("Could not extract title from input")
            title = ""

    title = " ".join(title.split())

    module_logger.debug("extracted title of {}".format(title))

    return title