#!/bin/bash

# Check if the search word and UUID are provided as command-line arguments
if [ -z "$1" ] || [ -z "$3" ]; then
    exit 1
fi

# Get the search word and UUID from the command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -n) search_word="$2"; shift ;;
        --id) uuid="$2"; shift ;;
        *) exit 1 ;;
    esac
    shift
done

# Get a list of running containers with the specified word in the name
containers=$(docker ps -a --format "{{.Names}}" | grep "$search_word")

# Restart the containers
for container in $containers; do
    docker restart "$container" > /dev/null 2>&1
done

# Perform the curl health check
curl -m 10 --retry 5 "https://healthchecks.cr.lvtd.dev/ping/$uuid" > /dev/null 2>&1
