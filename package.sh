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

