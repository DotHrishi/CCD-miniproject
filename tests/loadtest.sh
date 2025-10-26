#!/bin/bash
# Usage: ./loadtest.sh <num> <file> <host>
NUM=${1:-50}
FILE=${2:-tests/sample_files/sample1mb.bin}
HOST=${3:-http://localhost:8080}

for i in $(seq 1 $NUM); do
  curl -s -F "file=@${FILE}" ${HOST}/upload > /dev/null &
done
wait
echo "done"
