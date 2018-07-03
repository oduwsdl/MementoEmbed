FROM python:3.6-stretch

RUN pip install waitress 
RUN apt-get update && apt-get install redis-server -y

WORKDIR /app

ADD . /app

RUN pip install .

# TODO: replace this workaround required to install the templates for MementoEmbed to work
# RUN ln -s /app/mementoembed/templates /usr/local/lib/python3.6/site-packages/mementoembed/templates && \
#     ln -s /app/mementoembed/static /usr/local/lib/python3.6/site-packages/mementoembed/static

RUN cp docker_appconfig.json /etc/mementoembed.json

RUN mkdir /app/logs

EXPOSE 5550

CMD [ "./dockerstart.sh" ]
