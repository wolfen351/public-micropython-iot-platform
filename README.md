<h1 align="center">Welcome to Project Fred - Micropython IOT Platform 👋</h1>
<p>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue.svg?cacheSeconds=2592000" />
  <a href="https://github.com/wolfen351/public-micropython-iot-platform/wiki" target="_blank">
    <img alt="Documentation" src="https://img.shields.io/badge/documentation-yes-brightgreen.svg" />
  </a>
  <a href="https://opensource.org/license/mit" target="_blank">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  </a>
</p>

> Micropython code to control relays, temp sensors, buttons, touchscreen, gps etc. Has web ui, mqtt, home assistant and thingsboard support

### 🏠 [Homepage](https://github.com/wolfen351/public-micropython-iot-platform)

### ✨ [Demo](https://github.com/wolfen351/public-micropython-iot-platform/wiki/Web-UI)

## Supported Hardware

* ESP32R4V3 - This is a ESP32 based board that has AC Power Support, 4 relays, 4 buttons, DIN Rail support etc: https://www.aliexpress.com/item/1005003153036762.html
* LilyGo-T-OI-PLUS - This is a ESP32 based board that has a built in battery and charging circuit: https://github.com/Xinyuan-LilyGO/LilyGo-T-OI-PLUS
* LilyGo-T-Internet-POE - This is a ESP32 based board with ethernet support:  https://www.lilygo.cc/products/t-internet-poe
* Wemos S2 Mini - This is a small ESP32 that has USB-C support: https://www.wemos.cc/en/latest/s2/s2_mini.html 
* Sonoff Basic R4 - This is a mains power rated relay board: https://itead.cc/product/sonoff-basicr4-wi-fi-smart-switch/ 

Many other boards will probably work too!

## Supported Modules
* ac_remote - This presents a simple UI on a touchscreen (ILI9341 XPT2046) to be the remote control unit for a air conditioner.
* binary_clock - This presents a nice little binary clock UI on a touchscreen ().
* builtin_button - This exposes the built in button on many of these development boards to mqtt etc
* dht11 - This reads the temperature and humidity from a DHT11 sensor
* dht22 - This reads the temperature and humidity from a DHT22 sensor
* ds18b20 - This reads the temperature from a DS18B20 sensor
* four_button - This exposes 4 buttons on a board to mqtt etc (Currently used by the esp32r4v3 board)
* four_relay - This exposes 4 relays on a board to mqtt etc (Currently used by the esp32r4v3 board)
* gps - This reads the GPS data from a GPS module
* home_assistant - This sends data and receives commands to/from a home assistant instance via mqtt (Auto discovery etc is supported)
* ledstrip - This controls a WS2812B LED strip
* ledstrip_remote - This presents a simple UI on a touchscreen () to be the remote control unit for a WS2812B LED strip.
* lilygo_battery - This exposes the battery voltage and charging status of a LilyGo T-OI-PLUS board
* mosfet - This exposes the 4 mosfets on this great little board to mqtt etc
* mqtt - This sends data and receives commands to/from a mqtt broker
* ntp - This adds ntp support (currently fairly primitive)
* ota - This adds in OTA update support. You will need a web server to host the update packages
* pir - This reads the data from a PIR sensor
* relay - This controls a relay
* temphistory - This stores a history of temperature readings, saved locally on the board and sends it to mqtt and the web
* thingsboard - This sends data and receives commands to/from a thingsboard instance via mqtt
* touchscreen - This adds a touchscreen support to the board
* us_range - This allows the board to read data from a US-100 ultrasonic range sensor
* wdt - This exposes the WDT function on the board, so you can reset the board if it locks up
* web - This enables the board to have a web ui including configuration of wifi and all modules can contribute and use the web ui
* wifi - This enables the board to connect to wifi



## Install

### Install Micropython

To install this on your microcontroller, first flash micropython on it. You need at least version 1.22. You can find firmware and flashing instructions here: https://micropython.org/download/esp32/

I've written some powershell scripts to make the flashing process easier for each of the supported boards. Please see hardware/firmware folder for the scripts.

### Select / Create a Profile

You can select a ready made profile, or create a new one for your board. The profile selects which modules to install and run (like gps, or touchscreen etc). IT contains any additional configuration (like which pin the wires will be soldered to) that cannot be changed at runtime.

The profiles are stored in /profiles

If you can't find the profile you need simply create a new one for your board. You can do this by copying any of the json files to a new file called <manufacturer>-<boardname>.json. Then edit the file to match your board. 

### Send all the required micropython files to the board

You can use the sync.ps1 script to send all the required files to the board. You will need to pass the profile name
```sh
sync.ps1 s2mini-dht22
```

## Monitoring the Board Via Serial

```sh
Install-Module serial-toys.psm1
Show-SerialLog
```

## Author

👤 **Iain Prior**

* Github: [@wolfen351](https://github.com/wolfen351)

## 🤝 Contributing

Contributions, issues and feature requests are welcome!<br />Feel free to check [issues page](https://github.com/wolfen351/public-micropython-iot-platform/issues). You can also take a look at the [contributing guide](https://github.com/jessesquires/.github/blob/main/CONTRIBUTING.md).

## Show your support

Give a ⭐️ if this project helped you!

## 📝 License

Copyright © 2024 [Iain Prior](https://github.com/wolfen351).<br />
This project is [MIT](https://opensource.org/license/mit) licensed.

***
_This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator)_
