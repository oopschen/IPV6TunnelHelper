#!/bin/bash
# name cipv4 cipv6 sipv4 sipv6 routepre
scriptdir=$(dirname $0)
source ${scriptdir}/sudoauto.sh

${cmd_ip} tunnel add ${1} mode sit remote ${4} local ${2} ttl 255 && \
${cmd_ip} link set dev ${1} up txqueuelen 3000 && \
${cmd_ip} addr add ${3}/64 dev ${1} && \
${cmd_ip} route add ${6} dev ${1}
