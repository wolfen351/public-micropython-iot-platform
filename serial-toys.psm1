function Find-MicrocontrollerPort {
    Write-Host "Detecting port..."
    $SerialPorts = Get-WmiObject Win32_PnPEntity | Where Name -match 'COM\d+' | Select-Object Name, Description, DeviceID
    $Name = $SerialPorts | Where-Object { ($_.Description -eq 'USB Serial Device') -or ($_.Description -eq 'USB-SERIAL CH340K') } | Select -ExpandProperty Name
    $Name -match "COM\d+" > $null
    $port = $Matches.0

    try {

        if ($port -eq $null) {
            throw "Unable to find serial port"
        }

        Write-Host "Testing connectivity to port $port ..."
        $portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
        $portObj.DtrEnable = $true;
        $portObj.RtsEnable = $true;
        $portObj.open()
        $portObj.Close()

        return $port
    }
    catch 
    {
        Write-Host "Failed to connect. ${$_.Exception.Message}"
        Write-Host "Detected ports:"
        Write-Host Get-WmiObject Win32_PnPEntity | Where Name -match 'COM\d+' | Select-Object Name, Description, DeviceID
        Write-Host "Aborted." -ErrorAction Stop
        Exit 5
    }
}
