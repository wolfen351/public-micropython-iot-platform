#!/bin/bash

Import-Module .\serial-toys.psm1

$port = Find-MicrocontrollerPort

Write-Output "About to erase"

Write-Host "Press any key to continue..."
$junk = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

esptool.py --chip esp32c3 --port $port erase_flash
esptool.py --chip esp32c3 --port $port --baud 460800 write_flash -z 0x0 ./firmware/esp32c3-20220618-v1.19.1.bin