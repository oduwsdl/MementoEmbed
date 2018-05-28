FROM python:3.6.4-stretch

# the flask documentation recommends WSGI server waitress for use
RUN pip install waitress

# TODO: publish archiveit_utilities so that we don't need to do this
RUN git clone https://github.com/shawnmjones/archiveit_utilities.git

RUN cd archiveit_utilities && pip install .

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 5550

ENV FLASK_APP=mementoembed/mementoembed.py

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5550"]

# TODO: actually use waitress
# CMD ["waitress-serve", "--call", "mementoembed:create_app"]