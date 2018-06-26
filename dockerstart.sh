#!/bin/bash

# service redis-server start
redis-server --daemonize yes --save ""
flask run --host 0.0.0.0 --port 5550
