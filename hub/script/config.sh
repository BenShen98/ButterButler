#!/bin/bash
. "$( dirname ${BASH_SOURCE[0]} )/_setup.sh"

read -rd '' SCRIPTDOC <<SCRIPTDOC
Usage: $(basename $0) command [target...]

Update(up), download(dn) and delete (rm) config folder.
Note when perform \`rm\`, all files including ssl key/crt
and other service generated data will be removed.

If target not specified, default will be all folder under
${_CFDIR}
SCRIPTDOC

main() {
  # parse variable
  task=$1
  shift
  volList=$@

  if [[ -z $volList ]]; then
    volList=$(find "$_CFDIR" -maxdepth 1 -mindepth 1 -type d -printf '%P ')
  fi

  cd $_WKDIR
  case "$task" in
    up)
      upload
      ;;
    dn)
      download
      ;;
    rm)
      remove
      ;;
    *)
      echo "$SCRIPTDOC"
      ;;
  esac


}

upload(){
  >&2 echo "Upload '$volList' to $_REMOTE"

  local remotecode
  read -rd '' remotecode <<-EOF
  (for config in \$(find ./config -maxdepth 1 -mindepth 1 -type d); do
      echo "Start coping '\$config'"
      vol="\$(balena volume ls --format '{{ .Mountpoint }}' --filter "name=\$(basename \$config)" --filter "dangling=false")"
      if [ \$(echo \$vol | wc -l) -eq 1 ]; then
          # TODO: add some check to avoid override unwanted file
          cp -vrb \$config/* \$vol

      else
          echo "WARNING: mutiple \$vol exist"
      fi
  done) >&2
	EOF


  >&2 echo "$remote"
  # tar nessuary files and send to remote via pipe
  (
      cfdir=$(echo $_CFDIR | sed "s ${_WKDIR}/  g" ) # use space as seperator

      { # combine required files using {}
          echo $_SHDIR/_remote_upload_config.sh | sed "s ${_WKDIR}/  g"; # tar script
          echo $volList | sed "s \([^\ ]*\)\ * $cfdir/\1\n g"; # tar config folders
      }| tar -cf - -C "$_WKDIR" -T -

      if [ $? -ne 0 ]; then
          >&2 echo "ERROR: unable to pack tar"
          exit 1
      fi
  ) | ssh -p 22222 $_REMOTE 'dir=$(mktemp -d); tar -xC $dir; cd $dir; ./script/_remote_upload_config.sh; rm -rf $dir'


}

download(){
  >&2 echo "Download '$volList' from $_REMOTE"
  tarname=config.${_REMOTE}.$(date '+%H-%M-%S').tar

  local remotecode
  read -rd '' remotecode <<-EOF
  targets=""

  for config in $volList; do
    >&2 echo \$config
    target="\$(balena volume ls --format '{{ .Mountpoint }}' --filter "name=\${config}" --filter "dangling=false")"
    targets="\$targets \$target"
  done

  # create tar and send to stdout
  echo \$targets | sed 's/ /\n/g' | tar -cT -
	EOF

  echo "$remotecode" | ssh -p 22222 $_REMOTE "bash -s" > $_DNDIR/$tarname
  >&2 echo "Done, tar at '$tarname'"

}

remove(){
  ssh -p 22222 $_REMOTE "bash -s" <<-EOF
  targets=""
  for config in $volList; do
      target="\$(balena volume ls --format '{{ .Mountpoint }}' --filter "name=\${config}" --filter "dangling=false")"
      targets="\$targets \$target"
  done

  rm -rfv \$targets # remove everything include .folder .file
  mkdir \$targets # recreate root folder
	EOF

}

main "$@"; exit $?