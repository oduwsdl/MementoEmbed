import re
import logging

from bs4 import BeautifulSoup
from readability import Document
from justext import justext, get_stoplist

logger = logging.getLogger(__name__)

p = re.compile(' +')

def get_best_description(htmlcontent):

    description = None

    doc = Document(htmlcontent)

    d = doc.score_paragraphs()

    maxscore = 0

    maxpara = None

    for para in d:

        if d[para]['content_score'] > maxscore:
            maxpara = d[para]['elem']
            maxscore = d[para]['content_score']

    if maxpara is not None:
        allparatext = maxpara.text_content().replace('\n', ' ').replace('\r', ' ').strip()
        description = p.sub(' ', allparatext)
    else:
        paragraphs = justext(htmlcontent, get_stoplist("English"))

        allparatext = ""
        
        for paragraph in paragraphs:

            if not paragraph.is_boilerplate:

                allparatext += " {}".format(paragraph.text)

        if allparatext == "":

            for paragraph in paragraphs:

                allparatext += "{}".format(paragraph.text)
        
        if allparatext != "":
            description = allparatext.strip()
        else:
            # we give up at this point
            description = ""

    return description


def extract_text_snippet(htmlcontent):
    
    soup = BeautifulSoup(htmlcontent, 'html5lib')

    snippet = None

    description_dict = {}

    for metatag in soup.find_all("meta"):

        if metatag.get("property") == "og:description":
            description_dict["og:description"] = metatag.get("content")

        if metatag.get("name") == "og:description":
            description_dict["og:description"] = metatag.get("content")

        if metatag.get("name") == "twitter:description":
            description_dict["twitter:description"] = metatag.get("content")

        if metatag.get("property") == "twitter:description":
            description_dict["twitter:description"] = metatag.get("content")

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

    soup = BeautifulSoup(htmlcontent, 'html5lib')

    title = None

    titledict = {}
    
    for metatag in soup.find_all("meta"):

        if metatag.get("property") == "og:title":
            titledict["og:title"] = metatag.get("content")

        if metatag.get("name") == "og:title":
            titledict["og:title"] = metatag.get("content")

        if metatag.get("name") == "twitter:title":
            titledict["twitter:title"] = metatag.get("content")

        if metatag.get("property") == "twitter:title":
            titledict["twitter:title"] = metatag.get("content")

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
            logger.warning("Could not extract title from input")
            title = ""

    title = " ".join(title.split())

    logger.debug("extracted title of {}".format(title))

    return title