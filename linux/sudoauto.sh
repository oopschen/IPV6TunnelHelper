#!/bin/bash
which sudo >> /dev/null 2>&1
if [ 0 == $? ]; then
  cmd_ip="sudo ip"
else
  cmd_ip="ip"
fi
