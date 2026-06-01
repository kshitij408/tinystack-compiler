#!/bin/bash

source venv/bin/activate

python3 src/main.py "$1"

if [ $? -ne 0 ]; then
    exit 1
fi

clang output/output_optimized.ll -o output/program

if [ $? -ne 0 ]; then
    exit 1
fi

./output/program
