#!/bin/bash

# variable setup
_REMOTE=root@eatchickenhub.ddns.net
_WKDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
_SHDIR=$_WKDIR/script
_CFDIR=$_WKDIR/config
_DNDIR=$_WKDIR/.backup

# configurable debugging variable, can be alternated via env
>&2 echo "_DEV is set to ${_DEV:=0}"

# create dir
[ -d "$_DNDIR" ] || mkdir "$_DNDIR"