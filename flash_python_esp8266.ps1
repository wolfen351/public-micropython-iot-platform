#!/bin/bash

Write-Output "This will flash the ESP8266 with the latest firmware."

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


esptool.py --port $port erase_flash
esptool.py --port $port --baud 1000000 write_flash --flash_size=4MB -fm dio 0 .\firmware\esp8266-20230426-v1.20.0.bin

Show-SerialLog