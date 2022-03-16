#!/bin/bash

Write-Output "Make S2 boards into Device Firmware Upgrade (DFU) mode."
Write-Output "    Hold on Button 0"
Write-Output "    Press Button Reset"
Write-Output "    Release Button 0 When you hear the prompt tone on usb reconnection"

read -p "Press any key to continue... " -n1 -s

esptool.py --chip esp32-s2 --port COM4 erase_flash
esptool.py --chip esp32-s2 --port COM4 --baud 1000000 write_flash -z 0x1000 s2_mini_micropython_v1.16-200-g1b87e1793.bin
