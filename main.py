# Main 

try:
    # Turn on the LED to show we are alive
    import machine
    from machine import Pin
    led = Pin(15, Pin.OUT)
    led.on()

    # Import other modules needed
    from mqtt_control import MQTTControl
    from web_portal import WebPortal
    from web_processor import WebProcessor
    from machine import Pin
    from wifi import WifiHandler
    import sys, machine
    from serial_log import SerialLog
    import gc
    from temp_monitor import TempMonitor
    
    #SerialLog.disable() # disable for live, otherwise you pay 30s startup cost

    SerialLog.log()
    SerialLog.log("Speed to 240Mhz")
    machine.freq(240000000) # set the CPU frequency to 240 MHz

    SerialLog.log()
    SerialLog.log("Starting Wifi..")
    wifi = WifiHandler()
    wifi.start()

    SerialLog.log()
    SerialLog.log("Starting Temperature..")
    temp = TempMonitor()
    temp.start()

    SerialLog.log()
    SerialLog.log("Starting MQTT..")
    mqtt = MQTTControl()
    mqtt.start(temp)

    SerialLog.log()
    SerialLog.log("Starting WebProcessor..")
    webProcessor = WebProcessor()
    webProcessor.start(mqtt, temp)
    
    SerialLog.log()
    SerialLog.log("Starting Web..")
    web = WebPortal()
    web.start(webProcessor);

    SerialLog.log()
    SerialLog.log("Cleanup..")
    gc.collect()

    SerialLog.log()
    SerialLog.log("Ready!")

    ledOn = True

    def runSafe(cmd):
        try:
            cmd()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log(e)
            sys.print_exception(e)
            gc.collect()

    while True:
        # tick all the modules
        runSafe(wifi.tick)
        runSafe(web.tick)
        runSafe(mqtt.tick)
        runSafe(temp.tick)

        # blink blue 
        ledOn = not ledOn
        if (ledOn):
            led.on()
        else:
            led.off()

except KeyboardInterrupt:
    raise
except Exception as e:
    import sys
    from serial_log import SerialLog
    sys.print_exception(e)
    SerialLog.log("Fatal exception, will reboot in 10s")
    machine.sleep(10000)
    machine.reset()
