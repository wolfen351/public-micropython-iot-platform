#!/bin/bash

Write-Output "This will flash the ESPCAM with the latest firmware."

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


esptool --port $port erase_flash
esptool --chip auto --port $port write_flash -z 0x0 ./firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20240602-v1.23.0.bin

Show-SerialLog
