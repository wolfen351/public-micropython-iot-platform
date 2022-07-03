Write-Output "Any key to exit"
$port= new-Object System.IO.Ports.SerialPort COM5,115200,None,8,one
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