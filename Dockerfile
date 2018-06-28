FROM python:3.6-stretch

RUN pip install waitress

RUN apt-get update && apt-get install redis-server -y

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 5550

ENV FLASK_APP=mementoembed

CMD [ "./dockerstart.sh" ] 