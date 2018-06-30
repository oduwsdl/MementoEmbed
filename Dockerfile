FROM python:3.6-stretch

RUN pip install waitress && apt-get update && apt-get install redis-server -y

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 5550

# TODO: this is an irritation kludge, setup.py needs to be modified
RUN ln -s /app/mementoembed/templates /usr/local/lib/python3.6/site-packages/mementoembed/templates && \
    ln -s /app/mementoembed/static /usr/local/lib/python3.6/site-packages/mementoembed/static && \
    ln -s /app/mementoembed/config /usr/local/lib/python3.6/site-packages/mementoembed/config

CMD [ "./dockerstart.sh" ]
