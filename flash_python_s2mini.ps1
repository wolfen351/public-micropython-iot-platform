#!/bin/bash

Write-Output "Make S2 boards into Device Firmware Upgrade (DFU) mode."
Write-Output "    Hold on Button 0"
Write-Output "    Press Button Reset"
Write-Output "    Release Button 0 When you hear the prompt tone on usb reconnection"

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


esptool --chip esp32-s2 --port $port erase_flash
esptool --chip esp32-s2 --port $port --baud 1000000 write_flash -z 0x1000 ./firmware/firmware-LOLIN_S2_MINI-v1.20.0-124-g17c3f6b6a.bin
