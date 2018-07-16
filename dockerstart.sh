#!/bin/bash

redis-server --daemonize yes --save ""
# waitress-serve --port=5550 --call mementoembed:create_app
export FLASK_APP=mementoembed
flask run --host 0.0.0.0 --port 5550
