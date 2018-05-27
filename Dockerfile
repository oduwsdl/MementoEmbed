FROM python:3.6.4-stretch

RUN git clone https://github.com/shawnmjones/archiveit_utilities.git

RUN cd archiveit_utilities && pip install .

WORKDIR /app

ADD . /app

RUN pip install .

EXPOSE 5550

ENV FLASK_APP=mementoembed/mementoembed.py

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5550"]

# CMD ["/bin/bash"]