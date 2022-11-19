#!/bin/bash

echo_time() {
    date +"%Y-%m-%d %H:%M:%S.%6N INFO [sample_workload.sh]: $*"
}

while read line ; do
    echo_time "${line}"
done

