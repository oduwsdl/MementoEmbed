import re
import logging

from bs4 import BeautifulSoup
from readability import Document
from justext import justext, get_stoplist
from summa.summarizer import _clean_text_by_sentences, _build_graph, \
    _set_graph_edge_weights, _remove_unreachable_nodes, _pagerank, \
    _add_scores_to_sentences

module_logger = logging.getLogger('mementoembed.textprocessing')

p = re.compile(' +')

class TextProcessingError(Exception):

    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception

class TitleExtractionError(TextProcessingError):
    pass

class SnippetGenerationError(TextProcessingError):
    pass

def get_text_without_boilerplate(htmlcontent):

    # htmlcontent = htmlcontent.replace('\n', ' ')

    try:
        paragraphs = justext(htmlcontent, get_stoplist("English"))
    except Exception as e:
        raise SnippetGenerationError(
            "failed to process document using justext",
            original_exception=e)

    allparatext = ""
    
    for paragraph in paragraphs:

        try:
            if not paragraph.is_boilerplate:
                allparatext += " {}".format(paragraph.text)
        except Exception as e:
            raise SnippetGenerationError(
                "failed to process document using justext",
                original_exception=e)

    if allparatext == "":

        for paragraph in paragraphs:

            try:
                allparatext += "{}".format(paragraph.text)
            except Exception as e:
                raise SnippetGenerationError(
                    "failed to process document using justext",
                    original_exception=e)

    return allparatext   

def get_sentence_scores_by_textrank(htmlcontent):

    text = get_text_without_boilerplate(htmlcontent)

    # the following code was adapted from the source code 
    # of the summa summarizer function by Federico Barrios et al.
    # ref: https://pypi.org/project/summa/

    # Gets a list of processed sentences.
    sentences = _clean_text_by_sentences(text, "english", None)
    # TODO: update the language so that it is automatically determined

    # Creates the graph and calculates the similarity coefficient for every pair of nodes.
    graph = _build_graph([sentence.token for sentence in sentences])
    _set_graph_edge_weights(graph)

    # Remove all nodes with all edges weights equal to zero.
    _remove_unreachable_nodes(graph)

    # PageRank cannot be run in an empty graph.
    if len(graph.nodes()) == 0:
        return []

    # Ranks the tokens using the PageRank algorithm. Returns dict of sentence -> score
    pagerank_scores = _pagerank(graph)

    # Adds the summa scores to the sentence objects.
    _add_scores_to_sentences(sentences, pagerank_scores)

    # done with adapated code

    scored_sentences = []

    for sentence in sentences:
        scored_sentences.append(
            (sentence.score, sentence.text)
        )

    return sorted(scored_sentences, reverse=True)

def get_section_scores_by_readability(htmlcontent):

    try:
        doc = Document(htmlcontent)
        d = doc.score_paragraphs()
    except Exception as e:
        raise SnippetGenerationError(
            "failed to process document using readability",
            original_exception=e)

    scored_elements = []

    for para in d:

        try:
            score = d[para]['content_score']
            text = d[para]['elem'].text_content().replace('\n', ' ').replace('\r', ' ').strip()

            scored_elements.append( (score, text) )

        except Exception as e:
            raise SnippetGenerationError(
                "failed to process document using readability",
                original_exception=e)

    return sorted(scored_elements, reverse=True)

def get_sentence_scores_by_readability_and_textrank(htmlcontent):

    scored_elements = get_section_scores_by_readability(htmlcontent)

    complex_scores = []

    for paragraph in sorted(scored_elements, reverse=True):

        para_score = paragraph[0]
        text = paragraph[1]

        # module_logger.debug("paragraph text: {}".format(text))

        scored_sentences = get_sentence_scores_by_textrank(text)

        # module_logger.debug("scored_sentences: {}".format(scored_sentences))

        if len(scored_sentences) != 0:

            for sentence in scored_sentences:
                # module_logger.debug("looking at sentence {}".format(sentence))
                complex_scores.append(
                    (para_score, sentence[0], sentence[1])
                )
                # module_logger.debug("complex_scores is now {}".format(complex_scores))

    # module_logger.debug("returning: {}".format(complex_scores))

    return sorted(complex_scores, reverse=True)

def get_sentence_scores_by_readability_and_lede3(htmlcontent):

    scored_elements = get_section_scores_by_readability(htmlcontent)

    complex_scores = []

    sentences_seen = []

    for paragraph in sorted(scored_elements, reverse=True):

        para_score = paragraph[0]
        text = paragraph[1]

        module_logger.debug("paragraph text: {}".format(text))

        sentences = _clean_text_by_sentences(text, "english", None)

        for sentence in sentences:

            if sentence.text not in sentences_seen:
                complex_scores.append( (para_score, sentence.index, sentence.text) )
                sentences_seen.append(sentence.text)

    # module_logger.debug("returning: {}".format(complex_scores))

    return complex_scores

def get_best_description(htmlcontent):

    description = None

    try:
        doc = Document(htmlcontent)
        d = doc.score_paragraphs()
    except Exception as e:
        raise SnippetGenerationError(
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
            raise SnippetGenerationError(
                "failed to process document using readability",
                original_exception=e)

    if maxpara is not None:
        allparatext = maxpara.text_content().replace('\n', ' ').replace('\r', ' ').strip()
        description = p.sub(' ', allparatext)
    else:

        try:
            paragraphs = justext(htmlcontent, get_stoplist("English"))
        except Exception as e:
            raise SnippetGenerationError(
                "failed to process document using justext",
                original_exception=e)

        allparatext = ""
        
        for paragraph in paragraphs:

            try:
                if not paragraph.is_boilerplate:

                    allparatext += " {}".format(paragraph.text)
            except Exception as e:
                raise SnippetGenerationError(
                    "failed to process document using justext",
                    original_exception=e)

        if allparatext == "":

            for paragraph in paragraphs:

                try:
                    allparatext += "{}".format(paragraph.text)
                except Exception as e:
                    raise SnippetGenerationError(
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
        raise SnippetGenerationError(
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
        raise SnippetGenerationError(
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
        raise TitleExtractionError(
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
        raise TitleExtractionError(
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
