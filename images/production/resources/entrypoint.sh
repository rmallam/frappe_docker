#!/bin/bash
set -e

# if the running uid is not in /etc/passwd, create it
if ! whoami &> /dev/null; then
  if [ -w /etc/passwd ]; then
    echo "${USER_NAME:-frappe}:x:$(id -u):0:${USER_NAME:-frappe} user:${HOME}:/sbin/nologin" >> /etc/passwd
  fi
fi

exec "$@"
