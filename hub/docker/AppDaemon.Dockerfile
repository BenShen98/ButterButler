FROM balenalib/raspberrypi3-alpine-python:3

VOLUME /conf

RUN apk add --no-cache  && \
    apk add --no-cache --virtual=build-dep gcc musl-dev python3-dev libffi-dev && \
    pip3 install appdaemon && \
    apk del build-dep

CMD test -n "$TOKEN" && echo "token: ${TOKEN}" > /conf/secrets.yaml; \
    appdaemon -c /conf
