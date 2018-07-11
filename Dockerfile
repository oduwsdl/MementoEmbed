FROM python:3.6-stretch

RUN pip install waitress 
RUN apt-get update && apt-get install redis-server -y

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app

# TODO: this seems like the wrong way to get the git revision
RUN git rev-parse HEAD > revfile.txt && rm -rf .git

COPY sample_appconfig.cfg /etc/mementoembed.cfg

RUN mkdir /app/logs

RUN pip install .

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
