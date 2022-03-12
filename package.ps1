# increment the version
.\bump_version.ps1

# make firmware archive for ota
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, version, *.crt, *.key
tar -zcf firmware.tar.gz $files

$vers = Get-Content -Path .\version -Raw
$h256 = Get-FileHash .\firmware.tar.gz
$V="${$vers};firmware.tar.gz;30;${$h256}"
Write-Output "Firmware latest: $V"
Write-Output $V > latest

echo 1

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