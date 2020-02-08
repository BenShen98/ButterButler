FROM benshen98/apline:3.9.5_armv6 as builder

WORKDIR /
RUN apk add python3 python3-dev libffi-dev openssl-dev g++ make
RUN pip3 install --user smbus gpiozero RPi.GPIO paho-mqtt PyYAML

# RUN set PATH=/root/.local/bin:$PATH && \
#     pip3 install smbus gpiozero RPi.GPIO paho-mqtt PyYAML --user

FROM benshen98/apline:3.9.5_armv6

WORKDIR /daemon
RUN apk add --no-cache python3
ENV PATH=/root/.local/bin:$PATH

COPY --from=builder /root/.local /root/.local
COPY modules .
COPY da-config /config

CMD ["python3", "daemon.py", "/config/config.yaml"]
