#!/bin/bash
echo "start compiling......"
cd /code
ls
g++ ./code.cpp -o code -std=c++14
rm ./code.cpp