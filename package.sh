#!/bin/bash

# increment the version
raw=$(cat ./version)
v=$(echo $raw | awk -F. '{ printf("%d.%d.%d",$1,$2,$3); }')
nv=$(echo $v | awk -F. '{ printf("%d.%d.%d.%d",$1,$2,$3+1,0); }')
newVersion=${nv%.*}
echo "Version is now: $newVersion"
echo $newVersion > ./version

# record the current time in lastedit.dat
date +%s > ./lastedit.dat

#make firmware archives for ota
profiles=$(ls -1 ./profiles)

for profile in $profiles
do
    echo "Processing Profile: $profile"

    shortName=$(cat "./profiles/$profile" | jq ".shortName") 
    activeModules=$(cat "./profiles/$profile" | jq ".activeModules") 
    echo "Flashing Profile: " $shortName
    echo "Active Modules: " $activeModules

    # build up a list of all files
    allFiles=()

    # Root Files
    rootFiles=($(ls *.py *.crt *.key version lastedit.dat))
    allFiles+=($rootFiles)

    # Write all files to the console
    echo "All Files: " 
    # Iterate the loop to read and print each array element
    for value in "${allFiles[@]}"
    do
        echo $value
    done

done



