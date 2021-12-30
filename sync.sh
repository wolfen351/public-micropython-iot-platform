#!/bin/bash

if [ ! -f lastedit.dat ]
then
    echo "lastedit.dat does not exist, making a new one"
    echo 0 > lastedit.dat
fi

read MAX < lastedit.dat
#echo "Last sync was at $MAX"

for f in *.py *.html *.sh *.js
do
  THIS=$(stat -c %Y $f)
#  echo $f was edited at $THIS
  if [ $THIS -gt $MAX ]
  then
    echo Sending $f
    ampy --port /dev/ttyUSB0 put $f
  fi
done

# record the last time a file was edited
stat -c %Y *.py | sort -r | head -n 1 > lastedit.dat
