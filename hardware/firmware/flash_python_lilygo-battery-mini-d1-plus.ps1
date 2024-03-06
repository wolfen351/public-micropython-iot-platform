#!/bin/bash

Import-Module .\serial-toys.psm1

$port = Find-MicrocontrollerPort

Write-Output "About to erase"

Write-Host "Press any key to continue..."
$junk = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool --chip esp32c3 --port $port erase_flash
esptool --chip esp32c3 --port $port --baud 460800 write_flash -z 0x0 ./firmware/ESP32_GENERIC_C3-20240105-v1.22.1.bin