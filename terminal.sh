#!/bin/bash

while :; 
do
    picocom /dev/ttyACM0 -b 115200 -q
done;

