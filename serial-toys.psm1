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
    $SerialPorts = Get-WmiObject Win32_PnPEntity | Where-Object Name -match 'COM\d+' | Select-Object Name, Description, DeviceID
    $Name = $SerialPorts | Where-Object { ($_.Description -eq 'USB Serial Device') -or ($_.Description -eq 'USB-SERIAL CH340K') -or ($_.Description -eq 'Prolific USB-to-Serial Comm Port') -or ($_.Description -eq 'USB-Enhanced-SERIAL CH9102') -or ($_.Description -eq 'USB-SERIAL CH340') } | Select-Object -ExpandProperty Name
    $Name -match "COM\d+" > $null

    $port = $Matches.0

    if ($null -eq $port) {
        throw "Unable to find serial port"
    }

    if ('COM1' -eq $port) {
        throw "Only found COM1, which is not a valid port"
    }

    Write-Host "Detected $port"
    return $port
}


function Show-SerialLog {

    param(
        $port
    )

    while ($null -eq $port)
    {
        try {
            $port = Find-MicrocontrollerPort
        }
        catch {
            $err = "Error. $_"
            Write-Progress -Activity "Detecting COM Port" -Status $err
        }
    }

    Write-Host "-------------------------------------------------------------------------------"
    Write-Host "Listening on $port. Serial Log follows - Press any key to disconnect!" 
    Write-Host "-------------------------------------------------------------------------------"
    $portObj = new-Object System.IO.Ports.SerialPort $port,115200,None,8,one
    $portObj.ReadTimeout = 1000
    $portObj.DtrEnable = $true;
    $portObj.RtsEnable = $true;
    $portObj.Open()

    while (! [console]::KeyAvailable) {
        try {
            if (! $portObj.IsOpen) {
                $portObj.Open()
            }            

            $data = $portObj.ReadLine()
            if ($data -ne "") {
            Write-Output $data
            Write-Progress -Completed -Activity "Connecting"
            }
        }
        catch [TimeoutException] {
            continue;
        }
        catch {
            $err = "Error. $_"
            Write-Progress -Activity "Connecting" -Status $err
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

    esptool --port $port chip_id
}

function Step-Version {
    # increment the version 
    $raw = Get-Content -Path .\version -Raw
    $v = [version]$raw
    $nv = [version]::New($v.Major,$v.Minor,$v.Build+1,0)
    $newVersion = "$($nv)";
    $newVersion = $newVersion.Substring(0, $newVersion.Length - 2)
    Write-Host "Version is now: $newVersion"
    Write-Output $newVersion | Out-File -encoding ascii .\version
}

function Xargs {
    param(
        $Cmd
    )
    process {
        $args += ,$_
    }
    end {
        & $Cmd @args
    }
}