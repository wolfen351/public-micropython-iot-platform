#!/bin/bash

ampy --port /dev/ttyACM0 get lastedit.dat > lastedit.dat

if [ $? -ne 0 ];
then
    echo "lastedit.dat does not exist, making a new one"
    echo 0 > lastedit.dat
fi

read MAX < lastedit.dat
echo "Last sync for this board was at $MAX"

for f in *.py *.html *.sh *.js
do
  THIS=$(stat -c %Y $f)
#  echo $f was edited at $THIS
  if [ $THIS -gt $MAX ]
  then
    echo Sending $f
    ampy --port /dev/ttyACM0 put $f
    if [ $? -ne 0 ]; then
        echo "Failed."
        exit 3
    fi
  fi
done

# record the last time a file was edited
stat -c %Y *.py | sort -r | head -n 1 > lastedit.dat
ampy --port /dev/ttyACM0 put lastedit.dat

echo "Rebooting..."
echo -e "import machine\r\nmachine.reset()\r\n" | picocom -qrx 1000 -b 115200 /dev/ttyACM0
sleep 1
echo "Ctrl+A,X to exit"
picocom /dev/ttyACM0 -b 115200 -q

