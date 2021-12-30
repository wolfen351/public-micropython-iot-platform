# Main 
from machine import sleep
import machine

try:
    import gc
    import time

    print('\nConnecting to wifi...')
    import network
    sta_if = network.WLAN(network.STA_IF)
    t_end = time.time() + 15
    sta_if.active(True)
    while not sta_if.isconnected() and time.time() < t_end:
        pass
    if (sta_if.isconnected()):
        print('network config:', sta_if.ifconfig())
        # Disable AP
        sta_ap = network.WLAN(network.AP_IF)
        sta_ap.active(False)
        del sta_ap
    else:
        print("No Wifi, starting portal to configure wifi")
        from captive_portal import CaptivePortal
        portal = CaptivePortal(project="4LIGHTS")
        portal.start()
        import machine
        machine.reset() # Reboot to save RAM
    del t_end
    del sta_if
    gc.collect()

    # Import other modules needed
    from mqtt_control import MQTTControl
    from web_portal import WebPortal
    from web_processor import WebProcessor
    from light_control import LightControl
    from mosfet_control import MosfetControl
    from d1mini_pins import PIN_LED
    from machine import Pin

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
            import sys
            sys.print_exception(e)

    while True:
        # tick all the modules

        runSafe(web.tick);
        runSafe(mqtt.tick);
        runSafe(lights.tick);
        runSafe(mosfet.tick);

        # blink blue 
        ledOn = not ledOn;
        if (ledOn):
            led.on()
        else:
            led.off()

        #clean up
        gc.collect()

except KeyboardInterrupt:
    raise
except Exception as e:
    import sys
    sys.print_exception(e)
    print("Fatal exception, will reboot in 30s")
    sleep(10000)
    machine.reset()
