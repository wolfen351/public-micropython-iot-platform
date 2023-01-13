#!/bin/bash

Write-Output "Set board into Device Firmware Upgrade (DFU) mode."
Write-Output "    Hold on Button PROG"
Write-Output "    Press Button RESET"
Write-Output "    Release Button PROG When you hear the prompt tone on usb reconnection"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool.py --chip esp32 --port COM11 erase_flash
esptool.py --chip esp32 --port COM11 write_flash -z 0x1000 ./firmware/esp32-20220117-v1.18.bin