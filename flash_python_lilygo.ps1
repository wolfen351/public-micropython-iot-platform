#!/bin/bash

Write-Output "About to erase"


read -p "Press any key to continue... " -n1 -s

esptool.py --chip esp32c3 --port COM5 erase_flash
esptool.py --chip esp32c3 --port COM5 --baud 460800 write_flash -z 0x0 esp32c3-20220117-v1.18.bin