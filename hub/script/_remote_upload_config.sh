#!/bin/bash

# RUN ON REMOTE, with file structure like below
# tmp <-- ***WE ARE HERE***
# |
# |-- script
# |   `-- _remote_upload_config.sh
# |
# |-- config
# |   |-- mos-config
# |   |   |-- file and folders for config
# |   `-- other config
#


for config in $(find ./config -maxdepth 1 -mindepth 1 -type d); do
    echo "Start coping '$config'"
    vol="$(balena volume ls --format '{{ .Mountpoint }}' --filter "name=$(basename $config)" --filter "dangling=false")"
    if [ $(echo $vol | wc -l) -eq 1 ]; then
        # TODO: add some check to avoid override unwanted file
        cp -vrb $config/* $vol

    else
        echo "WARNING: mutiple $vol exist"
    fi
done