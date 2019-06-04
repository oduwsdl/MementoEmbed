FROM python:3.7-stretch

WORKDIR /app

# for production-level WSGI capability
RUN pip install waitress 

# for Redis cachine service
RUN apt-get update && apt-get install redis-server -y

# for thumbnail system dependencies
RUN wget -O nodesetup.sh https://deb.nodesource.com/setup_10.x && bash nodesetup.sh \
    && apt-get install -y build-essential nodejs libx11-xcb1 libxtst6 libnss3 libasound2 libatk-bridge2.0-0 libgtk-3-0

# for thumbnail library dependencies
COPY package-lock.json /app

# install the items in the package-lock.json file
RUN npm install

# install puppeteer and chromium, which doesn't seem to
# work straight from the package-lock.json file
RUN npm install puppeteer

# for Python environment dependencies
# RUN pip install pipenv
# COPY Pipfile.lock Pipfile /app/
# COPY Pipfile /app/
# RUN pipenv install --system

# for Python environment dependencies
COPY requirements.txt /
RUN pip install -r /requirements.txt

# installing the MementoEmbed application
COPY . /app

RUN pip install .

COPY sample_appconfig.cfg /etc/mementoembed.cfg

RUN mkdir /app/logs && mkdir -p /app/thumbnails && mkdir -p /app/imagereels

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
# CMD ["/bin/bash"]
