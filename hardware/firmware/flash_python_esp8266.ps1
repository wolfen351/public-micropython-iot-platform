#!/bin/bash

Write-Output "This will flash the ESP8266 with the latest firmware."
Write-Output "WARNING - This project probably won't work on ESP8266 without at least 512Kb RAM"

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


esptool --port $port erase_flash
esptool --port $port --baud 1000000 write_flash --flash_size=1MB -fm dio 0 .\firmware\esp8266-20230426-v1.20.0.bin

Show-SerialLog