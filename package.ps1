Import-Module .\serial-toys.psm1

# increment the version
Step-Version

# make firmware archive for ota
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, version, *.crt, *.key
tar -zcf firmware.tar.gz $files

$vers = Get-Content -Path .\version
$h256 = (Get-FileHash .\firmware.tar.gz).Hash.ToLower()
$V="$vers;firmware.tar.gz;30;$h256"
Write-Output "Firmware latest: $V"
Write-Output $V | Out-File -encoding ascii latest

# put it in the correct folder and commit the changes
$ash = Get-Content -Path .\all_starts_here.py
$SHORTNAME = $ash[2].Split("'")[3].ToLower()
Write-Output "Processing project $SHORTNAME"

$BASEFOLDER="D:\stuff\code\wolfen-iot-firmware-archive"

# prepare git
Push-Location $BASEFOLDER
git fetch --all
git reset --hard origin/master
Pop-Location

if(!(Test-Path -path "$BASEFOLDER/firmware/$SHORTNAME"))  
{  
    New-Item -ItemType directory -Path $BASEFOLDER/firmware/$SHORTNAME
}

Copy-Item version $BASEFOLDER/firmware/$SHORTNAME
Copy-Item latest $BASEFOLDER/firmware/$SHORTNAME
Copy-Item firmware.tar.gz $BASEFOLDER/firmware/$SHORTNAME

Push-Location $BASEFOLDER
git add .
git commit -m "Updated project $SHORTNAME to version $V"
git push
Pop-Location