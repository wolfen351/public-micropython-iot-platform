#!/bin/bash

Write-Output "Make ESPCAM boards into Device Firmware Upgrade (DFU) mode."
Write-Output "    Connect UART to USB"
Write-Output "    See this URL for conenction diagram: "
Write-Output "    https://lastminuteengineers.com/getting-started-with-esp32-cam/"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool.py --chip esp32 --port COM8 erase_flash
esptool.py --chip esp32 --port COM8 --baud 1000000 write_flash -z 0x1000 ./firmware/micropython_camera_feeeb5ea3_esp32_idf4_4.bin
