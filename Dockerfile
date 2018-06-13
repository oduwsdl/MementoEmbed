FROM python:3.6-stretch

# the flask documentation recommends WSGI server waitress for use
RUN pip install waitress

# TODO: publish archiveit_utilities so that we don't need to do this
RUN git clone https://github.com/shawnmjones/archiveit_utilities.git /tmp/archiveit_utilities \
    && pip install /tmp/archiveit_utilities \
    && rm -rf /tmp/archiveit_utilities

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 5550

ENV FLASK_APP=mementoembed

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5550"]

# TODO: actually use waitress
# CMD ["waitress-serve", "--call", "mementoembed:create_app"]
