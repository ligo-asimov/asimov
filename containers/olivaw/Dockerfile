# This file defines the docker image for running olivaw.

FROM python:3.7

#WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install .

CMD [ "olivaw" ]

