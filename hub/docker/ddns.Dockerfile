# build stage 0
FROM benshen98/apline:3.9.5_armv6 AS builder
WORKDIR /build

RUN apk add make gcc libc-dev wget

RUN wget https://www.noip.com/client/linux/noip-duc-linux.tar.gz
RUN tar xzf noip-duc-linux.tar.gz && cd noip-2.1.9-1 && make


# final stage 1
FROM benshen98/apline:3.9.5_armv6
WORKDIR /

RUN apk add --no-cache curl &&\
    mkdir -p /usr/local/etc/

COPY --from=builder /build/noip-2.1.9-1/noip2 .
COPY ddns.config /usr/local/etc/no-ip2.conf

CMD /noip2 -i $(curl -X GET --header "Content-Type:application/json" \
    "$BALENA_SUPERVISOR_ADDRESS/v1/device?apikey=$BALENA_SUPERVISOR_API_KEY" \
	| sed 's/.*"ip_address":"\([0-9.]*\).*/\1/g')