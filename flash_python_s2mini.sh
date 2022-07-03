#!/bin/bash

echo "Make S2 boards into Device Firmware Upgrade (DFU) mode."
echo     Hold on Button 0
echo     Press Button Reset
echo     Release Button 0 When you hear the prompt tone on usb reconnection

read -p "Press any key to continue... " -n1 -s

esptool.py --chip esp32-s2 --port /dev/ttyACM0 erase_flash
esptool.py --chip esp32-s2 --port /dev/ttyACM0 --baud 1000000 write_flash -z 0x1000 LOLIN_S2_MINI-20220618-v1.19.1.bin
