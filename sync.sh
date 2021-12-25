#!/bin/bash

read MAX < lastedit.dat
#echo "Last sync was at $MAX"

for f in *.py *.html *.sh
do
  THIS=$(stat -c %Y $f)
#  echo $f was edited at $THIS
  if [ $THIS -gt $MAX ]
  then
    echo Sending $f
    ampy --port /dev/ttyUSB0 put $f
  fi
done

stat -c %Y *.py | sort -r | head -n 1 > lastedit.dat
