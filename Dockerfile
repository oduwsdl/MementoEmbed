FROM python:3.6-stretch

WORKDIR /app

RUN pip install waitress 

RUN apt-get update && apt-get install redis-server -y

# for thumbnail functionality
# RUN wget -O nodesetup.sh https://deb.nodesource.com/setup_10.x && bash nodesetup.sh && apt-get install -y nodejs libx11-xcb1 libxtst6 libnss3 && npm i puppeteer

RUN apt-get install -y build-essential

COPY requirements.txt /app

RUN pip install -r requirements.txt

RUN wget -O nodesetup.sh https://deb.nodesource.com/setup_10.x && bash nodesetup.sh 

RUN apt-get install -y nodejs
RUN npm i puppeteer
RUN apt-get install -y libx11-xcb1
RUN apt-get install -y libxtst6
RUN apt-get install -y libnss3
RUN apt-get install -y libasound2
RUN apt-get install -y libatk-bridge2.0-0
RUN apt-get install -y libgtk-3-0 

COPY . /app

RUN pip install .

COPY sample_appconfig.cfg /etc/mementoembed.cfg

RUN mkdir /app/logs && mkdir -p /app/thumbnails

EXPOSE 5550



CMD [ "./dockerstart.sh" ]
