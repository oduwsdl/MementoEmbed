FROM python:3.6-stretch

RUN pip install waitress 
RUN apt-get update && apt-get install redis-server -y

WORKDIR /app

COPY . /app

RUN pip install .

COPY sample_appconfig.json /etc/mementoembed.json

RUN mkdir /app/logs

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
