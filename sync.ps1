param($profileName) 

# Globals
Import-Module .\serial-toys.psm1


# Set env var for baud
$env:AMPY_BAUD = 921600

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

# if the user added -prod to the command line, send a new file to the board containing 1.0.0 with the file name version
if ($args -contains "-prod") {
    Write-Host "Prod option specified. Will upload minimum files for flashing, with version 1.0.0."
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    $activeModules = @("basic", "ota", "wifi", "web")
} elseif ($args -contains "-force") {
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    Write-Output "Force option specified. All files will be copied!"
} else {
    Write-Host "Checking when board was last updated.."
    Remove-Item ./lastedit.dat
    ampy --port $port get lastedit.dat > lastedit.dat # 2> $null

    $MAX = Get-Content -Path .\lastedit.dat
    $MAXEDITTIME = $MAX
    Write-Output "Last sync for this board was at $MAX"

    if ((Get-Item "lastedit.dat").length -eq 0) {
        Write-Output "The board does not have a lastedit.dat file, so all files will be copied."
        Write-Host "Press any key to continue..."
        $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null

        Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    }
}

# send all files to the device
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, *.crt, *.key, *.c, *.raw, profile.json, *.json
$sent = 0
for ($i = 0; $i -lt $files.Count; $i++) {
    $f = $files[$i]
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

        # Ok send the file, all conditions satisfied
        Write-Output "Sending file $f..."

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
        $sent++
    }
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

Show-SerialLog $port