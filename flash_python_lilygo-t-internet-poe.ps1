#!/bin/bash

Import-Module .\serial-toys.psm1

Write-Output "Set board into Device Firmware Upgrade (DFU) mode."
Write-Output "    Hold on Button BUT"
Write-Output "    Press Button RST"
Write-Output "    Release Button BUT When you hear the prompt tone on usb reconnection"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

$port = Find-MicrocontrollerPort

Write-Output "About to erase"

Write-Host "Press any key to continue..."
$junk = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool --chip esp32 --port $port erase_flash
esptool --chip esp32 --port $port --baud 460800 write_flash -z 0x1000 ./firmware/esp32-20220117-v1.18.bin
