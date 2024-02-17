#!/bin/bash

Write-Output "Set board into Device Firmware Upgrade (DFU) mode."
Write-Output "    Hold on Button PROG"
Write-Output "    Press Button RESET"
Write-Output "    Release Button PROG When you hear the prompt tone on usb reconnection"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool --chip esp32 --port $port erase_flash
esptool --chip esp32 --port $port write_flash -z 0x1000 ./firmware/esp32spiram-20220117-v1.18.bin
