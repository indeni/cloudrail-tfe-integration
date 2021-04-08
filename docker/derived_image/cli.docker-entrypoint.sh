#!/bin/bash -e
​
if cloudrail $1 --help >/dev/null 2>&1; then
    set -- cloudrail "$@"
elif ! which $1 >/dev/null 2>&1; then
    set -- cloudrail "$@"
fi
​
exec "$@"