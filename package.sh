#!/bin/bash

# make firmware archive for ota
cat version | perl -ne 'chomp; print join(".", splice(@{[split/\./,$_]}, 0, -1), map {++$_} pop @{[split/\./,$_]}), "\n";' > version_new
rm version
mv version_new version
echo "Version is now:"
tar -czf firmware.tar.gz *.py *.html *.sh *.js *.cfg version
V="$(cat version);firmware.tar.gz;30;$(sha256sum firmware.tar.gz | cut -d " " -f 1)"
echo $V
echo $V > latest

# put it in the correct folder and commit the changes

SHORTNAME=$(cat all_starts_here.py | grep ShortName | cut -d "'" -f 4)
echo "Processing project $SHORTNAME"

BASEFOLDER=/stuff/code/wolfen-iot-firmware-archive

cp version $BASEFOLDER/firmware/${SHORTNAME,,}
cp latest $BASEFOLDER/firmware/${SHORTNAME,,}
cp firmware.tar.gz $BASEFOLDER/firmware/${SHORTNAME,,}

cd $BASEFOLDER
git add .
git commit -m "Updated project $SHORTNAME to version $V"
git push