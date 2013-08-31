#!/bin/bash
# name cipv4 cipv6 sipv4 sipv6 routepre

scriptdir=$(dirname $0)
source ${scriptdir}/sudoauto.sh

${cmd_ip} tunnel delete name ${1}
