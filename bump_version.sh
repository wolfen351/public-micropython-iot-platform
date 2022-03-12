#!/bin/bash

# increment the version 
cat version | perl -ne 'chomp; print join(".", splice(@{[split/\./,$_]}, 0, -1), map {++$_} pop @{[split/\./,$_]}), "\n";' > version_new
rm version
mv version_new version
echo "Version is now:"
cat version

