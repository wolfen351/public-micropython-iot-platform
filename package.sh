#!/bin/bash

# increment the version
newVersion=6.0.$CI_PIPELINE_ID
echo "Version is now: $newVersion"
echo $newVersion > ./version

# record the current time in lastedit.dat
date +%s > ./lastedit.dat

#make firmware archives for ota
profiles=$(ls -1 ./profiles)

#make a spot for the archives to go
mkdir artifacts

for profile in $profiles
do
    echo "Processing Profile: $profile"
    
    shortName=$(cat "./profiles/$profile" | jq ".shortName" | tr -d '"')
    echo "Short Name: $shortName"

    mkdir -p "./artifacts/$shortName"

    # build up a list of all files
    allFiles=()

    # Root Files
    rootFiles=(*.py *.crt *.key version lastedit.dat)
    allFiles+=("${rootFiles[@]}")

    # System Files: Add all files in board_system directory to the someFiles array
    someFiles=()
    for file in ./board_system/*
    do
        someFiles+=("$file")
    done
    allFiles+=("${someFiles[@]}")
    
    # Iterate through the activeModules array
    for moduleName in $(cat "./profiles/$profile" | jq ".activeModules" | jq -r '.[]' ); 
    do
        # Module Files: Add all files in the modules directory to the someFiles array
        someFiles=()
        for file in $(find ./modules/$moduleName/* -type f)
        do
            someFiles+=("$file")
        done
        allFiles+=("${someFiles[@]}")
    done

    # Prepare package directory
    rm -rf ".package"
    mkdir ".package"

    # copy all files for this profile to the .package directory
    for itemToCopy in "${allFiles[@]}"
    do
        dest="./.package/$(realpath --relative-to=. "$itemToCopy")"
        if [[ ! -d "$(dirname "$dest")" ]]; then
            mkdir -p "$(dirname "$dest")"
        fi
        cp -r "$itemToCopy" "$dest"
    done

    # Profile File
    dest="./.package/profile.json"
    if [ ! -d "$(dirname "$dest")" ]; then
        mkdir -p "$(dirname "$dest")"
    fi
    cp -r "./profiles/$profile" "$dest"

    # Tar up all the files
    cd .package
    vers="$(cat ./version)"
    tar -zcvf ../firmware.tar.gz *

    # Calculate a h256 hash of the files
    sha256sum ../firmware.tar.gz
    h256=$(sha256sum ../firmware.tar.gz | awk '{print $1}')
    size=$(du -k ../firmware.tar.gz | awk '{print $1}') # size in kb
    V="$vers;firmware.tar.gz;$size;$h256"
    echo "Firmware latest: $V"
    echo $V > ./latest

    # put all the files in the artifact folder
    mv ../firmware.tar.gz ../artifacts/$shortName/
    cp version ../artifacts/$shortName/version
    mv version ../artifacts/$shortName/v$vers
    mv latest ../artifacts/$shortName/latest

    cd ..


done

echo "Packages are ready:"
find ./artifacts
