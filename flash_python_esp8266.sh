#!/bin/bash

esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 --baud 1000000 write_flash --flash_size=4MB -fm dio 0 ./firmware/esp8266-20210807-unstable-v1.16-166-g78718fffb.bin