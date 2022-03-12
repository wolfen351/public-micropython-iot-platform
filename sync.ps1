Remove-Item ./lastedit.dat

ampy --port COM3 get lastedit.dat > lastedit.dat

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

# increment the version
./bump_version.ps1

# send all files to the device
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, version, *.crt, *.key
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
        $bits = $f.ToString().Split('\\')
        $dir = ""
        for ($j = 0; $j -lt $bits.Count - 1; $j++) {
            if ($j -gt 0) {
                $dir = $dir + "\\" + $bits[$j]
            }
            else {
                $dir = $bits[$j]
            }

            ampy --port COM3 mkdir $dir > $null  2>&1
        }

        # SEND THE FILE
        ampy --port COM3 put "$($f.ToString().Replace("\\", "\\\\"))" "$($f.ToString().Replace("\\", "\\\\"))"
        if (!($?)) {
            Write-Output "Failed."
            exit 3
        }
    }
}

# record the last time a file was edited
$MAXEDITTIME = [math]::Round($MAXEDITTIME)
Write-Output $MAXEDITTIME | Out-File -Encoding ascii .\lastedit.dat
ampy --port COM3 put lastedit.dat

Write-Output "Rebooting..."
$port= new-Object System.IO.Ports.SerialPort COM3,115200,None,8,one
$port.open()
$port.WriteLine("$([char] 2)")
$port.WriteLine("$([char] 3)")
$port.WriteLine("$([char] 4)")
$port.WriteLine("import machine\r\n")
$port.WriteLine("machine.reset()\r\n")
$port.Close()
Start-Sleep 1
Write-Output "Any key to exit"
$port= new-Object System.IO.Ports.SerialPort COM3,115200,None,8,one
$port.open()
while (![Console]::KeyAvailable) {
    try {
        $line = $port.ReadExisting()
        if ($line)
        {
            Write-Host -NoNewLine $line
        }
    }
    catch {
        $port.Close()
        $port.Open()
    }
}
$port.Close()
