# Globals
$port = "COM3"

Remove-Item ./lastedit.dat
ampy --port $port get lastedit.dat > lastedit.dat

if ((Get-Item "lastedit.dat").length -eq 0) {
    Write-Output "lastedit.dat does not exist, making a new one"
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
}

if ($args[0] -eq "--force") {
    Write-Output 0 | Out-File -Encoding ascii .\lastedit.dat
    Write-Output "All files will be copied!"
}

$MAX = Get-Content -Path .\lastedit.dat
$MAXEDITTIME = $MAX
Write-Output "Last sync for this board was at $MAX"

# send all files to the device
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, *.crt, *.key, *.c
$sent = 0
for ($i = 0; $i -lt $files.Count; $i++) {
    $f = $files[$i]
    $LE = (Get-ChildItem $f).LastWriteTimeUtc | Get-Date -UFormat %s

    if ($LE -gt $MAX) {
        if ($MAXEDITTIME -lt $LE)
        {
            $MAXEDITTIME = $LE
        }
        Write-Output "Sending $f"

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
        $sent++
        if (!($?)) {
            Write-Output "Failed."
            exit 3
        }
    }
}

if ($sent -gt 0) {
    # increment the version
    ./bump_version.ps1
    ampy --port $port put version

    # record the last time a file was edited
    $MAXEDITTIME = [math]::Round($MAXEDITTIME)
    Write-Output $MAXEDITTIME | Out-File -Encoding ascii .\lastedit.dat
    ampy --port $port put lastedit.dat
} else {
    Write-Output "No changes since last sync."
}

Write-Output "Rebooting..."
$port= new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
$port.open()
$port.WriteLine("$([char] 2)")
$port.WriteLine("$([char] 3)")
$port.WriteLine("$([char] 4)")
$port.WriteLine("import machine\r\n")
$port.WriteLine("machine.reset()\r\n")
$port.Close()
Start-Sleep 1
Write-Output "Any key to exit"

.\terminal.ps1