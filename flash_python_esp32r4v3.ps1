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
# 1.20 last version that works, after this the wifi is causing issues - setting the dhcp hostname causes crashes
# 1.22 now works, provided that the setting is set to suppress setting the dhcp hostname in the profile
esptool --chip esp32 --port $port write_flash -z 0x1000 ./firmware/ESP32_GENERIC-SPIRAM-20240105-v1.22.1.bin
