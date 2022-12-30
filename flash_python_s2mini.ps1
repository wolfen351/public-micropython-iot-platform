#!/bin/bash

Write-Output "Make S2 boards into Device Firmware Upgrade (DFU) mode."
Write-Output "    Hold on Button 0"
Write-Output "    Press Button Reset"
Write-Output "    Release Button 0 When you hear the prompt tone on usb reconnection"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool.py --chip esp32-s2 --port COM5 erase_flash
esptool.py --chip esp32-s2 --port COM5 --baud 1000000 write_flash -z 0x1000 ./firmware/LOLIN_S2_MINI-20220618-v1.19.1.bin
