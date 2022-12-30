Import-Module .\serial-toys.psm1

$port = Find-MicrocontrollerPort

$portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
$portObj.DtrEnable = $true;
$portObj.RtsEnable = $true;

$portObj.open()
$portObj.WriteLine("$([char] 3)")

while (![Console]::KeyAvailable) {
    try {
        $portObj.WriteLine("$([char] 1)")
        $line = $portObj.ReadExisting()
        if ($line)
        {
            Write-Host -NoNewLine $line
        }
    }
    catch {
        $portObj.Close()
        $portObj.Open()
    }
}
$portObj.Close()