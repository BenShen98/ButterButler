#!/bin/bash
. "$( dirname ${BASH_SOURCE[0]} )/_setup.sh"

# USAGE: run script to regenerate all keys
# Provide extra arguement for exported certificate (externalList)


dockerList="ha mos"
externalList=$@

read -rd '' remote_code<<EOF
    # function
    function getcrt {
        # take space seprated word, first word is CN, rest if SAN
        local v3_ext

        read -rd '' v3_ext <<-EOF2
        authorityKeyIdentifier=keyid,issuer
        basicConstraints=CA:FALSE
        keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
        subjectAltName = @alt_names

        [alt_names]
		EOF2

        # parse args, genearte alt_names
        cn=\$1
        sans=\$(for (( i=1; i<=\${#@}; i++ )); do
            echo "DNS.\${i} = \${!i}" # !1 is indirect reference, get ith variable
        done)

        # creat keys,crts
        openssl req -nodes -newkey rsa:2048 -keyout \${cn}.key -out \${cn}.csr -subj "/CN=\${cn}"
        if [[ \${#@} > 1 ]]; then
            openssl x509 -req -in \${cn}.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out \${cn}.crt -days 360 \
                -extfile <(echo "\$v3_ext"\$'\n'"\$sans" )
        else
            openssl x509 -req -in \${cn}.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out \${cn}.crt -days 360
        fi
        rm \${cn}.csr

        # openssl x509 -in \${cn}.crt -text -noout
    }

    # boiler plate
    dir=\$(mktemp -d)
    cd \$dir
    error=0

    # ca self sign
    openssl req -nodes -new -x509 -keyout ca.key -out ca.crt -subj "/CN=CA" -days 1826

    # gen host certs
    for config in $dockerList; do

        # gen certificate
        getcrt \$config eatchickenhub.ddns.net
        vol="\$(balena volume ls --format '{{ .Mountpoint }}/' --filter "name=\$(basename \$config)-config" --filter "dangling=false")"

        # move certificate
        if [ \$(echo \$vol | wc -l) -eq 1 ]; then
            cp ./{ca.crt,\${config}.crt,\${config}.key} \$vol
        else
            >&2 echo "WARNING: mutiple \$vol exist"
            error=\$((\$error+1))
        fi

    done

    # gen external certs
    exernalCrts=''
    for config in $externalList; do
        getcrt \$config
        exernalCrts="\$exernalCrts \$config.crt \$config.key"
    done


    if [ $_DEV -eq 1 ]; then
        # send certificate back if under debug mode
        getcrt $(hostname)
        tar -c ./ # tar file to stdout

    elif [[ ${#@} > 0 ]]; then
        # send externalList back if required
        echo ca.crt \$exernalCrts | sed 's/ /\n/g' | tar -c -T -

    fi

    # clean up
    rm -rf \$dir

    if [ \$error -eq 0 ]; then
        >&2 echo "key generated without error"
    else
        >&2 echo "\$error error generated"
        exit \$error
    fi
EOF


if [ $_DEV -eq 1 ]; then
    zname="crt.${_REMOTE}.$(date '+%H-%M-%S').tar"
    >&2 echo "debug mode: export crt to '$zname'"
    echo "$remote_code" | ssh -p 22222 $_REMOTE "bash -s" > "${_DNDIR}/${zname}"
elif [[ ${#@} > 0 ]]; then
    zname="exportcrt.${_REMOTE}.$(date '+%H-%M-%S').tar"
    >&2 echo "export attional crt ${externalList} to '$zname'"
    echo "$remote_code" | ssh -p 22222 $_REMOTE "bash -s" > "${_DNDIR}/$zname"
else
    echo "$remote_code" | ssh -p 22222 $_REMOTE "bash -s"
fi

