FROM python:3.6-stretch

RUN pip install waitress 
RUN apt-get update && apt-get install redis-server -y

RUN pip install aiu
RUN pip install bs4
RUN pip install dicttoxml
RUN pip install filelock
RUN pip install flask
RUN pip install html5lib
RUN pip install htmlmin
RUN pip install httpcache
RUN pip install justext
RUN pip install lockfile
RUN pip install Pillow
RUN pip install readability-lxml
RUN pip install redis
RUN pip install requests
RUN pip install requests_cache
RUN pip install tldextract

WORKDIR /app

COPY . /app

RUN pip install .

COPY sample_appconfig.cfg /etc/mementoembed.cfg

RUN mkdir /app/logs

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
