FROM python:3.6-stretch

RUN pip install waitress && apt-get update && apt-get install redis-server -y

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
