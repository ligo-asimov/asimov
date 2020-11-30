# This file defines the docker image for running olivaw.

FROM python:3.7

#WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install git+https://git.ligo.org/daniel-williams/supervisor.git

CMD [ "olivaw" ]

