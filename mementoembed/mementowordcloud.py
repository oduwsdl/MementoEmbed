import logging
import io

from wordcloud import WordCloud

from .mementoresource import memento_resource_factory
from .textprocessing import get_text_without_boilerplate

class MementoWordCloudGenerationError(Exception):
    pass

class MementoWordCloud:

    def __init__(self, user_agent, httpcache):

        self.user_agent = user_agent
        self.httpcache = httpcache

    def generate_wordcloud(self, urim, colormap="inferno", background_color="white"):

        memento = memento_resource_factory(urim, self.httpcache)

        text = get_text_without_boilerplate(memento.raw_content)

        wordcloud = WordCloud(background_color=background_color, colormap=colormap)
        
        wordcloud.generate(text)

        im = wordcloud.to_image()

        output_bytes = io.BytesIO()

        im.save(output_bytes, format='PNG')

        return output_bytes.getvalue()

    def generate_words_and_scores(self, urim):

        memento = memento_resource_factory(urim, self.httpcache)

        text = get_text_without_boilerplate(memento.raw_content)

        wordcloud = WordCloud()

        wordcloud.generate(text)

        return wordcloud.words_
