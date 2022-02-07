#!/bin/bash

ampy --port /dev/ttyACM0 get lastedit.dat > lastedit.dat

if [ $? -ne 0 ];
then
    echo "lastedit.dat does not exist, making a new one"
    echo 0 > lastedit.dat
fi

read MAX < lastedit.dat
echo "Last sync for this board was at $MAX"

# increment the version
./bump_version.sh

# send all files to the device
for f in *.py *.html *.sh *.js *.cfg version
do
  THIS=$(stat -c %Y $f)
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
stat -c %Y *.py *.html *.sh *.js *.cfg version | sort -r | head -n 1 > lastedit.dat
ampy --port /dev/ttyACM0 put lastedit.dat

echo "Rebooting..."
echo -e "import machine\r\nmachine.reset()\r\n" | picocom -qrx 1000 -b 115200 /dev/ttyACM0
sleep 1
echo "Ctrl+A,X to exit"
picocom /dev/ttyACM0 -b 115200 -q

