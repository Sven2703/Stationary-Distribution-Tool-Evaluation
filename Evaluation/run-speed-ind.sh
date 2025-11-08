#!/bin/bash

echo "Switching working directory"

# cd to the directory where the script lies in
cd "$( dirname "${BASH_SOURCE[0]}" )"
pwd

echo "Starting benchmarking."
date
python3 ../scripts/run.py -t stationary -r results -f speed-ind.json


echo "Finished benchmarking."
date
