$port= new-Object System.IO.Ports.SerialPort COM3,115200,None,8,one
$port.open()
$port.WriteLine("$([char] 3)")

while (![Console]::KeyAvailable) {
    try {
        $port.WriteLine("$([char] 1)")
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