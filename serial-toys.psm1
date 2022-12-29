function Test-Port {

    param(
        $port
    )

    try {
        $portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
        $portObj.DtrEnable = $true;
        $portObj.RtsEnable = $true;
        $portObj.open()
        $portObj.Close()
    }
    catch 
    {
        Write-Error "Failed to connect. ${$_.Exception.Message}"
        Write-Error "Unable to connect to $port Serial Port " -ErrorAction Stop
        Exit 5
    }
}

function Find-MicrocontrollerPort {
    Write-Host "Detecting port..."
    $SerialPorts = Get-WmiObject Win32_PnPEntity | Where-Object Name -match 'COM\d+' | Select-Object Name, Description, DeviceID
    $Name = $SerialPorts | Where-Object { ($_.Description -eq 'USB Serial Device') -or ($_.Description -eq 'USB-SERIAL CH340K') } | Select-Object -ExpandProperty Name
    $Name -match "COM\d+" > $null
    $port = $Matches.0

    try {

        if ($null -eq $port) {
            throw "Unable to find serial port"
        }

        Write-Host "Testing connectivity to port $port ..."
        Test-Port $port

        return $port
    }
    catch 
    {
        Write-Host "Failed to connect. ${$_.Exception.Message}"
        Write-Host "Detected ports:"
        Write-Host Get-WmiObject Win32_PnPEntity | Where-Object Name -match 'COM\d+' | Select-Object Name, Description, DeviceID
        Write-Host "Aborted." -ErrorAction Stop
        Exit 5
    }
}


function Show-SerialLog {

    param(
        $port
    )

    Write-Host "Listening on $port. Serial Log follows - Press any key to disconnect!" 
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

            Write-Host "Error. $_"

            if (! $portObj.IsOpen) {
                $portObj.Open()
            }
        }
        #python -m serial.tools.miniterm $port 115200 2> $null
    }

    Write-Host "Disconnecting from port $port"
    $portObj.Close()
}

function Restart-Microcontroller {

    param(
        $port
    )

    Test-Port $port

    $portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
    $portObj.DtrEnable = $true;
    $portObj.RtsEnable = $true;
    $portObj.open()
    $portObj.WriteLine("$([char] 2)")
    $portObj.WriteLine("$([char] 3)")
    $portObj.WriteLine("$([char] 4)")
    $portObj.WriteLine("import machine\r\n")
    $portObj.WriteLine("machine.reset()\r\n")
    $portObj.Close()

}