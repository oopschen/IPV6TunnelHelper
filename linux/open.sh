#!/bin/bash
# name cipv4 cipv6 sipv4 sipv6 routepre
ip tunnel add name ${1} mode sit remote ${4} local ${2} ttl 128 && \
ip link set dev ${1} up mtu 1280 && \
ip addr add ${3}/64 dev ${1} && \
ip route add ${6} via ${5} dev ${1}
