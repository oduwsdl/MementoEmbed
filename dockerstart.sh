#!/bin/bash

redis-server --daemonize yes --save ""
waitress-serve --port=5550 --call mementoembed:create_app
