FROM python:3.6-stretch

WORKDIR /app

# for production-level WSGI capability
RUN pip install waitress 

# for Redis cachine service
RUN apt-get update && apt-get install redis-server -y

# for thumbnail functionality
RUN wget -O nodesetup.sh https://deb.nodesource.com/setup_10.x && bash nodesetup.sh \
    && apt-get install -y build-essential nodejs libx11-xcb1 libxtst6 libnss3 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    && npm i puppeteer

COPY requirements.txt /app

# TODO: find a more efficient way to handle this - requirements are in setup.py, too
RUN pip install -r requirements.txt

COPY . /app

RUN pip install .

COPY sample_appconfig.cfg /etc/mementoembed.cfg

RUN mkdir /app/logs && mkdir -p /app/thumbnails

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
