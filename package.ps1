Import-Module .\serial-toys.psm1

# increment the version
Step-Version

# make firmware archives for ota
$profiles = Get-ChildItem ".\profiles\"

# record the last time a file was edited
$MAXEDITTIME = [math]::Round($MAXEDITTIME)
Write-Output $MAXEDITTIME | Out-File -Encoding ascii .\lastedit.dat

foreach ($profile in $profiles){
    Write-Host "Processing Profile: $($profile.Name)"

    $activeProfile = Get-Content -Raw $profile | ConvertFrom-Json 
    # load active modules
    $activeModules = $activeProfile.activeModules
    Write-Host "Flashing Profile: $($activeProfile.shortName)"
    Write-Host "Active Modules: $activeModules"

    # build up a list of all files
    $allFiles = @()

    # Root Files
    $rootFiles = Get-ChildItem *.py,*.crt,*.cfg,*.key,version,lastedit.dat
    $allFiles +=  $rootFiles

    # System Files
    $someFiles = Get-ChildItem board_system
    $allFiles +=  $someFiles

    # Module Files
    Foreach ($moduleName in $activeModules) {
        $someFiles = Get-ChildItem .\modules\$moduleName -recurse
        $allFiles +=  $someFiles
    }

    # Prepare package directory
    rmdir -recurse ".package" 2> $null
    mkdir '.package' > $null 2> $null

    # copy all files for this profile to the .package directory
    foreach ($itemToCopy in $allFiles)
    {
        $dest = "$PSScriptRoot\.package\$($itemToCopy | Resolve-Path -Relative)"
        $dest = $dest.replace("\.\", "\")
        Invoke-Expression "xcopy $itemToCopy $dest /Y /-I"
    }

    # Profile File
    $dest = "$PSScriptRoot\.package\profile.json"
    Invoke-Expression "xcopy .\profiles\$($profile.Name) $dest /Y /-I"

    # Tar up all the files
    Push-Location .package
    tar -zcvf ..\firmware.tar.gz *
    Pop-Location

    # Calculate a h256 hash of the files
    $vers = Get-Content -Path .\version
    $h256 = (Get-FileHash .\firmware.tar.gz).Hash.ToLower()
    $V="$vers;firmware.tar.gz;30;$h256"
    Write-Output "Firmware latest: $V"
    Write-Output $V | Out-File -encoding ascii latest

    # Copy it to the package directory
    $BASEFOLDER="D:\stuff\code\wolfen-iot-firmware-archive"

    # prepare git
    Push-Location $BASEFOLDER
    git fetch --all
    git reset --hard origin/master
    Pop-Location

    if(!(Test-Path -path "$BASEFOLDER/firmware/$($activeProfile.shortName)"))  
    {  
        New-Item -ItemType directory -Path $BASEFOLDER/firmware/$($activeProfile.shortName)
    }

    Copy-Item version $BASEFOLDER/firmware/$($activeProfile.shortName)
    Copy-Item latest $BASEFOLDER/firmware/$($activeProfile.shortName)
    Copy-Item firmware.tar.gz $BASEFOLDER/firmware/$($activeProfile.shortName)

    Push-Location $BASEFOLDER
    git add .
    git commit -m "Updated project $($activeProfile.shortName) to version $V"
    git push
    Pop-Location

    # CLEANUP
    rmdir -recurse ".package" 2> $null
}

# TAG GIT
git add .\version
git commit -m "Packaged version: $(cat version)"
git tag "$(cat version)"
git push --tags