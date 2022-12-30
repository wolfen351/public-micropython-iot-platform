param($profileName) 

# Globals
Import-Module .\serial-toys.psm1

# Load the profile
try {

    if ($null -eq $profileName) {
        throw "Profile Name Required!"
    }
    
    $activeProfile = Get-Content -Raw ".\profiles\$profileName.json" | ConvertFrom-Json 
    # load active modules
    $activeModules = $activeProfile.active_modules
    Write-Host "Flashing Profile: $profileName"
    Write-Host "Active Modules: $activeModules"
}
catch {
    Write-Error "Could not load profile from file .\profiles\$profileName.json"
    Write-Error "Please specify the profile name as a parameter to this script" -ErrorAction Stop
}

# record the last time a file was edited
$MAXEDITTIME = [math]::Round($MAXEDITTIME)
Write-Output $MAXEDITTIME | Out-File -Encoding ascii .\lastedit.dat

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

rmdir -recurse "Deploy" 2> $null
mkdir 'Deploy' > $null 2> $null
foreach ($itemToCopy in $allFiles)
{
    $dest = "$PSScriptRoot\Deploy\$($itemToCopy | Resolve-Path -Relative)"
    $dest = $dest.replace("\.\", "\")
    echo "xcopy $itemToCopy $dest /E /Y /-I"
    Invoke-Expression "xcopy $itemToCopy $dest /Y /-I"
}

# Profile File
$dest = "$PSScriptRoot\Deploy\profile.json"
Invoke-Expression "xcopy .\profiles\$profileName.json $dest /Y /-I"

Write-Host "Sending files to the board, will take about 2 min..."
cd Deploy
ampy --baud 460800 --port COM6 put . /
ampy --port COM6 ls
cd ..

rmdir -recurse "Deploy"

Write-Output "Rebooting..."
Restart-Microcontroller $port

Show-SerialLog $port