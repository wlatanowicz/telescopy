#!/bin/sh

set -x

uPYTHON=/micropython/ports/unix/micropython
COMPILER=/micropython/mpy-cross/mpy-cross

server() {
    $uPYTHON /app/dome.py
}

compile() {
    python /bin/read_manifesto.py /app/manifesto.json compile | xargs -t -n1 $COMPILER
}

upload() {
    python /bin/read_manifesto.py /app/manifesto.json publish | xargs -t -n 1 -I @ python /bin/webrepl_cli.py -p $UC_PASSWORD @ $UC_ADDRESS:@
}

start() {
    for cmd in $@
    do
       ${cmd} || exit $?
    done
}

"$@" || exit $?
