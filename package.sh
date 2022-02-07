#!/bin/bash

# increment the version
./bump_version.sh

# make firmware archive for ota
tar -czf firmware.tar.gz *.py *.html *.sh *.js *.cfg version
V="$(cat version);firmware.tar.gz;30;$(sha256sum firmware.tar.gz | cut -d " " -f 1)"
echo "Firmware latest: $V"
echo $V > latest

# put it in the correct folder and commit the changes

SHORTNAME=$(cat all_starts_here.py | grep ShortName | cut -d "'" -f 4)
echo "Processing project $SHORTNAME"

BASEFOLDER=/stuff/code/wolfen-iot-firmware-archive

mkdir $BASEFOLDER/firmware/${SHORTNAME,,}
cp version $BASEFOLDER/firmware/${SHORTNAME,,}
cp latest $BASEFOLDER/firmware/${SHORTNAME,,}
cp firmware.tar.gz $BASEFOLDER/firmware/${SHORTNAME,,}

cd $BASEFOLDER
git add .
git commit -m "Updated project $SHORTNAME to version $V"
git push