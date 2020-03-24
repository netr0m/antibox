FROM python:alpine

LABEL maintainer="Morten Amundsen <me@mortenamundsen.me>"

ENV USER=abc
ENV PUID=1000
ENV PGID=1000

RUN addgroup -g $PGID $USER
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/tmp/$USER" \
    --ingroup "$USER" \
    --no-create-home \
    --uid "$PUID" \
    "$USER"

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

COPY . /usr/src/app

USER $USER

CMD [ "python", "-u", "./antibox.py" ]
