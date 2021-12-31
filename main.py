# Main 
try:
    import gc

    # Import other modules needed
    from mqtt_control import MQTTControl
    from web_portal import WebPortal
    from light_control import LightControl
    from web_processor import WebProcessor
    from mosfet_control import MosfetControl
    from d1mini_pins import PIN_LED
    from machine import Pin
    from wifi import WifiHandler

    print()
    print("Starting Wifi..")
    wifi = WifiHandler()
    wifi.start()

    print()
    print("Starting MosfetControl..")
    mosfet = MosfetControl()
    mosfet.start();

    print()
    print("Starting LightControl..")
    lights = LightControl(mosfet)
    lights.start();
    gc.collect()

    print()
    print("Starting MQTT..")
    mqtt = MQTTControl()
    mqtt.start(lights, mosfet)
    gc.collect()

    print()
    print("Starting WebProcessor..")
    webProcessor = WebProcessor()
    webProcessor.start(lights, mqtt)
    
    print()
    print("Starting Web..")
    web = WebPortal()
    web.start(webProcessor);
    gc.collect()

    print("Ready!")

    led = Pin(PIN_LED, Pin.OUT)
    ledOn = True

    def runSafe(cmd):
        try:
            cmd()
            gc.collect()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(e)

    while True:
        # tick all the modules

        runSafe(wifi.tick)
        runSafe(web.tick)
        runSafe(mqtt.tick)
        runSafe(lights.tick)
        runSafe(mosfet.tick)

        # blink blue 
        ledOn = not ledOn
        if (ledOn):
            led.on()
        else:
            led.off()

        #clean up
        gc.collect()

except KeyboardInterrupt:
    raise
except Exception as e:
    import sys, machine
    sys.print_exception(e)
    print("Fatal exception, will reboot in 30s")
    machine.sleep(10000)
    machine.reset()
