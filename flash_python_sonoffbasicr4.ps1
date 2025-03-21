#!/bin/bash

Write-Output "Set board into programming mode."
Write-Output "    Hold the Button"
Write-Output "    Connect the power"
Write-Output "    Release Button when you hear the prompt tone on usb reconnection"

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


esptool --chip esp32c3 --port $port erase_flash
esptool --chip esp32c3 --port $port --baud 115200 write_flash -z 0x0 ./firmware/ESP32_GENERIC_C3-20240105-v1.22.1.bin
