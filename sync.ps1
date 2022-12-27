# Globals
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
    Write-Error "Failed to connect." -ErrorAction Stop
}

Remove-Item ./lastedit.dat
ampy --port $port get lastedit.dat > lastedit.dat 2> $null

if ((Get-Item "lastedit.dat").length -eq 0) {
    Write-Output "lastedit.dat does not exist, making a new one"

    Write-Host "Press any key to continue..."
    $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

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
$files = Get-ChildItem . -name -recurse -include *.py, *.html, *.sh, *.js, *.cfg, *.crt, *.key, *.c, *.raw
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

Write-Output "Waiting for port: $port" 
$portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
$portObj.ReadTimeout = 1000
$portObj.DtrEnable = $true;
$portObj.RtsEnable = $true;
$portObj.Open()
while (1) {
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

