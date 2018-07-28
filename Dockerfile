FROM python:3.6-stretch

WORKDIR /app

# for production-level WSGI capability
RUN pip install waitress 

# for Redis cachine service
RUN apt-get update && apt-get install redis-server -y

# for thumbnail system dependencies
RUN wget -O nodesetup.sh https://deb.nodesource.com/setup_10.x && bash nodesetup.sh \
    && apt-get install -y build-essential nodejs libx11-xcb1 libxtst6 libnss3 libasound2 libatk-bridge2.0-0 libgtk-3-0

# for Python environment dependencies
COPY requirements.txt /app

RUN pip install -r requirements.txt

# for thumbnail library dependencies
COPY package-lock.json /app

# install the items in the package-lock.json file
RUN npm install

# install puppeteer and chromium, which doesn't seem to
# work straight from the package-lock.json file
RUN npm install puppeteer

# installing the MementoEmbed application
COPY . /app

RUN pip install .

COPY sample_appconfig.cfg /etc/mementoembed.cfg

RUN mkdir /app/logs && mkdir -p /app/thumbnails

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
