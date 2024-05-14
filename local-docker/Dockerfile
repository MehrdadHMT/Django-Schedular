FROM hub.hamdocker.ir/library/python:3.11.8-slim

RUN apt-get -y update && apt-get -y upgrade && apt-get -y autoremove
RUN apt-get install -y --no-install-recommends build-essential python3-pip python3-dev python3-psycopg2 postgresql-client graphviz libgraphviz-dev pkg-config cron gettext

RUN mkdir /django
WORKDIR /django
EXPOSE 8000

ADD ./restapi/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

CMD gunicorn -b :8000 django.wsgi