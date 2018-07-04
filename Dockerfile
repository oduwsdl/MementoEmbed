FROM python:3.6-stretch

RUN pip install waitress 
RUN apt-get update && apt-get install redis-server -y

WORKDIR /app

COPY . /app

# TODO: this seems like the wrong way to get the git revision
RUN git rev-parse HEAD > revfile.txt && rm -rf .git

COPY sample_appconfig.json /etc/mementoembed.json

RUN mkdir /app/logs

RUN pip install .

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
