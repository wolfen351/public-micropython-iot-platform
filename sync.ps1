# Globals
Write-Output "Detecting port..."
$SerialPorts = Get-CimInstance -Class Win32_SerialPort | Select-Object Name, Description, DeviceID
$port = $SerialPorts | Where-Object -Property Description -eq 'USB Serial Device' | Select -ExpandProperty DeviceID
Write-Output "Connecting on port $port"
try {
    $portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
    $portObj.DtrEnable = $true;
    $portObj.RtsEnable = $true;
    $portObj.open()
    $portObj.Close()
}
catch 
{
    Write-Error "Failed to connect. $PSItem.Exception.Message" -ErrorAction Stop
}

Remove-Item ./lastedit.dat
ampy --port $port get lastedit.dat > lastedit.dat 2> $null

if ((Get-Item "lastedit.dat").length -eq 0) {
    Write-Output "The board does not have a lastedit.dat file, so all files will be copied."
    Write-Host "Press any key to continue..."
    $junk = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
}

if ($args[0] -eq "--force") {
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    Write-Output "Force option specified. All files will be copied!"
}

$MAX = Get-Content -Path .\lastedit.dat
$MAXEDITTIME = $MAX
Write-Output "Last sync for this board was at $MAX"

# load active modules
$activeModules = @(Get-Content "active_modules.config")

# send all files to the device
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, *.crt, *.key, *.c, *.raw
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
    # increment the version
    ./bump_version.ps1
    ampy --baud 1152000 --port $port put version

    # record the last time a file was edited
    $MAXEDITTIME = [math]::Round($MAXEDITTIME)
    Write-Output $MAXEDITTIME | Out-File -Encoding ascii .\lastedit.dat
    ampy --port $port put lastedit.dat
} else {
    Write-Output "No changes since last sync."
}

Write-Output "Rebooting..."
$portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
$portObj.open()
$portObj.WriteLine("$([char] 2)")
$portObj.WriteLine("$([char] 3)")
$portObj.WriteLine("$([char] 4)")
$portObj.WriteLine("import machine\r\n")
$portObj.WriteLine("machine.reset()\r\n")
$portObj.Close()

Write-Output "Waiting for port: $port. Serial Log follows - Press any key to disconnect!" 
$portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
$portObj.ReadTimeout = 1000
$portObj.DtrEnable = $true;
$portObj.RtsEnable = $true;
$portObj.Open()
while (! [console]::KeyAvailable) {
    try {
        $data = $portObj.ReadLine()
        if ($data -ne "") {
          Write-Output $data
        }
    }
    catch {

        if ($PSItem.Exception.Message.Contains("timeout")){
            continue;
        }

        Write-Output "Error. $_"

        if (! $portObj.IsOpen) {
            $portObj.Open()
        }
    }
    #python -m serial.tools.miniterm $port 115200 2> $null
}

Write-Host "Disconnecting from port $port"
$portObj.Close()
