param($profileName) 

# If /? is specified then print help
if ($args -contains "/?") {
    Write-Output "Usage: sync.ps1 [profileName] [-wipe] [-prod] [-force] [-nopref] [-precompile]"
    Write-Output "profileName: The name of the profile to sync"
    Write-Output "-wipe: Wipe all files on the board before syncing"
    Write-Output "-prod: Sync only the minimum files for flashing, with version 1.0.0"
    Write-Output "-force: Sync all files, regardless of last edit time"
    Write-Output "-nopref: Skip sending prefs.json"
    Write-Output "-precompile: Precompile .py files to .mpy files"
    exit 0
}

# Globals
Import-Module .\serial-toys.psm1


# Set env var for baud
$env:AMPY_BAUD = 115200

# Load the profile
try {

    if ($null -eq $profileName) {
        throw "Profile Name Required!"
    }
    
    $activeProfile = Get-Content -Raw ".\profiles\$profileName.json" | ConvertFrom-Json 
    # load active modules
    $activeModules = $activeProfile.activeModules
    Write-Host "Flashing Profile: $profileName"
    Write-Host "Active Modules: $activeModules"

    $dest = "$PSScriptRoot\profile.json"
    Invoke-Expression "xcopy .\profiles\$profileName.json $dest /Y /-I"
}
catch {
    Write-Error "Could not load profile from file .\profiles\$profileName.json"
    Write-Error "Please specify the profile name as a parameter to this script" -ErrorAction Stop
}

# Connect to the board
$port = Find-MicrocontrollerPort
if ($port -eq "COM1")
{
    Write-Error "Board not detected. Aborting." -ErrorAction Stop
}

Start-Sleep 4

$MAX = 0
$MAXEDITTIME = 0

# check basic connectivity to the board
ampy --port $port ls > $null 2>&1
if ($? -eq $false) {
    Write-Error "Could not connect to the board. Aborting." -ErrorAction Stop
}

# if the user specified -wipe or -prod, delete all files on the board
if ($args -contains "-wipe" -or $args -contains "-prod") {
    Write-Host "Wipe option specified. Deleting all files on the board.."

    # wipe all files on the board, recursively
    $files = ampy --port $port ls -r
    $i = 0
    foreach ($f in $files) {
        $fn = $f -replace "\s", ""
        $i++
        # Use Write Progress to show progress
        $percentComplete = [math]::Round(($i / $files.Count) * 100)
        Write-Progress "Deleting:" -Status "($percentComplete%) Deleting file $fn.." -PercentComplete (($i / $files.Count) * 100)  -Id 1

        # skip prefs.json if -nopref is specified
        if ($args -contains "-nopref" -and $fn -eq "prefs.json") {
            Write-Output "Skipping deleting prefs.json (-nopref specified)"
            continue;
        }
        ampy --port $port rm $fn > $null
    }
    Write-Output "All files deleted."
}

# if the user added -prod to the command line, send a new file to the board containing 1.0.0 with the file name version
if ($args -contains "-prod") {
    Write-Host "Prod option specified. Will upload minimum files for flashing, with version 1.0.0."
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    $activeModules = @("basic", "ota", "wifi", "web")
} elseif ($args -contains "-force") {
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    Write-Output "Force option specified. All files will be copied!"
} elseif ($args -contains "-wipe") {
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    Write-Output "Wipe option specified. All files will be copied!"
} else {
    Write-Host "Checking when board was last updated.."
    Remove-Item ./lastedit.dat
    ampy --port $port get lastedit.dat > lastedit.dat 2> $null

    $MAX = Get-Content -Path .\lastedit.dat
    $MAXEDITTIME = $MAX

    if ((Get-Item "lastedit.dat").length -eq 0) {
        Write-Output "The board does not have a lastedit.dat file, so all files will be copied."
        Write-Host "Press any key to continue..."
        $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null

        Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    }
    else {
        Write-Output "Last edit time on board: $MAX"
    }
}

# send all files to the device
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, *.crt, *.key, *.c, *.raw, profile.json, *.json
$sent = 0

# Remove all .venv files from $files
$files = $files | Where-Object {$_ -notlike ".venv*"}
$files = $files | Where-Object {$_ -notlike ".vscode*"}

# Create an array to store the files to send
$filesToSend = @()

for ($i = 0; $i -lt $files.Count; $i++) {
    $f = $files[$i]

    $percentComplete = [math]::Round(($i / $files.Count) * 100)
    Write-Progress "Processing files:" -Status "($percentComplete%) Checking $f..." -PercentComplete $percentComplete -Id 1

    $LE = (Get-ChildItem $f).LastWriteTimeUtc | Get-Date -UFormat %s

    if ($LE -gt $MAX) {

        # Skip unchanged files
        if ($MAXEDITTIME -lt $LE)
        {
            $MAXEDITTIME = $LE
        }

        # Skip files from inactive modules
        $activeModule = $False
        $rootFile = $False
        if ($activeModules.Contains("$((Get-Item $f).Directory.Name)")) {
            $activeModule = $True
        }
        if (!$f.Contains("\")) {
            $rootFile = $True
        }
        if ($f.Contains("board_system")) {
            $rootFile = $True
        }
        if ($f.Contains("ulib")) {
            $rootFile = $True
        }        

        # Skip .package
        if ($f.Contains(".package")) {
            continue;
        }

        if (!$rootFile -and !$activeModule)
        {
            continue;
        }

        # Skip prefs.json if "-no-prefs" is specified
        if ($args -contains "-nopref" -and $f -eq "prefs.json") {
            Write-Output "Skipping sending prefs.json (-nopref specified)"
            continue;
        }

        # Add the file to the array to send
        $filesToSend += $f
    }
}

# Let user know how many files will be transferred
Write-Output "Files to send: $($filesToSend.Count)"

# Send all the identified files
for ($i = 0; $i -lt $filesToSend.Count; $i++) {
    $f = $filesToSend[$i]

    $percentComplete = [math]::Round(($i / $filesToSend.Count) * 100)

    # Ok send the file, all conditions satisfied
    Write-Progress "Uploading files:" -Status "($percentComplete%) Processing file $f..." -PercentComplete $percentComplete -Id 1

    # MAKE SURE PATH EXISTS ON DEVICE
    $bits = $f.ToString() -split '\\'
    $dir = ""
    for ($j = 0; $j -lt $bits.Count - 1; $j++) {
        if ($j -gt 0) {
            $dir = $dir + "/" + $bits[$j]
        }
        else {
            $dir = $bits[$j]
        }

        ampy --port $port mkdir $dir > $null  2>&1
    }

    # SEND THE FILE
    $fn = "$($f)"
    $fnn = $fn -replace "\\", "/"

    # Only precompile if -precompile is specified
    if ($args -contains "-precompile") {
        # if the file is a .py file cross compile it, skip main.py, boot.py
        if ($fn -like "*.py" -and $fn -ne "main.py" -and $fn -ne "boot.py") {
            Write-Progress "Uploading files:" -Status "($percentComplete%) Cross Compiling file $fn..." -PercentComplete $percentComplete -Id 1
            python -m mpy_cross -march=xtensawin $fn
            $fnn = $fnn -replace ".py", ".mpy"
        }
    }

    # send the file using ampy
    Write-Progress "Uploading files:" -Status "($percentComplete%) Sending file $fnn..." -PercentComplete $percentComplete -Id 1
    ampy --port $port put $fnn $fnn

    if (!($?)) {
        Write-Output "Failed to send file to the board, attempting to delete and send again.."
        $boardFile = "$(ampy --port $port get $fnn)" 
        Write-Output "File on microcontoller is $($boardFile.length) bytes"
        Write-Output "File on disk is $((Get-Item $fnn).length) bytes"

        Write-Output "Deleting file on microcontroller:"
        ampy --port $port rm $fnn
        Write-Output "Trying another copy:"
        ampy --port $port put $fnn $fnn
        if (!($?)) {
            Write-Output "Failed again. Giving up."
            exit 3
        }
        Write-Output "Success, moving to next file"
    }
    else {
        $percentComplete = [math]::Round((($i+1) / $filesToSend.Count) * 100)
        Write-Progress "Uploading files:" -Status "($percentComplete%) Sent $fnn!" -PercentComplete $percentComplete -Id 1
    }
    $sent++
}

if ($sent -gt 0) {
    # Write "8.1.0" to the version file
    Write-Output "8.1.0" | Out-File -Encoding ascii .\version

    Write-Host "Uploading new version file to board.."
    ampy --port $port put version

    # record the last time a file was edited
    $MAXEDITTIME = [math]::Round($MAXEDITTIME)
    Write-Output $MAXEDITTIME | Out-File -Encoding ascii .\lastedit.dat
    Write-Host "Uploading lastedit.dat file to board.."
    ampy --port $port put lastedit.dat
} else {
    Write-Output "No changes since last sync."
}

# if the user added -prod to the command line, send a new file to the board containing 1.0.0 with the file name version
if ($args -contains "-prod") {
    Write-Output "1.0.0" | Out-File -Encoding ascii .\version
    Write-Host "Uploading 1.0.0 version file to board, so it will auto update.."
    ampy --port $port put version
    Write-Output "8.1.0" | Out-File -Encoding ascii .\version
}

# Clean up
Remove-Item profile.json

Write-Output "Rebooting..."
Restart-Microcontroller $port

# Remove the progress bar
Write-Progress -Id 1 -Completed "Clearing Progress Bar"

Show-SerialLog $port