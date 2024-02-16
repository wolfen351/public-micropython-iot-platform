#!/bin/bash

Write-Output "Set board into programming mode."
Write-Output "    Hold the Button"
Write-Output "    Connect the power"
Write-Output "    Release Button when you hear the prompt tone on usb reconnection"

Write-Host "Press any key to continue..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Import-Module ./serial-toys.psm1
$port = Find-MicrocontrollerPort
Write-Output "Found port: $port"


esptool --chip esp8266 --port $port erase_flash
esptool --chip esp8266 --port $port --baud 115200 write_flash -fm dout -z 0x0 ./firmware/ESP8266_GENERIC-FLASH_1M-20240105-v1.22.1.bin

